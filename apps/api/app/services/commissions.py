from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import CommissionClose, Guide, RiderCommission, RouteLeg, ServiceType, StationCommission


def resolve_week_window(week_start: str | None, previous_week: bool = False) -> tuple[datetime, datetime, date]:
    if week_start:
        monday = date.fromisoformat(week_start)
    else:
        today = datetime.now(timezone.utc).date()
        monday = today - timedelta(days=today.weekday())
        if previous_week:
            monday = monday - timedelta(days=7)

    monday_dt = datetime.combine(monday, datetime.min.time(), tzinfo=timezone.utc)
    next_monday_dt = monday_dt + timedelta(days=7)
    return monday_dt, next_monday_dt, monday


def compute_rider_rows(db: Session, start_dt: datetime, end_dt: datetime) -> list[tuple[str, int, float]]:
    rows = (
        db.query(RouteLeg, Guide)
        .join(Guide, Guide.id == RouteLeg.guide_id)
        .filter(
            RouteLeg.assigned_rider_id.is_not(None),
            RouteLeg.status == "completed",
            RouteLeg.updated_at >= start_dt,
            RouteLeg.updated_at < end_dt,
        )
        .all()
    )

    pickup_leg_types = {"pickup_to_station", "pickup_to_client", "pickup_to_origin_station"}
    delivery_leg_types = {"station_to_client", "destination_station_to_client"}
    totals: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    errand_guide_rider_roles: dict[tuple[str, str], set[str]] = defaultdict(set)

    for route_leg, guide in rows:
        if not route_leg.assigned_rider_id:
            continue

        rider_id = route_leg.assigned_rider_id
        totals[rider_id] += float(route_leg.rider_fee_amount or 0.0)
        counts[rider_id] += 1

        if guide.service_type == ServiceType.errand.value:
            key = (guide.id, rider_id)
            if route_leg.leg_type in pickup_leg_types:
                errand_guide_rider_roles[key].add("pickup")
            if route_leg.leg_type in delivery_leg_types:
                errand_guide_rider_roles[key].add("delivery")
            if route_leg.leg_type == "pickup_to_client":
                errand_guide_rider_roles[key].update({"pickup", "delivery"})

    # Errand rule: if same rider performs pickup and delivery, it counts as one tariff event.
    for (_guide_id, rider_id), roles in errand_guide_rider_roles.items():
        if "pickup" in roles and "delivery" in roles and counts[rider_id] > 1:
            counts[rider_id] -= 1

    return [(rider_id, int(counts[rider_id]), float(totals[rider_id])) for rider_id in totals.keys()]


def compute_station_rows(db: Session, start_dt: datetime, end_dt: datetime) -> list[tuple[str, int, float]]:
    rows = (
        db.query(
            Guide.station_id,
            func.count(Guide.id),
            func.coalesce(func.sum(Guide.sale_amount), 0.0),
        )
        .filter(
            Guide.station_id.is_not(None),
            Guide.created_at >= start_dt,
            Guide.created_at < end_dt,
        )
        .group_by(Guide.station_id)
        .all()
    )
    return [(station_id, int(count), float(total or 0.0)) for station_id, count, total in rows]


def compute_rider_leg_type_rows(db: Session, start_dt: datetime, end_dt: datetime) -> list[tuple[str, str, int, float]]:
    rows = (
        db.query(
            RouteLeg.assigned_rider_id,
            RouteLeg.leg_type,
            func.count(RouteLeg.id),
            func.coalesce(func.sum(RouteLeg.rider_fee_amount), 0.0),
        )
        .filter(
            RouteLeg.assigned_rider_id.is_not(None),
            RouteLeg.status == "completed",
            RouteLeg.updated_at >= start_dt,
            RouteLeg.updated_at < end_dt,
        )
        .group_by(RouteLeg.assigned_rider_id, RouteLeg.leg_type)
        .all()
    )
    return [
        (rider_id, str(leg_type), int(count), float(total or 0.0))
        for rider_id, leg_type, count, total in rows
    ]


def _resolve_station_for_leg(leg: RouteLeg) -> str | None:
    if leg.leg_type in {"station_to_station", "pickup_to_station", "pickup_to_origin_station"}:
        return leg.origin_station_id
    if leg.leg_type in {"station_to_client", "destination_station_to_client"}:
        return leg.destination_station_id or leg.origin_station_id
    return leg.origin_station_id or leg.destination_station_id


