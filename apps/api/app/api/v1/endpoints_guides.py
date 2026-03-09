from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.db.models import ClientProfile, Delivery, Guide, GuideParty, PricingRule, Service, Station, WorkflowStage
from app.db.models import User, UserRole
from app.db.session import get_db
from app.models.schemas import DeliveryResponse, DeliveryStageUpdate, GuideCreate, GuideResponse

router = APIRouter(prefix="/guides", tags=["guides"])


def _to_guide_response(guide: Guide) -> GuideResponse:
    return GuideResponse(
        guide_code=guide.guide_code,
        customer_name=guide.customer_name,
        destination_name=guide.destination_name,
        service_type=guide.service_type,
        service_id=guide.service_id,
        station_id=guide.station_id,
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

    customer_name = payload.customer_name.strip()
    destination_name = payload.destination_name.strip()
    if origin_client:
        customer_name = origin_client.display_name
    if destination_client:
        destination_name = destination_client.display_name

    guide_code = f"M24-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid4().hex[:6].upper()}"
    guide = Guide(
        guide_code=guide_code,
        customer_name=customer_name,
        destination_name=destination_name,
        service_type=service.service_type.value,
        service_id=service.id,
        station_id=station.id,
        sale_amount=pricing_rule.price,
        currency=pricing_rule.currency,
    )
    db.add(guide)
    db.flush()

    delivery = Delivery(
        guide_id=guide.id,
        stage=WorkflowStage.assigned,
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
