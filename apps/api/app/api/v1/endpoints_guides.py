from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.user_roles import user_has_role
from app.db.models import ClientProfile, Delivery, GeoColony, Guide, GuideParty, PricingRule, Rider, RiderAccountStatus, RouteLeg, Service, ServiceType, Station, StationCoverageRule, WorkflowStage, Zone
from app.db.models import User, UserRole
from app.db.session import get_db
from app.models.schemas import (
    DeliveryResponse,
    DeliveryStageUpdate,
    GuideCreate,
    GuideResponse,
    RouteLegAssignRequest,
    RouteLegResponse,
    RouteLegRiderSuggestionResponse,
)
from app.services.quote_policy import resolve_quote_policy

router = APIRouter(prefix="/guides", tags=["guides"])

VALID_ROUTE_LEG_STATUSES = {"planned", "assigned", "in_progress", "completed", "failed", "cancelled"}
ROUTE_LEG_MUTATING_STATUSES = {"in_progress", "completed", "failed"}
REQUESTER_ROLE_OPTIONS = {"origin", "destination", "external"}


def _service_type_value(service_type: object) -> str:
    raw = getattr(service_type, "value", service_type)
    return str(raw or "").strip().lower()


def _is_errand_service(service_type: object) -> bool:
    return _service_type_value(service_type) == ServiceType.errand.value


def _sanitize_requester_role(requester_role: str) -> str:
    value = requester_role.strip().lower()
    return value if value in REQUESTER_ROLE_OPTIONS else "origin"


def _rider_is_operational(rider: Rider) -> bool:
    return rider.active and rider.account_status == RiderAccountStatus.active and rider.is_available


def _to_guide_response(guide: Guide) -> GuideResponse:
    return GuideResponse(
        guide_code=guide.guide_code,
        customer_name=guide.customer_name,
        destination_name=guide.destination_name,
        service_type=guide.service_type,
        requested_service_type=(guide.deliveries[0].note.split("requested_service_type:", 1)[1].split(";", 1)[0] if guide.deliveries and guide.deliveries[0].note and "requested_service_type:" in guide.deliveries[0].note else None),
        service_converted=(bool(guide.deliveries and guide.deliveries[0].note and "service_converted:true" in guide.deliveries[0].note)),
        service_id=guide.service_id,
        station_id=guide.station_id,
        destination_station_id=guide.destination_station_id,
        sale_amount=guide.sale_amount,
        currency=guide.currency,
        created_at=guide.created_at,
    )


def _resolve_station_coverage(
    db: Session,
    state_code: str,
    municipality_code: str,
    postal_code: str,
    colony_id: str,
) -> Station | None:
    candidates = (
        db.query(StationCoverageRule)
        .filter(
            StationCoverageRule.active.is_(True),
            StationCoverageRule.state_code == state_code,
            or_(StationCoverageRule.municipality_code.is_(None), StationCoverageRule.municipality_code == municipality_code),
            or_(StationCoverageRule.postal_code.is_(None), StationCoverageRule.postal_code == postal_code),
            or_(StationCoverageRule.colony_id.is_(None), StationCoverageRule.colony_id == colony_id),
        )
        .all()
    )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            1 if item.colony_id else 0,
            1 if item.postal_code else 0,
            1 if item.municipality_code else 0,
            1 if item.state_code else 0,
        ),
        reverse=True,
    )
    for item in candidates:
        station = db.query(Station).filter(Station.id == item.station_id, Station.active.is_(True)).first()
        if station:
            return station
    return None


def _to_delivery_response(delivery: Delivery) -> DeliveryResponse:
    return DeliveryResponse(
        delivery_id=delivery.id,
        guide_code=delivery.guide.guide_code,
        stage=delivery.stage,
        updated_at=delivery.updated_at,
    )


