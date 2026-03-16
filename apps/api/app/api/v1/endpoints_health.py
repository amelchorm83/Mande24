from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.models import CommissionClose, RiderCommission, RouteLeg, StationCommission, User, UserRole
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/commissions")
def commission_health(
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> dict:
    """Returns financial integrity indicators for commission management."""
    close_records = db.query(func.count(CommissionClose.id)).scalar() or 0
    failed_closes = (
        db.query(func.count(CommissionClose.id))
        .filter(CommissionClose.status == "failed")
        .scalar()
    ) or 0
    in_progress_closes = (
        db.query(func.count(CommissionClose.id))
        .filter(CommissionClose.status == "in_progress")
        .scalar()
    ) or 0
    successful_closes = (
        db.query(func.count(CommissionClose.id))
        .filter(CommissionClose.status == "success")
        .scalar()
    ) or 0
    rider_commission_count = db.query(func.count(RiderCommission.id)).scalar() or 0
    station_commission_count = db.query(func.count(StationCommission.id)).scalar() or 0
    completed_legs = (
        db.query(func.count(RouteLeg.id))
        .filter(RouteLeg.status == "completed", RouteLeg.assigned_rider_id.isnot(None))
        .scalar()
    ) or 0

    status = "ok"
    if failed_closes > 0 or in_progress_closes > 0:
        status = "degraded"

    return {
        "status": status,
        "commission_closes": {
            "total": close_records,
            "successful": successful_closes,
            "failed": failed_closes,
            "in_progress": in_progress_closes,
        },
        "rider_commissions": rider_commission_count,
        "station_commissions": station_commission_count,
        "completed_route_legs": completed_legs,
    }
