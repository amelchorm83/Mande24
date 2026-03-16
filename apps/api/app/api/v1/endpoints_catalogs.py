from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.api.deps import get_current_user, require_roles
from app.db.models import GeoColony, GeoMunicipality, GeoPostalCode, GeoState, PricingRule, QuotePolicyRule, Region, Rider, Service, Station, StationCoverageRule, User, UserRole, Zone, ZoneSurchargeRule
from app.db.session import get_db
from app.models.schemas import (
    PricingRuleCreate,
    PricingRuleResponse,
    QuotePolicyRuleCreate,
    QuotePolicyRuleResponse,
    QuotePolicyRuleUpdate,
    RegionCreate,
    RegionResponse,
    RiderCreate,
    RiderResponse,
    ServiceCreate,
    ServiceResponse,
    StationCreate,
    StationResponse,
    ZoneCreate,
    ZoneSurchargeRuleCreate,
    ZoneSurchargeRuleResponse,
    ZoneSurchargeRuleUpdate,
    ZoneResponse,
)

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


def _normalize_datetime_range(valid_from: datetime | None, valid_to: datetime | None) -> tuple[datetime, datetime | None]:
    now = datetime.now(timezone.utc)
    normalized_from = valid_from or now
    if valid_to and valid_to < normalized_from:
        raise HTTPException(status_code=400, detail="valid_to must be greater than or equal to valid_from")
    return normalized_from, valid_to


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

    region_id = (payload.region_id or "").strip() or None
    if region_id and not db.query(Region).filter(Region.id == region_id, Region.active.is_(True)).first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Region not found")

    zone = Zone(name=payload.name.strip(), code=payload.code.strip().upper(), region_id=region_id)
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return ZoneResponse(id=zone.id, name=zone.name, code=zone.code, region_id=zone.region_id, active=zone.active)


@router.get("/zones", response_model=list[ZoneResponse])
def list_zones(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ZoneResponse]:
    zones = db.query(Zone).order_by(Zone.name.asc()).all()
    return [ZoneResponse(id=item.id, name=item.name, code=item.code, region_id=item.region_id, active=item.active) for item in zones]