def _to_route_leg_response(route_leg: RouteLeg, guide_code: str) -> RouteLegResponse:
    return RouteLegResponse(
        id=route_leg.id,
        guide_code=guide_code,
        sequence=route_leg.sequence,
        leg_type=route_leg.leg_type,
        from_node_type=route_leg.from_node_type,
        to_node_type=route_leg.to_node_type,
        origin_station_id=route_leg.origin_station_id,
        destination_station_id=route_leg.destination_station_id,
        assigned_rider_id=route_leg.assigned_rider_id,
        rider_fee_amount=route_leg.rider_fee_amount,
        station_fee_amount=route_leg.station_fee_amount,
        currency=route_leg.currency,
        status=route_leg.status,
        updated_at=route_leg.updated_at,
    )


def _build_route_legs(
    guide: Guide,
    pricing_rule: PricingRule,
    service_type: str,
    station_id: str,
    destination_station_id: str,
    use_station_handoff: bool,
    amount_multiplier: float = 1.0,
) -> list[RouteLeg]:
    route_legs: list[RouteLeg] = []
    service_kind = _service_type_value(service_type)
    pickup_fee = round(pricing_rule.pickup_fee * amount_multiplier, 2)
    transfer_fee = round(pricing_rule.transfer_fee * amount_multiplier, 2)
    delivery_fee = round(pricing_rule.delivery_fee * amount_multiplier, 2)
    station_fee = round(pricing_rule.station_fee * amount_multiplier, 2)

    if service_kind in {"messaging", "package"}:
        route_legs.append(
            RouteLeg(
                guide_id=guide.id,
                sequence=1,
                leg_type="pickup_to_origin_station",
                from_node_type="client_origin",
                to_node_type="station_origin",
                origin_station_id=station_id,
                destination_station_id=station_id,
                rider_fee_amount=pickup_fee,
                station_fee_amount=station_fee,
                currency=pricing_rule.currency,
                status="planned",
            )
        )

        if destination_station_id != station_id:
            route_legs.append(
                RouteLeg(
                    guide_id=guide.id,
                    sequence=2,
                    leg_type="station_to_station",
                    from_node_type="station_origin",
                    to_node_type="station_destination",
                    origin_station_id=station_id,
                    destination_station_id=destination_station_id,
                    rider_fee_amount=transfer_fee,
                    station_fee_amount=station_fee,
                    currency=pricing_rule.currency,
                    status="planned",
                )
            )
            delivery_sequence = 3
        else:
            delivery_sequence = 2

        route_legs.append(
            RouteLeg(
                guide_id=guide.id,
                sequence=delivery_sequence,
                leg_type="destination_station_to_client",
                from_node_type="station_destination",
                to_node_type="client_destination",
                origin_station_id=destination_station_id,
                destination_station_id=destination_station_id,
                rider_fee_amount=delivery_fee,
                station_fee_amount=station_fee,
                currency=pricing_rule.currency,
                status="planned",
            )
        )
        return route_legs

    if use_station_handoff:
        route_legs.append(
            RouteLeg(
                guide_id=guide.id,
                sequence=1,
                leg_type="pickup_to_station",
                from_node_type="client_origin",
                to_node_type="station_origin",
                origin_station_id=station_id,
                destination_station_id=station_id,
                rider_fee_amount=pickup_fee,
                station_fee_amount=station_fee,
                currency=pricing_rule.currency,
                status="planned",
            )
        )
        route_legs.append(
            RouteLeg(
                guide_id=guide.id,
                sequence=2,
                leg_type="station_to_client",
                from_node_type="station_origin",
                to_node_type="client_destination",
                origin_station_id=station_id,
                destination_station_id=destination_station_id,
                rider_fee_amount=delivery_fee,
                station_fee_amount=station_fee,
                currency=pricing_rule.currency,
                status="planned",
            )
        )
    else:
        route_legs.append(
            RouteLeg(
                guide_id=guide.id,
                sequence=1,
                leg_type="pickup_to_client",
                from_node_type="client_origin",
                to_node_type="client_destination",
                origin_station_id=station_id,
                destination_station_id=destination_station_id,
                rider_fee_amount=round((pickup_fee + delivery_fee), 2),
                station_fee_amount=station_fee,
                currency=pricing_rule.currency,
                status="planned",
            )
        )

    return route_legs


