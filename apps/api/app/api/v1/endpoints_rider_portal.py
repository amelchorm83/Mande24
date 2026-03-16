from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.models import Rider, RiderAccountStatus, User, UserRole
from app.db.session import get_db
from app.models.schemas import RiderProfileUpdate, RiderResponse

router = APIRouter(prefix="/rider-portal", tags=["rider-portal"])


def _to_rider_response(rider: Rider) -> RiderResponse:
    return RiderResponse(
        id=rider.id,
        user_id=rider.user_id,
        zone_id=rider.zone_id,
        station_id=rider.station_id,
        vehicle_type=rider.vehicle_type,
        landline_phone=rider.landline_phone,
        whatsapp_phone=rider.whatsapp_phone,
        license_file=rider.license_file,
        license_expires_at=rider.license_expires_at,
        circulation_card_file=rider.circulation_card_file,
        insurance_policy_file=rider.insurance_policy_file,
        insurance_expires_at=rider.insurance_expires_at,
        contract_file=rider.contract_file,
        contract_signed_at=rider.contract_signed_at,
        comprobaciones_file=rider.comprobaciones_file,
        work_days=rider.work_days,
        rest_day=rider.rest_day,
        is_available=rider.is_available,
        account_status=rider.account_status,
        state=rider.state,
        active=rider.active,
    )


@router.get("/me", response_model=RiderResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.rider)),
) -> RiderResponse:
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider profile not found")
    return _to_rider_response(rider)


@router.put("/me", response_model=RiderResponse)
def update_my_profile(
    payload: RiderProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.rider)),
) -> RiderResponse:
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider profile not found")
    if rider.account_status != RiderAccountStatus.active or not rider.active:
        raise HTTPException(status_code=403, detail="Account is not active")

    # Email is authentication key; rider cannot change it from portal.
    user.full_name = payload.full_name.strip()
    rider.landline_phone = payload.landline_phone.strip()
    rider.whatsapp_phone = payload.whatsapp_phone.strip()
    rider.vehicle_type = payload.vehicle_type.strip()
    rider.license_file = payload.license_file.strip()
    rider.license_expires_at = payload.license_expires_at
    rider.circulation_card_file = payload.circulation_card_file.strip()
    rider.insurance_policy_file = payload.insurance_policy_file.strip()
    rider.insurance_expires_at = payload.insurance_expires_at
    rider.contract_file = payload.contract_file.strip()
    rider.contract_signed_at = payload.contract_signed_at
    rider.comprobaciones_file = payload.comprobaciones_file.strip()
    rider.work_days = payload.work_days.strip()
    rider.rest_day = payload.rest_day.strip().lower()

    db.commit()
    db.refresh(rider)
    return _to_rider_response(rider)


@router.patch("/me/availability", response_model=RiderResponse)
def update_my_availability(
    available: bool,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.rider)),
) -> RiderResponse:
    rider = db.query(Rider).filter(Rider.user_id == user.id).first()
    if not rider:
        raise HTTPException(status_code=404, detail="Rider profile not found")
    if rider.account_status != RiderAccountStatus.active or not rider.active:
        raise HTTPException(status_code=403, detail="Account is not active")

    rider.is_available = available
    db.commit()
    db.refresh(rider)
    return _to_rider_response(rider)
