from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.models import RiderCommission, StationCommission, User, UserRole
from app.db.session import get_db
from app.models.schemas import (
    RiderLegTypeWeeklyCommissionResponse,
    RiderLegTypeWeeklyCommissionRow,
    RiderCommissionHistoryRow,
    RiderWeeklyCommissionResponse,
    RiderWeeklyCommissionRow,
    StationLegTypeWeeklyCommissionResponse,
    StationLegTypeWeeklyCommissionRow,
    StationCommissionHistoryRow,
    StationWeeklyCommissionResponse,
    StationWeeklyCommissionRow,
)
from app.services.commissions import (
    close_rider_week,
    close_station_week,
    compute_rider_leg_type_rows,
    compute_rider_rows,
    compute_station_leg_type_rows,
    compute_station_rows,
    resolve_week_window,
)

router = APIRouter(prefix="/commissions", tags=["commissions"])


def _resolve_week_window_or_422(week_start: str | None):
    try:
        return resolve_week_window(week_start)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid week_start. Expected YYYY-MM-DD") from exc


@router.get("/riders/weekly", response_model=RiderWeeklyCommissionResponse)
def rider_weekly_commissions(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> RiderWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = compute_rider_rows(db, start_dt, end_dt)
    rows = [
        RiderWeeklyCommissionRow(rider_id=rider_id, delivery_count=count, total_amount=total)
        for rider_id, count, total in tuples
    ]
    return RiderWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.get("/riders/weekly/by-leg", response_model=RiderLegTypeWeeklyCommissionResponse)
def rider_weekly_commissions_by_leg(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> RiderLegTypeWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = compute_rider_leg_type_rows(db, start_dt, end_dt)
    rows = [
        RiderLegTypeWeeklyCommissionRow(
            rider_id=rider_id,
            leg_type=leg_type,
            leg_count=count,
            total_amount=total,
        )
        for rider_id, leg_type, count, total in tuples
    ]
    return RiderLegTypeWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.post("/riders/weekly/close", response_model=RiderWeeklyCommissionResponse)
def close_rider_weekly_commissions(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> RiderWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = close_rider_week(db, monday, start_dt, end_dt)
    rows = [
        RiderWeeklyCommissionRow(rider_id=rider_id, delivery_count=count, total_amount=total)
        for rider_id, count, total in tuples
    ]
    return RiderWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.get("/riders/weekly/history", response_model=list[RiderCommissionHistoryRow])
def rider_weekly_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> list[RiderCommissionHistoryRow]:
    snapshots = db.query(RiderCommission).order_by(RiderCommission.week_start.desc()).limit(limit).all()
    return [
        RiderCommissionHistoryRow(
            rider_id=item.rider_id,
            week_start=item.week_start.isoformat(),
            delivery_count=item.delivery_count,
            total_amount=item.total_amount,
            state=item.state,
        )
        for item in snapshots
    ]


@router.get("/stations/weekly", response_model=StationWeeklyCommissionResponse)
def station_weekly_commissions(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> StationWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = compute_station_rows(db, start_dt, end_dt)
    rows = [
        StationWeeklyCommissionRow(
            station_id=station_id,
            sold_guide_count=count,
            sold_guide_amount=total,
            total_amount=total,
        )
        for station_id, count, total in tuples
    ]
    return StationWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.get("/stations/weekly/by-leg", response_model=StationLegTypeWeeklyCommissionResponse)
def station_weekly_commissions_by_leg(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> StationLegTypeWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = compute_station_leg_type_rows(db, start_dt, end_dt)
    rows = [
        StationLegTypeWeeklyCommissionRow(
            station_id=station_id,
            leg_type=leg_type,
            leg_count=count,
            total_amount=total,
        )
        for station_id, leg_type, count, total in tuples
    ]
    return StationLegTypeWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.post("/stations/weekly/close", response_model=StationWeeklyCommissionResponse)
def close_station_weekly_commissions(
    week_start: str | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> StationWeeklyCommissionResponse:
    start_dt, end_dt, monday = _resolve_week_window_or_422(week_start)
    tuples = close_station_week(db, monday, start_dt, end_dt)
    rows = [
        StationWeeklyCommissionRow(
            station_id=station_id,
            sold_guide_count=count,
            sold_guide_amount=total,
            total_amount=total,
        )
        for station_id, count, total in tuples
    ]
    return StationWeeklyCommissionResponse(
        week_start=monday.isoformat(),
        week_end=(monday + timedelta(days=6)).isoformat(),
        rows=rows,
    )


@router.get("/stations/weekly/history", response_model=list[StationCommissionHistoryRow])
def station_weekly_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> list[StationCommissionHistoryRow]:
    snapshots = db.query(StationCommission).order_by(StationCommission.week_start.desc()).limit(limit).all()
    return [
        StationCommissionHistoryRow(
            station_id=item.station_id,
            week_start=item.week_start.isoformat(),
            sold_guide_count=item.sold_guide_count,
            sold_guide_amount=item.sold_guide_amount,
            total_amount=item.total_amount,
            state=item.state,
        )
        for item in snapshots
    ]