def _ensure_route_leg_transition(db: Session, route_leg: RouteLeg, new_status: str) -> None:
    if route_leg.status == new_status:
        return

    if route_leg.status == "completed" and new_status != "completed":
        raise HTTPException(status_code=400, detail="Completed route leg cannot move to another status")

    if new_status in ROUTE_LEG_MUTATING_STATUSES and not route_leg.assigned_rider_id:
        raise HTTPException(status_code=400, detail="Route leg requires assigned rider before execution")

    if new_status in {"in_progress", "completed"}:
        previous_leg = (
            db.query(RouteLeg)
            .filter(RouteLeg.guide_id == route_leg.guide_id, RouteLeg.sequence == route_leg.sequence - 1)
            .first()
        )
        if previous_leg and previous_leg.status != "completed":
            raise HTTPException(status_code=400, detail="Previous route leg must be completed first")


def _derive_delivery_stage(route_legs: list[RouteLeg]) -> WorkflowStage:
    if not route_legs:
        return WorkflowStage.assigned

    ordered = sorted(route_legs, key=lambda item: item.sequence)
    statuses = [item.status for item in ordered]

    if any(item == "failed" for item in statuses):
        return WorkflowStage.failed
    if all(item == "completed" for item in statuses):
        return WorkflowStage.delivered

    last_leg = ordered[-1]
    if last_leg.status == "in_progress":
        return WorkflowStage.out_for_delivery

    if any(item in {"in_progress", "assigned"} for item in statuses):
        return WorkflowStage.in_transit

    if any(item == "completed" for item in statuses):
        return WorkflowStage.at_station

    return WorkflowStage.assigned


def _sync_delivery_from_route_legs(db: Session, guide_id: str) -> None:
    delivery = db.query(Delivery).filter(Delivery.guide_id == guide_id).first()
    if not delivery:
        return

    route_legs = db.query(RouteLeg).filter(RouteLeg.guide_id == guide_id).order_by(RouteLeg.sequence.asc()).all()
    if not route_legs:
        return

    stage = _derive_delivery_stage(route_legs)
    if stage == WorkflowStage.delivered and not (delivery.has_evidence and delivery.has_signature):
        # Keep route progression complete, but require explicit evidence/signature confirmation.
        delivery.stage = WorkflowStage.out_for_delivery
    else:
        delivery.stage = stage

    if delivery.stage == WorkflowStage.delivered and not delivery.delivered_at:
        delivery.delivered_at = datetime.now(timezone.utc)
    if delivery.stage != WorkflowStage.delivered:
        delivery.delivered_at = None
    delivery.updated_at = datetime.now(timezone.utc)


def _suggest_riders_for_route_leg(db: Session, route_leg: RouteLeg) -> list[RouteLegRiderSuggestionResponse]:
    station_id = route_leg.origin_station_id or route_leg.destination_station_id
    station_zone_id = None
    preferred_station_id = None
    if station_id:
        station = db.query(Station).filter(Station.id == station_id, Station.active.is_(True)).first()
        if station:
            station_zone_id = station.zone_id
            preferred_station_id = station.id

    riders = db.query(Rider).filter(Rider.active.is_(True), Rider.account_status == RiderAccountStatus.active, Rider.is_available.is_(True)).all()
    if not riders:
        return []

    rows: list[RouteLegRiderSuggestionResponse] = []
    for rider in riders:
        same_station = bool(preferred_station_id and rider.station_id == preferred_station_id)
        same_zone = bool(station_zone_id and rider.zone_id == station_zone_id)
        if same_station:
            score = 0
            reason = "same_station"
        elif same_zone:
            score = 5
            reason = "same_zone"
        else:
            score = 10
            reason = "fallback_active"
        rows.append(
            RouteLegRiderSuggestionResponse(
                rider_id=rider.id,
                user_id=rider.user_id,
                zone_id=rider.zone_id,
                vehicle_type=rider.vehicle_type,
                score=score,
                reason=reason,
            )
        )

    rows.sort(key=lambda item: (item.score, item.rider_id))
    return rows


