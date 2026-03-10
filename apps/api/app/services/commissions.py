from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Delivery, Guide, RiderCommission, RouteLeg, StationCommission, WorkflowStage


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
        db.query(
            Delivery.rider_id,
            func.count(Delivery.id),
            func.coalesce(func.sum(Delivery.commission_amount), 0.0),
        )
        .filter(
            Delivery.rider_id.is_not(None),
            Delivery.stage == WorkflowStage.delivered,
            Delivery.delivered_at >= start_dt,
            Delivery.delivered_at < end_dt,
        )
        .group_by(Delivery.rider_id)
        .all()
    )
    return [(rider_id, int(count), float(total or 0.0)) for rider_id, count, total in rows]


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


def close_rider_week(db: Session, monday: date, start_dt: datetime, end_dt: datetime) -> list[tuple[str, int, float]]:
    rows = compute_rider_rows(db, start_dt, end_dt)
    for rider_id, count, total in rows:
        snapshot = (
            db.query(RiderCommission)
            .filter(RiderCommission.rider_id == rider_id, RiderCommission.week_start == monday)
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
    db.commit()
    return rows


def close_station_week(db: Session, monday: date, start_dt: datetime, end_dt: datetime) -> list[tuple[str, int, float]]:
    rows = compute_station_rows(db, start_dt, end_dt)
    for station_id, count, total in rows:
        snapshot = (
            db.query(StationCommission)
            .filter(StationCommission.station_id == station_id, StationCommission.week_start == monday)
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
    db.commit()
    return rows


def close_weekly_commissions(db: Session, week_start: str | None = None, previous_week: bool = False) -> dict[str, int]:
    start_dt, end_dt, monday = resolve_week_window(week_start=week_start, previous_week=previous_week)
    rider_rows = close_rider_week(db, monday, start_dt, end_dt)
    station_rows = close_station_week(db, monday, start_dt, end_dt)
    return {
        "rider_snapshots": len(rider_rows),
        "station_snapshots": len(station_rows),
        "week_start": monday.isoformat(),
    }