def compute_station_leg_type_rows(db: Session, start_dt: datetime, end_dt: datetime) -> list[tuple[str, str, int, float]]:
    legs = (
        db.query(RouteLeg)
        .filter(
            RouteLeg.status == "completed",
            RouteLeg.updated_at >= start_dt,
            RouteLeg.updated_at < end_dt,
        )
        .all()
    )
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"count": 0, "total": 0.0})
    for leg in legs:
        station_id = _resolve_station_for_leg(leg)
        if not station_id:
            continue
        key = (station_id, leg.leg_type)
        grouped[key]["count"] += 1
        grouped[key]["total"] += float(leg.station_fee_amount or 0.0)

    return [
        (station_id, leg_type, int(values["count"]), float(values["total"]))
        for (station_id, leg_type), values in grouped.items()
    ]


def close_rider_week(
    db: Session,
    monday: date,
    start_dt: datetime,
    end_dt: datetime,
    *,
    commit: bool = True,
) -> list[tuple[str, int, float]]:
    rows = compute_rider_rows(db, start_dt, end_dt)
    for rider_id, count, total in rows:
        snapshot = (
            db.query(RiderCommission)
            .filter(RiderCommission.rider_id == rider_id, RiderCommission.week_start == monday)
            .with_for_update()
            .first()
        )
        if snapshot:
            snapshot.delivery_count = count
            snapshot.total_amount = total
        else:
            db.add(
                RiderCommission(
                    rider_id=rider_id,
                    week_start=monday,
                    delivery_count=count,
                    total_amount=total,
                    state="confirmed",
                )
            )
    if commit:
        db.commit()
    return rows


def close_station_week(
    db: Session,
    monday: date,
    start_dt: datetime,
    end_dt: datetime,
    *,
    commit: bool = True,
) -> list[tuple[str, int, float]]:
    rows = compute_station_rows(db, start_dt, end_dt)
    for station_id, count, total in rows:
        snapshot = (
            db.query(StationCommission)
            .filter(StationCommission.station_id == station_id, StationCommission.week_start == monday)
            .with_for_update()
            .first()
        )
        if snapshot:
            snapshot.sold_guide_count = count
            snapshot.sold_guide_amount = total
            snapshot.total_amount = total
        else:
            db.add(
                StationCommission(
                    station_id=station_id,
                    week_start=monday,
                    sold_guide_count=count,
                    sold_guide_amount=total,
                    total_amount=total,
                    state="confirmed",
                )
            )
    if commit:
        db.commit()
    return rows


def close_weekly_commissions(db: Session, week_start: str | None = None, previous_week: bool = False) -> dict[str, int]:
    start_dt, end_dt, monday = resolve_week_window(week_start=week_start, previous_week=previous_week)

    # Idempotent: return existing result if this week was already closed successfully.
    existing = (
        db.query(CommissionClose)
        .filter(CommissionClose.week_start == monday, CommissionClose.status == "success")
        .first()
    )
    if existing:
        return {
            "rider_snapshots": existing.rider_snapshots,
            "station_snapshots": existing.station_snapshots,
            "week_start": monday.isoformat(),
            "already_closed": True,
        }

    # Claim the closure slot; unique constraint blocks concurrent runs for same week.
    close_record = CommissionClose(week_start=monday, status="in_progress")
    db.add(close_record)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Commission close already in progress for week {monday.isoformat()}")

    try:
        rider_rows = close_rider_week(db, monday, start_dt, end_dt, commit=False)
        station_rows = close_station_week(db, monday, start_dt, end_dt, commit=False)
        close_record.status = "success"
        close_record.rider_snapshots = len(rider_rows)
        close_record.station_snapshots = len(station_rows)
        close_record.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as exc:
        db.rollback()
        failed_record = db.query(CommissionClose).filter(CommissionClose.week_start == monday).first()
        if not failed_record:
            failed_record = CommissionClose(week_start=monday)
            db.add(failed_record)
        failed_record.status = "failed"
        failed_record.error_message = str(exc)[:2000]
        failed_record.completed_at = datetime.now(timezone.utc)
        db.commit()
        raise

    return {
        "rider_snapshots": len(rider_rows),
        "station_snapshots": len(station_rows),
        "week_start": monday.isoformat(),
    }