def _assigned_rider_for_guide(db: Session, guide_id: str) -> str | None:
    assigned = (
        db.query(RouteLeg.assigned_rider_id)
        .filter(RouteLeg.guide_id == guide_id, RouteLeg.assigned_rider_id.isnot(None))
        .order_by(RouteLeg.sequence.asc())
        .first()
    )
    return assigned[0] if assigned and assigned[0] else None


@router.post("", response_model=GuideResponse)
def create_guide(
    payload: GuideCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.client, UserRole.station)),
) -> GuideResponse:
    service = db.query(Service).filter(Service.id == payload.service_id, Service.active.is_(True)).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or inactive")

    station = db.query(Station).filter(Station.id == payload.station_id, Station.active.is_(True)).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found or inactive")

    destination_station_id = payload.destination_station_id or payload.station_id
    destination_station = db.query(Station).filter(Station.id == destination_station_id, Station.active.is_(True)).first()
    if not destination_station:
        raise HTTPException(status_code=404, detail="Destination station not found or inactive")

    requested_service_kind = _service_type_value(service.service_type)
    service_kind = requested_service_kind
    requester_role_clean = _sanitize_requester_role(payload.requester_role)
    policy_notes: list[str] = []
    policy_multiplier = 1.0

    requested_policy_service = "mandaditos" if requested_service_kind == ServiceType.errand.value else (
        "paqueteria" if requested_service_kind == ServiceType.package.value else "programado"
    )
    station_zone = db.query(Zone).filter(Zone.id == station.zone_id).first() if station.zone_id else None
    zone_code = station_zone.code.strip().lower() if station_zone and station_zone.code else "urbana"
    quote_policy = resolve_quote_policy(
        db=db,
        requested_service_type=requested_policy_service,
        distance_km=payload.distance_km or 0.0,
        zone_type=zone_code,
        rural_complexity="media",
    )
    policy_notes = quote_policy.policy_notes
    policy_multiplier = quote_policy.zone_factor * quote_policy.complexity_factor * quote_policy.service_factor

    origin_client = None
    destination_client = None
    if payload.origin_client_id:
        origin_client = db.query(ClientProfile).filter(ClientProfile.id == payload.origin_client_id, ClientProfile.active.is_(True)).first()
        if not origin_client:
            raise HTTPException(status_code=404, detail="Origin client not found or inactive")

    if payload.destination_client_id:
        destination_client = db.query(ClientProfile).filter(ClientProfile.id == payload.destination_client_id, ClientProfile.active.is_(True)).first()
        if not destination_client:
            raise HTTPException(status_code=404, detail="Destination client not found or inactive")

    origin_user = None
    destination_user = None
    if origin_client and origin_client.user_id:
        origin_user = db.query(User).filter(User.id == origin_client.user_id).first()
    if destination_client and destination_client.user_id:
        destination_user = db.query(User).filter(User.id == destination_client.user_id).first()

    origin_landline_clean = (payload.origin_landline_phone or "").strip() or (origin_client.landline_phone if origin_client else "") or ""
    origin_whatsapp_clean = payload.origin_whatsapp_phone.strip() or (origin_client.whatsapp_phone if origin_client else "") or ""
    origin_email_clean = payload.origin_email.strip() or (origin_user.email if origin_user else "") or ""
    origin_state_clean = payload.origin_state_code.strip().upper() or (origin_client.state_code if origin_client else "") or ""
    origin_municipality_clean = payload.origin_municipality_code.strip().upper() or (origin_client.municipality_code if origin_client else "") or ""
    origin_postal_clean = payload.origin_postal_code.strip() or (origin_client.postal_code if origin_client else "") or ""
    origin_colony_clean = payload.origin_colony_id.strip() or (origin_client.colony_id if origin_client else "") or ""
    origin_address_clean = payload.origin_address_line.strip() or (origin_client.address_line if origin_client else "") or ""

    destination_landline_clean = (payload.destination_landline_phone or "").strip() or (destination_client.landline_phone if destination_client else "") or ""
    destination_whatsapp_clean = payload.destination_whatsapp_phone.strip() or (destination_client.whatsapp_phone if destination_client else "") or ""
    destination_email_clean = payload.destination_email.strip() or (destination_user.email if destination_user else "") or ""
    destination_state_clean = payload.destination_state_code.strip().upper() or (destination_client.state_code if destination_client else "") or ""
    destination_municipality_clean = payload.destination_municipality_code.strip().upper() or (destination_client.municipality_code if destination_client else "") or ""
    destination_postal_clean = payload.destination_postal_code.strip() or (destination_client.postal_code if destination_client else "") or ""
    destination_colony_clean = payload.destination_colony_id.strip() or (destination_client.colony_id if destination_client else "") or ""
    destination_address_clean = payload.destination_address_line.strip() or (destination_client.address_line if destination_client else "") or ""

    required_fields = [
        (origin_whatsapp_clean, "Origin WhatsApp is required"),
        (origin_email_clean, "Origin email is required"),
        (origin_state_clean, "Origin state is required"),
        (origin_municipality_clean, "Origin municipality is required"),
        (origin_postal_clean, "Origin postal code is required"),
        (origin_colony_clean, "Origin colony is required"),
        (origin_address_clean, "Origin address is required"),
        (destination_whatsapp_clean, "Destination WhatsApp is required"),
        (destination_email_clean, "Destination email is required"),
        (destination_state_clean, "Destination state is required"),
        (destination_municipality_clean, "Destination municipality is required"),
        (destination_postal_clean, "Destination postal code is required"),
        (destination_colony_clean, "Destination colony is required"),
        (destination_address_clean, "Destination address is required"),
    ]
    for value, message in required_fields:
        if not value:
            raise HTTPException(status_code=400, detail=message)

    origin_geo_valid = (
        db.query(GeoColony)
        .filter(
            GeoColony.id == origin_colony_clean,
            GeoColony.state_code == origin_state_clean,
            GeoColony.municipality_code == origin_municipality_clean,
            GeoColony.postal_code == origin_postal_clean,
        )
        .first()
    )
    if not origin_geo_valid:
        raise HTTPException(status_code=400, detail="Origin geo combination is invalid")

    destination_geo_valid = (
        db.query(GeoColony)
        .filter(
            GeoColony.id == destination_colony_clean,
            GeoColony.state_code == destination_state_clean,
            GeoColony.municipality_code == destination_municipality_clean,
            GeoColony.postal_code == destination_postal_clean,
        )
        .first()
    )
    if not destination_geo_valid:
        raise HTTPException(status_code=400, detail="Destination geo combination is invalid")

    origin_coverage_station = _resolve_station_coverage(
        db,
        state_code=origin_state_clean,
        municipality_code=origin_municipality_clean,
        postal_code=origin_postal_clean,
        colony_id=origin_colony_clean,
    )
    if origin_coverage_station and origin_coverage_station.id != station.id:
        raise HTTPException(status_code=400, detail="Origin location is outside selected station coverage")

    destination_coverage_station = _resolve_station_coverage(
        db,
        state_code=destination_state_clean,
        municipality_code=destination_municipality_clean,
        postal_code=destination_postal_clean,
        colony_id=destination_colony_clean,
    )

    service_converted = False
    if _is_errand_service(service_kind):
        requires_package = quote_policy.service_converted or (
            destination_coverage_station and destination_coverage_station.id != station.id
        )
        if requires_package:
            package_service = (
                db.query(Service)
                .filter(Service.active.is_(True), Service.service_type == ServiceType.package)
                .order_by(Service.name.asc())
                .first()
            )
            if not package_service:
                raise HTTPException(status_code=400, detail="Errand crosses station coverage and requires an active package service")
            service = package_service
            service_kind = ServiceType.package.value
            service_converted = True
            if destination_coverage_station:
                destination_station = destination_coverage_station
        elif destination_coverage_station:
            destination_station = destination_coverage_station

    pricing_rule = (
        db.query(PricingRule)
        .filter(
            PricingRule.service_id == service.id,
            PricingRule.station_id == payload.station_id,
            PricingRule.active.is_(True),
        )
        .first()
    )
    if not pricing_rule:
        raise HTTPException(status_code=400, detail="No active pricing rule for service and station")

    if _is_errand_service(requested_service_kind):
        if requester_role_clean == "origin" and not origin_client:
            raise HTTPException(status_code=400, detail="Errand requester=origin requires origin client")
        if requester_role_clean == "destination" and not destination_client:
            raise HTTPException(status_code=400, detail="Errand requester=destination requires destination client")

    customer_name = payload.customer_name.strip()
    destination_name = payload.destination_name.strip()
    if origin_client:
        customer_name = origin_client.display_name
    if destination_client:
        destination_name = destination_client.display_name

    if _is_errand_service(requested_service_kind):
        if requester_role_clean == "destination" and destination_client:
            customer_name = destination_client.display_name
        elif requester_role_clean == "origin" and origin_client:
            customer_name = origin_client.display_name

    guide_code = f"M24-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    guide = Guide(
        guide_code=guide_code,
        customer_name=customer_name,
        destination_name=destination_name,
        service_type=service_kind,
        service_id=service.id,
        station_id=station.id,
        destination_station_id=destination_station.id,
        sale_amount=round(pricing_rule.price * policy_multiplier, 2),
        currency=pricing_rule.currency,
    )
    db.add(guide)
    db.flush()

    delivery = Delivery(
        guide_id=guide.id,
        stage=WorkflowStage.assigned,
        note=(
            f"requester_role:{requester_role_clean};"
            f"requested_service_type:{requested_service_kind};"
            f"service_converted:{'true' if service_converted else 'false'};"
            f"policy_notes:{' | '.join([item.replace(';', ',') for item in policy_notes])}"
        ),
    )
    db.add(delivery)

    party = GuideParty(
        guide_id=guide.id,
        origin_client_id=origin_client.id if origin_client else None,
        destination_client_id=destination_client.id if destination_client else None,
        origin_landline_phone=origin_landline_clean,
        origin_whatsapp_phone=origin_whatsapp_clean,
        origin_email=origin_email_clean,
        origin_state_code=origin_state_clean,
        origin_municipality_code=origin_municipality_clean,
        origin_postal_code=origin_postal_clean,
        origin_colony_id=origin_colony_clean,
        origin_address_line=origin_address_clean,
        destination_landline_phone=destination_landline_clean,
        destination_whatsapp_phone=destination_whatsapp_clean,
        destination_email=destination_email_clean,
        destination_state_code=destination_state_clean,
        destination_municipality_code=destination_municipality_clean,
        destination_postal_code=destination_postal_clean,
        destination_colony_id=destination_colony_clean,
        destination_address_line=destination_address_clean,
        origin_wants_invoice=(
            payload.origin_wants_invoice
            if payload.origin_wants_invoice is not None
            else (origin_client.wants_invoice if origin_client else False)
        ),
    )
    db.add(party)

    for leg in _build_route_legs(
        guide=guide,
        pricing_rule=pricing_rule,
        service_type=service_kind,
        station_id=station.id,
        destination_station_id=destination_station.id,
        use_station_handoff=payload.use_station_handoff,
        amount_multiplier=policy_multiplier,
    ):
        db.add(leg)

    db.commit()
    db.refresh(guide)
    return _to_guide_response(guide)


