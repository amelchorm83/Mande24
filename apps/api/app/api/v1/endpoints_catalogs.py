from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.models import PricingRule, Rider, Service, Station, User, UserRole, Zone
from app.db.session import get_db
from app.models.schemas import (
    PricingRuleCreate,
    PricingRuleResponse,
    RiderCreate,
    RiderResponse,
    ServiceCreate,
    ServiceResponse,
    StationCreate,
    StationResponse,
    ZoneCreate,
    ZoneResponse,
)

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.post("/services", response_model=ServiceResponse)
def create_service(
    payload: ServiceCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> ServiceResponse:
    existing = db.query(Service).filter(Service.name == payload.name.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service name already exists")

    service = Service(
        name=payload.name.strip(),
        description=payload.description,
        service_type=payload.service_type,
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return ServiceResponse(
        id=service.id,
        name=service.name,
        description=service.description,
        service_type=service.service_type,
        active=service.active,
    )


@router.get("/services", response_model=list[ServiceResponse])
def list_services(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ServiceResponse]:
    services = db.query(Service).order_by(Service.name.asc()).all()
    return [
        ServiceResponse(
            id=item.id,
            name=item.name,
            description=item.description,
            service_type=item.service_type,
            active=item.active,
        )
        for item in services
    ]


@router.post("/zones", response_model=ZoneResponse)
def create_zone(
    payload: ZoneCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> ZoneResponse:
    existing = db.query(Zone).filter(Zone.code == payload.code.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Zone code already exists")

    zone = Zone(name=payload.name.strip(), code=payload.code.strip().upper())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return ZoneResponse(id=zone.id, name=zone.name, code=zone.code, active=zone.active)


@router.get("/zones", response_model=list[ZoneResponse])
def list_zones(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ZoneResponse]:
    zones = db.query(Zone).order_by(Zone.name.asc()).all()
    return [ZoneResponse(id=item.id, name=item.name, code=item.code, active=item.active) for item in zones]


@router.post("/stations", response_model=StationResponse)
def create_station(
    payload: StationCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> StationResponse:
    zone = db.query(Zone).filter(Zone.id == payload.zone_id).first()
    if not zone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    existing = db.query(Station).filter(Station.name == payload.name.strip()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Station name already exists")

    station = Station(
        name=payload.name.strip(),
        zone_id=payload.zone_id,
        landline_phone=payload.landline_phone.strip(),
        whatsapp_phone=payload.whatsapp_phone.strip(),
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return StationResponse(
        id=station.id,
        name=station.name,
        zone_id=station.zone_id,
        landline_phone=station.landline_phone,
        whatsapp_phone=station.whatsapp_phone,
        active=station.active,
    )


@router.get("/stations", response_model=list[StationResponse])
def list_stations(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[StationResponse]:
    stations = db.query(Station).order_by(Station.name.asc()).all()
    return [
        StationResponse(
            id=item.id,
            name=item.name,
            zone_id=item.zone_id,
            landline_phone=item.landline_phone,
            whatsapp_phone=item.whatsapp_phone,
            active=item.active,
        )
        for item in stations
    ]


@router.post("/riders", response_model=RiderResponse)
def create_rider(
    payload: RiderCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> RiderResponse:
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.query(Rider).filter(Rider.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Rider already exists for user")

    if payload.zone_id:
        zone = db.query(Zone).filter(Zone.id == payload.zone_id).first()
        if not zone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    rider = Rider(
        user_id=payload.user_id,
        zone_id=payload.zone_id,
        vehicle_type=payload.vehicle_type.strip(),
        landline_phone=payload.landline_phone.strip(),
        whatsapp_phone=payload.whatsapp_phone.strip(),
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)
    return RiderResponse(
        id=rider.id,
        user_id=rider.user_id,
        zone_id=rider.zone_id,
        vehicle_type=rider.vehicle_type,
        landline_phone=rider.landline_phone,
        whatsapp_phone=rider.whatsapp_phone,
        state=rider.state,
        active=rider.active,
    )


@router.get("/riders", response_model=list[RiderResponse])
def list_riders(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[RiderResponse]:
    riders = db.query(Rider).order_by(Rider.id.desc()).all()
    return [
        RiderResponse(
            id=item.id,
            user_id=item.user_id,
            zone_id=item.zone_id,
            vehicle_type=item.vehicle_type,
            landline_phone=item.landline_phone,
            whatsapp_phone=item.whatsapp_phone,
            state=item.state,
            active=item.active,
        )
        for item in riders
    ]


@router.post("/pricing-rules", response_model=PricingRuleResponse)
def create_pricing_rule(
    payload: PricingRuleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> PricingRuleResponse:
    service = db.query(Service).filter(Service.id == payload.service_id).first()
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")

    station = db.query(Station).filter(Station.id == payload.station_id).first()
    if not station:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")

    existing = (
        db.query(PricingRule)
        .filter(PricingRule.service_id == payload.service_id, PricingRule.station_id == payload.station_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Pricing rule already exists")

    rule = PricingRule(
        service_id=payload.service_id,
        station_id=payload.station_id,
        price=payload.price,
        pickup_fee=payload.pickup_fee,
        delivery_fee=payload.delivery_fee,
        transfer_fee=payload.transfer_fee,
        station_fee=payload.station_fee,
        currency=payload.currency.strip().upper(),
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return PricingRuleResponse(
        id=rule.id,
        service_id=rule.service_id,
        station_id=rule.station_id,
        price=rule.price,
        pickup_fee=rule.pickup_fee,
        delivery_fee=rule.delivery_fee,
        transfer_fee=rule.transfer_fee,
        station_fee=rule.station_fee,
        currency=rule.currency,
        active=rule.active,
    )


@router.get("/pricing-rules", response_model=list[PricingRuleResponse])
def list_pricing_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[PricingRuleResponse]:
    rules = db.query(PricingRule).order_by(PricingRule.id.desc()).all()
    return [
        PricingRuleResponse(
            id=item.id,
            service_id=item.service_id,
            station_id=item.station_id,
            price=item.price,
            pickup_fee=item.pickup_fee,
            delivery_fee=item.delivery_fee,
            transfer_fee=item.transfer_fee,
            station_fee=item.station_fee,
            currency=item.currency,
            active=item.active,
        )
        for item in rules
    ]
