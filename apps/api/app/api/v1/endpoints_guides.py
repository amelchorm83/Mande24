from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.models import ClientProfile, Delivery, Guide, GuideParty, PricingRule, Rider, RouteLeg, Service, ServiceType, Station, WorkflowStage
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


def _to_guide_response(guide: Guide) -> GuideResponse:
    return GuideResponse(
        guide_code=guide.guide_code,
        customer_name=guide.customer_name,
        destination_name=guide.destination_name,
        service_type=guide.service_type,
        service_id=guide.service_id,
        station_id=guide.station_id,
        destination_station_id=guide.destination_station_id,
        sale_amount=guide.sale_amount,
        currency=guide.currency,
        created_at=guide.created_at,
    )


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
) -> list[RouteLeg]:
    route_legs: list[RouteLeg] = []
    service_kind = _service_type_value(service_type)

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
                rider_fee_amount=pricing_rule.pickup_fee,
                station_fee_amount=pricing_rule.station_fee,
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
                    rider_fee_amount=pricing_rule.transfer_fee,
                    station_fee_amount=pricing_rule.station_fee,
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
                rider_fee_amount=pricing_rule.delivery_fee,
                station_fee_amount=pricing_rule.station_fee,
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
                rider_fee_amount=pricing_rule.pickup_fee,
                station_fee_amount=pricing_rule.station_fee,
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
                rider_fee_amount=pricing_rule.delivery_fee,
                station_fee_amount=pricing_rule.station_fee,
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
                rider_fee_amount=pricing_rule.pickup_fee + pricing_rule.delivery_fee,
                station_fee_amount=pricing_rule.station_fee,
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
    delivery.stage = stage
    if stage == WorkflowStage.delivered and not delivery.delivered_at:
        delivery.delivered_at = datetime.now(timezone.utc)
    if stage != WorkflowStage.delivered:
        delivery.delivered_at = None
    if stage == WorkflowStage.delivered:
        delivery.has_evidence = True
        delivery.has_signature = True
    delivery.updated_at = datetime.now(timezone.utc)


def _suggest_riders_for_route_leg(db: Session, route_leg: RouteLeg) -> list[RouteLegRiderSuggestionResponse]:
    station_id = route_leg.origin_station_id or route_leg.destination_station_id
    station_zone_id = None
    if station_id:
        station = db.query(Station).filter(Station.id == station_id, Station.active.is_(True)).first()
        if station:
            station_zone_id = station.zone_id

    riders = db.query(Rider).filter(Rider.active.is_(True)).all()
    if not riders:
        return []

    rows: list[RouteLegRiderSuggestionResponse] = []
    for rider in riders:
        same_zone = bool(station_zone_id and rider.zone_id == station_zone_id)
        rows.append(
            RouteLegRiderSuggestionResponse(
                rider_id=rider.id,
                user_id=rider.user_id,
                zone_id=rider.zone_id,
                vehicle_type=rider.vehicle_type,
                score=0 if same_zone else 10,
                reason="same_zone" if same_zone else "fallback_active",
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

    pricing_rule = (
        db.query(PricingRule)
        .filter(
            PricingRule.service_id == payload.service_id,
            PricingRule.station_id == payload.station_id,
            PricingRule.active.is_(True),
        )
        .first()
    )
    if not pricing_rule:
        raise HTTPException(status_code=400, detail="No active pricing rule for service and station")

    service_kind = _service_type_value(service.service_type)
    requester_role_clean = _sanitize_requester_role(payload.requester_role)

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

    if _is_errand_service(service_kind):
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

    if _is_errand_service(service_kind):
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
        sale_amount=pricing_rule.price,
        currency=pricing_rule.currency,
    )
    db.add(guide)
    db.flush()

    delivery = Delivery(
        guide_id=guide.id,
        stage=WorkflowStage.assigned,
        note=(f"requester_role:{requester_role_clean}" if _is_errand_service(service_kind) else None),
    )
    db.add(delivery)

    party = GuideParty(
        guide_id=guide.id,
        origin_client_id=origin_client.id if origin_client else None,
        destination_client_id=destination_client.id if destination_client else None,
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
    guide = db.query(Guide).filter(Guide.guide_code == guide_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return _to_guide_response(guide)


@router.get("/{guide_code}/deliveries", response_model=list[DeliveryResponse])
def get_guide_deliveries(
    guide_code: str,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[DeliveryResponse]:
    guide = db.query(Guide).filter(Guide.guide_code == guide_code).first()
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
    guide = db.query(Guide).filter(Guide.guide_code == guide_code).first()
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
    if user.role == UserRole.rider:
        rider_profile = db.query(Rider).filter(Rider.user_id == user.id, Rider.active.is_(True)).first()
        if not rider_profile:
            raise HTTPException(status_code=403, detail="Rider profile not found for current user")

    if payload.rider_id:
        if user.role == UserRole.rider:
            raise HTTPException(status_code=403, detail="Rider cannot reassign route legs")
        rider = db.query(Rider).filter(Rider.id == payload.rider_id, Rider.active.is_(True)).first()
        if not rider:
            raise HTTPException(status_code=404, detail="Rider not found or inactive")
        guide = db.query(Guide).filter(Guide.id == route_leg.guide_id).first()
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
        if user.role == UserRole.rider and route_leg.assigned_rider_id != rider_profile.id:
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
            if rider:
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
    _user: User = Depends(require_roles(UserRole.admin, UserRole.rider)),
) -> DeliveryResponse:
    delivery = db.query(Delivery).filter(Delivery.id == delivery_id).first()
    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

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