@router.get("/{guide_code}", response_model=GuideResponse)
def get_guide(
    guide_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> GuideResponse:
    normalized_code = guide_code.strip().upper()
    guide = db.query(Guide).filter(Guide.guide_code == normalized_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _to_guide_response(guide)


@router.get("/{guide_code}/deliveries", response_model=list[DeliveryResponse])
def get_guide_deliveries(
    guide_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[DeliveryResponse]:
    normalized_code = guide_code.strip().upper()
    guide = db.query(Guide).filter(Guide.guide_code == normalized_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    deliveries = db.query(Delivery).filter(Delivery.guide_id == guide.id).order_by(Delivery.created_at.asc()).all()
    return [_to_delivery_response(item) for item in deliveries]


@router.get("/{guide_code}/route-legs", response_model=list[RouteLegResponse])
def get_guide_route_legs(
    guide_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[RouteLegResponse]:
    normalized_code = guide_code.strip().upper()
    guide = db.query(Guide).filter(Guide.guide_code == normalized_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    route_legs = db.query(RouteLeg).filter(RouteLeg.guide_id == guide.id).order_by(RouteLeg.sequence.asc()).all()
    return [_to_route_leg_response(item, guide.guide_code) for item in route_legs]


@router.get("/route-legs/my", response_model=list[RouteLegResponse])
def get_my_route_legs(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.rider)),
) -> list[RouteLegResponse]:
    rider = db.query(Rider).filter(Rider.user_id == user.id, Rider.active.is_(True)).first()
    if not rider:
        return []
    if not _rider_is_operational(rider):
        return []

    rows = (
        db.query(RouteLeg, Guide)
        .join(Guide, Guide.id == RouteLeg.guide_id)
        .filter(RouteLeg.assigned_rider_id == rider.id)
        .order_by(RouteLeg.updated_at.desc())
        .limit(200)
        .all()
    )
    return [_to_route_leg_response(route_leg, guide.guide_code) for route_leg, guide in rows]


@router.patch("/route-legs/{route_leg_id}/assign", response_model=RouteLegResponse)
def assign_route_leg(
    route_leg_id: str,
    payload: RouteLegAssignRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.station, UserRole.rider)),
) -> RouteLegResponse:
    route_leg = db.query(RouteLeg).filter(RouteLeg.id == route_leg_id).first()
    if not route_leg:
        raise HTTPException(status_code=404, detail="Route leg not found")

    rider_profile = None
    if user_has_role(user, UserRole.rider):
        rider_profile = db.query(Rider).filter(Rider.user_id == user.id, Rider.active.is_(True)).first()
        if not rider_profile:
            raise HTTPException(status_code=403, detail="Rider profile not found for current user")
        if not _rider_is_operational(rider_profile):
            raise HTTPException(status_code=403, detail="Rider is not operational")

    if payload.rider_id:
        if user_has_role(user, UserRole.rider):
            raise HTTPException(status_code=403, detail="Rider cannot reassign route legs")
        rider = db.query(Rider).filter(Rider.id == payload.rider_id, Rider.active.is_(True)).first()
        if not rider:
            raise HTTPException(status_code=404, detail="Rider not found or inactive")
        if not _rider_is_operational(rider):
            raise HTTPException(status_code=400, detail="Rider is not available or not active")
        guide = db.query(Guide).filter(Guide.id == route_leg.guide_id).first()
        if guide and _is_errand_service(guide.service_type) and rider.station_id and guide.station_id and rider.station_id != guide.station_id:
            raise HTTPException(status_code=400, detail="Errand rider must belong to guide origin station")
        if guide and _is_errand_service(guide.service_type):
            legs = db.query(RouteLeg).filter(RouteLeg.guide_id == route_leg.guide_id).all()
            for leg_item in legs:
                leg_item.assigned_rider_id = rider.id
                if leg_item.status == "planned":
                    leg_item.status = "assigned"
        else:
            route_leg.assigned_rider_id = rider.id
            if route_leg.status == "planned":
                route_leg.status = "assigned"

    if payload.status:
        new_status = payload.status.strip().lower()
        if new_status not in VALID_ROUTE_LEG_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid route leg status")
        if user_has_role(user, UserRole.rider) and route_leg.assigned_rider_id != rider_profile.id:
            raise HTTPException(status_code=403, detail="Route leg is not assigned to current rider")
        _ensure_route_leg_transition(db, route_leg, new_status)
        route_leg.status = new_status

    route_leg.updated_at = datetime.now(timezone.utc)
    _sync_delivery_from_route_legs(db, route_leg.guide_id)
    db.commit()
    db.refresh(route_leg)
    guide = db.query(Guide).filter(Guide.id == route_leg.guide_id).first()
    return _to_route_leg_response(route_leg, guide.guide_code if guide else "")


@router.get("/route-legs/{route_leg_id}/suggest-riders", response_model=list[RouteLegRiderSuggestionResponse])
def suggest_riders_for_route_leg(
    route_leg_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles(UserRole.admin, UserRole.station)),
) -> list[RouteLegRiderSuggestionResponse]:
    route_leg = db.query(RouteLeg).filter(RouteLeg.id == route_leg_id).first()
    if not route_leg:
        raise HTTPException(status_code=404, detail="Route leg not found")
    guide = db.query(Guide).filter(Guide.id == route_leg.guide_id).first()
    if guide and _is_errand_service(guide.service_type):
        existing_rider_id = _assigned_rider_for_guide(db, route_leg.guide_id)
        if existing_rider_id:
            rider = db.query(Rider).filter(Rider.id == existing_rider_id, Rider.active.is_(True)).first()
            if rider and _rider_is_operational(rider):
                return [
                    RouteLegRiderSuggestionResponse(
                        rider_id=rider.id,
                        user_id=rider.user_id,
                        zone_id=rider.zone_id,
                        vehicle_type=rider.vehicle_type,
                        score=0,
                        reason="errand_unified_rider",
                    )
                ]
    return _suggest_riders_for_route_leg(db, route_leg)


@router.patch("/deliveries/{delivery_id}/stage", response_model=DeliveryResponse)
def update_stage(
    delivery_id: str,
    payload: DeliveryStageUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.rider)),
) -> DeliveryResponse:
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if user_has_role(user, UserRole.rider):
        rider_profile = db.query(Rider).filter(Rider.user_id == user.id, Rider.active.is_(True)).first()
        if not rider_profile:
            raise HTTPException(status_code=403, detail="Rider profile not found for current user")
        if not _rider_is_operational(rider_profile):
            raise HTTPException(status_code=403, detail="Rider is not operational")
        rider_leg = (
            db.query(RouteLeg.id)
            .filter(
                RouteLeg.guide_id == delivery.guide_id,
                RouteLeg.assigned_rider_id == rider_profile.id,
            )
            .first()
        )
        if not rider_leg:
            raise HTTPException(status_code=403, detail="Delivery is not assigned to current rider")

    route_legs = db.query(RouteLeg).filter(RouteLeg.guide_id == delivery.guide_id).order_by(RouteLeg.sequence.asc()).all()
    if route_legs:
        if payload.stage == WorkflowStage.delivered and not all(item.status == "completed" for item in route_legs):
            raise HTTPException(status_code=400, detail="Cannot mark delivered until all route legs are completed")

    if payload.stage == WorkflowStage.delivered and not (payload.has_evidence and payload.has_signature):
        raise HTTPException(status_code=400, detail="Delivered requires evidence and signature")

    delivery.stage = payload.stage
    delivery.note = payload.note
    delivery.has_evidence = payload.has_evidence
    delivery.has_signature = payload.has_signature
    if payload.stage == WorkflowStage.delivered and not delivery.delivered_at:
        delivery.delivered_at = datetime.now(timezone.utc)
    if payload.stage != WorkflowStage.delivered:
        delivery.delivered_at = None
    delivery.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(delivery)
    return _to_delivery_response(delivery)


@router.get("/deliveries/{delivery_id}", response_model=DeliveryResponse)
def get_delivery(
    delivery_id: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> DeliveryResponse:
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return _to_delivery_response(delivery)