@router.post("/regions", response_model=RegionResponse)
def create_region(
    payload: RegionCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> RegionResponse:
    existing = db.query(Region).filter(Region.code == payload.code.strip().upper()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Region code already exists")
    row = Region(name=payload.name.strip(), code=payload.code.strip().upper(), active=True)
    db.add(row)
    db.commit()
    db.refresh(row)
    return RegionResponse(id=row.id, name=row.name, code=row.code, active=row.active)


@router.get("/regions", response_model=list[RegionResponse])
def list_regions(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[RegionResponse]:
    rows = db.query(Region).order_by(Region.name.asc()).all()
    return [RegionResponse(id=item.id, name=item.name, code=item.code, active=item.active) for item in rows]


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
        responsible_name=payload.responsible_name.strip(),
        proof_of_address_file=payload.proof_of_address_file.strip(),
        rfc_file=payload.rfc_file.strip(),
        comprobaciones_file=payload.comprobaciones_file.strip(),
        work_days=payload.work_days.strip(),
        rest_day=payload.rest_day.strip().lower(),
        opening_time=payload.opening_time.strip(),
        closing_time=payload.closing_time.strip(),
        max_active_users=payload.max_active_users,
    )
    db.add(station)
    db.flush()

    for row in payload.coverage_rows:
        state_code = row.state_code.strip().upper()
        municipality_code = (row.municipality_code or "").strip().upper() or None
        postal_code = (row.postal_code or "").strip() or None
        colony_id = (row.colony_id or "").strip() or None

        if not db.query(GeoState).filter(GeoState.code == state_code).first():
            raise HTTPException(status_code=400, detail="Coverage state not found")
        if municipality_code and not db.query(GeoMunicipality).filter(GeoMunicipality.code == municipality_code, GeoMunicipality.state_code == state_code).first():
            raise HTTPException(status_code=400, detail="Coverage municipality not valid for state")
        if postal_code and municipality_code and not db.query(GeoPostalCode).filter(GeoPostalCode.code == postal_code, GeoPostalCode.municipality_code == municipality_code).first():
            raise HTTPException(status_code=400, detail="Coverage postal code not valid for municipality")
        if colony_id:
            colony = db.query(GeoColony).filter(GeoColony.id == colony_id).first()
            if not colony:
                raise HTTPException(status_code=400, detail="Coverage colony not found")
            if colony.state_code != state_code:
                raise HTTPException(status_code=400, detail="Coverage colony not valid for state")
            if municipality_code and colony.municipality_code != municipality_code:
                raise HTTPException(status_code=400, detail="Coverage colony not valid for municipality")
            if postal_code and colony.postal_code != postal_code:
                raise HTTPException(status_code=400, detail="Coverage colony not valid for postal code")

        exists = (
            db.query(StationCoverageRule)
            .filter(
                StationCoverageRule.station_id == station.id,
                StationCoverageRule.state_code == state_code,
                StationCoverageRule.municipality_code == municipality_code,
                StationCoverageRule.postal_code == postal_code,
                StationCoverageRule.colony_id == colony_id,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            StationCoverageRule(
                station_id=station.id,
                state_code=state_code,
                municipality_code=municipality_code,
                postal_code=postal_code,
                colony_id=colony_id,
                active=True,
            )
        )

    db.commit()
    db.refresh(station)
    return StationResponse(
        id=station.id,
        name=station.name,
        zone_id=station.zone_id,
        landline_phone=station.landline_phone,
        whatsapp_phone=station.whatsapp_phone,
        responsible_name=station.responsible_name,
        proof_of_address_file=station.proof_of_address_file,
        rfc_file=station.rfc_file,
        comprobaciones_file=station.comprobaciones_file,
        work_days=station.work_days,
        rest_day=station.rest_day,
        opening_time=station.opening_time,
        closing_time=station.closing_time,
        max_active_users=station.max_active_users,
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
            responsible_name=item.responsible_name,
            proof_of_address_file=item.proof_of_address_file,
            rfc_file=item.rfc_file,
            comprobaciones_file=item.comprobaciones_file,
            work_days=item.work_days,
            rest_day=item.rest_day,
            opening_time=item.opening_time,
            closing_time=item.closing_time,
            max_active_users=item.max_active_users,
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

    station_id = payload.station_id
    resolved_zone_id = payload.zone_id
    if station_id:
        station = db.query(Station).filter(Station.id == station_id, Station.active.is_(True)).first()
        if not station:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Station not found")
        if resolved_zone_id and station.zone_id != resolved_zone_id:
            raise HTTPException(status_code=400, detail="Station does not belong to selected zone")
        resolved_zone_id = station.zone_id

    if resolved_zone_id:
        zone = db.query(Zone).filter(Zone.id == resolved_zone_id).first()
        if not zone:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found")

    rider = Rider(
        user_id=payload.user_id,
        zone_id=resolved_zone_id,
        station_id=station_id,
        vehicle_type=payload.vehicle_type.strip(),
        landline_phone=payload.landline_phone.strip(),
        whatsapp_phone=payload.whatsapp_phone.strip(),
        license_file=payload.license_file.strip(),
        license_expires_at=payload.license_expires_at,
        circulation_card_file=payload.circulation_card_file.strip(),
        insurance_policy_file=payload.insurance_policy_file.strip(),
        insurance_expires_at=payload.insurance_expires_at,
        contract_file=payload.contract_file.strip(),
        contract_signed_at=payload.contract_signed_at,
        comprobaciones_file=payload.comprobaciones_file.strip(),
        work_days=payload.work_days.strip(),
        rest_day=payload.rest_day.strip().lower(),
        is_available=payload.is_available,
        account_status=payload.account_status,
    )
    db.add(rider)
    db.commit()
    db.refresh(rider)
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
            station_id=item.station_id,
            vehicle_type=item.vehicle_type,
            landline_phone=item.landline_phone,
            whatsapp_phone=item.whatsapp_phone,
            license_file=item.license_file,
            license_expires_at=item.license_expires_at,
            circulation_card_file=item.circulation_card_file,
            insurance_policy_file=item.insurance_policy_file,
            insurance_expires_at=item.insurance_expires_at,
            contract_file=item.contract_file,
            contract_signed_at=item.contract_signed_at,
            comprobaciones_file=item.comprobaciones_file,
            work_days=item.work_days,
            rest_day=item.rest_day,
            is_available=item.is_available,
            account_status=item.account_status,
            state=item.state,
            active=item.active,
        )
        for item in riders
    ]


@router.post("/quote-policy-rules", response_model=QuotePolicyRuleResponse)
def create_quote_policy_rule(
    payload: QuotePolicyRuleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> QuotePolicyRuleResponse:
    service_type = payload.service_type.strip().lower()
    fallback_service = (payload.fallback_service_type or "").strip().lower() or None
    valid_from, valid_to = _normalize_datetime_range(payload.valid_from, payload.valid_to)

    row = QuotePolicyRule(
        service_type=service_type,
        fallback_service_type=fallback_service,
        max_distance_km=payload.max_distance_km,
        service_factor=payload.service_factor,
        active=payload.active,
        valid_from=valid_from,
        valid_to=valid_to,
        notes=(payload.notes.strip() if payload.notes else None),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return QuotePolicyRuleResponse(
        id=row.id,
        service_type=row.service_type,
        fallback_service_type=row.fallback_service_type,
        max_distance_km=row.max_distance_km,
        service_factor=row.service_factor,
        active=row.active,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        notes=row.notes,
    )


@router.get("/quote-policy-rules", response_model=list[QuotePolicyRuleResponse])
def list_quote_policy_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[QuotePolicyRuleResponse]:
    rows = db.query(QuotePolicyRule).order_by(QuotePolicyRule.service_type.asc(), QuotePolicyRule.valid_from.desc()).all()
    return [
        QuotePolicyRuleResponse(
            id=row.id,
            service_type=row.service_type,
            fallback_service_type=row.fallback_service_type,
            max_distance_km=row.max_distance_km,
            service_factor=row.service_factor,
            active=row.active,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            notes=row.notes,
        )
        for row in rows
    ]


@router.patch("/quote-policy-rules/{rule_id}", response_model=QuotePolicyRuleResponse)
def update_quote_policy_rule(
    rule_id: str,
    payload: QuotePolicyRuleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> QuotePolicyRuleResponse:
    row = db.query(QuotePolicyRule).filter(QuotePolicyRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Quote policy rule not found")

    if payload.fallback_service_type is not None:
        row.fallback_service_type = payload.fallback_service_type.strip().lower() or None
    if payload.max_distance_km is not None:
        row.max_distance_km = payload.max_distance_km
    if payload.service_factor is not None:
        row.service_factor = payload.service_factor
    if payload.active is not None:
        row.active = payload.active
    if payload.notes is not None:
        row.notes = payload.notes.strip() or None

    valid_from = payload.valid_from if payload.valid_from is not None else row.valid_from
    valid_to = payload.valid_to if payload.valid_to is not None else row.valid_to
    valid_from, valid_to = _normalize_datetime_range(valid_from, valid_to)
    row.valid_from = valid_from
    row.valid_to = valid_to

    db.commit()
    db.refresh(row)
    return QuotePolicyRuleResponse(
        id=row.id,
        service_type=row.service_type,
        fallback_service_type=row.fallback_service_type,
        max_distance_km=row.max_distance_km,
        service_factor=row.service_factor,
        active=row.active,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        notes=row.notes,
    )


@router.post("/zone-surcharge-rules", response_model=ZoneSurchargeRuleResponse)
def create_zone_surcharge_rule(
    payload: ZoneSurchargeRuleCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> ZoneSurchargeRuleResponse:
    valid_from, valid_to = _normalize_datetime_range(payload.valid_from, payload.valid_to)
    row = ZoneSurchargeRule(
        zone_type=payload.zone_type.strip().lower(),
        rural_complexity=(payload.rural_complexity.strip().lower() if payload.rural_complexity else None),
        zone_factor=payload.zone_factor,
        complexity_factor=payload.complexity_factor,
        eta_extra_minutes=payload.eta_extra_minutes,
        active=payload.active,
        valid_from=valid_from,
        valid_to=valid_to,
        notes=(payload.notes.strip() if payload.notes else None),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ZoneSurchargeRuleResponse(
        id=row.id,
        zone_type=row.zone_type,
        rural_complexity=row.rural_complexity,
        zone_factor=row.zone_factor,
        complexity_factor=row.complexity_factor,
        eta_extra_minutes=row.eta_extra_minutes,
        active=row.active,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        notes=row.notes,
    )


@router.get("/zone-surcharge-rules", response_model=list[ZoneSurchargeRuleResponse])
def list_zone_surcharge_rules(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ZoneSurchargeRuleResponse]:
    rows = (
        db.query(ZoneSurchargeRule)
        .order_by(ZoneSurchargeRule.zone_type.asc(), ZoneSurchargeRule.rural_complexity.asc(), ZoneSurchargeRule.valid_from.desc())
        .all()
    )
    return [
        ZoneSurchargeRuleResponse(
            id=row.id,
            zone_type=row.zone_type,
            rural_complexity=row.rural_complexity,
            zone_factor=row.zone_factor,
            complexity_factor=row.complexity_factor,
            eta_extra_minutes=row.eta_extra_minutes,
            active=row.active,
            valid_from=row.valid_from,
            valid_to=row.valid_to,
            notes=row.notes,
        )
        for row in rows
    ]


@router.patch("/zone-surcharge-rules/{rule_id}", response_model=ZoneSurchargeRuleResponse)
def update_zone_surcharge_rule(
    rule_id: str,
    payload: ZoneSurchargeRuleUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin)),
) -> ZoneSurchargeRuleResponse:
    row = db.query(ZoneSurchargeRule).filter(ZoneSurchargeRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Zone surcharge rule not found")

    if payload.rural_complexity is not None:
        row.rural_complexity = payload.rural_complexity.strip().lower() or None
    if payload.zone_factor is not None:
        row.zone_factor = payload.zone_factor
    if payload.complexity_factor is not None:
        row.complexity_factor = payload.complexity_factor
    if payload.eta_extra_minutes is not None:
        row.eta_extra_minutes = payload.eta_extra_minutes
    if payload.active is not None:
        row.active = payload.active
    if payload.notes is not None:
        row.notes = payload.notes.strip() or None

    valid_from = payload.valid_from if payload.valid_from is not None else row.valid_from
    valid_to = payload.valid_to if payload.valid_to is not None else row.valid_to
    valid_from, valid_to = _normalize_datetime_range(valid_from, valid_to)
    row.valid_from = valid_from
    row.valid_to = valid_to

    db.commit()
    db.refresh(row)
    return ZoneSurchargeRuleResponse(
        id=row.id,
        zone_type=row.zone_type,
        rural_complexity=row.rural_complexity,
        zone_factor=row.zone_factor,
        complexity_factor=row.complexity_factor,
        eta_extra_minutes=row.eta_extra_minutes,
        active=row.active,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        notes=row.notes,
    )


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
