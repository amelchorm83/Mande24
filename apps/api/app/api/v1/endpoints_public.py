import smtplib
from datetime import datetime
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit, resolve_client_identifier
from app.db.models import ContactLead, Delivery, Guide, OperationalSetting
from app.db.session import get_db
from app.models.schemas import (
    ContactLeadCreate,
    ContactLeadResponse,
    PublicQuoteRequest,
    PublicQuoteResponse,
    PublicTrackingResponse,
)
from app.services.national_lane import resolve_national_lane
from app.services.quote_policy import resolve_quote_policy

router = APIRouter(prefix="/public", tags=["public"])

ALLOWED_SERVICE_TYPES = {"express", "programada", "recurrente", "mandaditos", "paqueteria"}


def _to_float(raw: str | None, default: float) -> float:
    try:
        return float(str(raw or "").strip())
    except (TypeError, ValueError):
        return default


def _to_int(raw: str | None, default: int) -> int:
    try:
        return int(str(raw or "").strip())
    except (TypeError, ValueError):
        return default


def _send_contact_email_notification(lead: ContactLead) -> None:
    # Optional notification: if SMTP env vars are absent, skip silently.
    if not settings.smtp_host or not settings.smtp_to_email:
        return

    sender = settings.smtp_from_email or settings.smtp_user or "noreply@mande24.local"
    msg = EmailMessage()
    msg["Subject"] = f"[Mande24] Nuevo lead de contacto: {lead.full_name}"
    msg["From"] = sender
    msg["To"] = settings.smtp_to_email
    msg.set_content(
        "\n".join(
            [
                "Nuevo lead capturado desde el sitio web.",
                f"ID: {lead.id}",
                f"Nombre: {lead.full_name}",
                f"Empresa: {lead.company}",
                f"Email: {lead.email}",
                f"Telefono: {lead.phone}",
                f"Interes: {lead.service_interest}",
                f"Mensaje: {lead.message}",
            ]
        )
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_use_tls:
                smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        # Never fail user submission due to email infra issues.
        return


@router.post("/contact", response_model=ContactLeadResponse)
def create_contact_lead(payload: ContactLeadCreate, request: Request, db: Session = Depends(get_db)) -> ContactLeadResponse:
    identifier = resolve_client_identifier(request, extra=payload.email)
    enforce_rate_limit(
        "public:contact",
        identifier,
        limit=settings.public_contact_rate_limit,
        window_seconds=settings.public_rate_limit_window_seconds,
    )

    service_interest = payload.service_interest.strip().lower()
    if service_interest not in ALLOWED_SERVICE_TYPES:
        service_interest = "express"

    lead = ContactLead(
        full_name=payload.full_name.strip(),
        company=payload.company.strip(),
        email=payload.email.strip().lower(),
        phone=payload.phone.strip(),
        service_interest=service_interest,
        message=payload.message.strip(),
        status="new",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    _send_contact_email_notification(lead)

    return ContactLeadResponse(
        lead_id=lead.id,
        status="ok",
        message="Solicitud recibida. Nuestro equipo comercial te contactara pronto.",
    )


@router.post("/quote", response_model=PublicQuoteResponse)
def estimate_public_quote(payload: PublicQuoteRequest, request: Request, db: Session = Depends(get_db)) -> PublicQuoteResponse:
    identifier = resolve_client_identifier(request)
    enforce_rate_limit(
        "public:quote",
        identifier,
        limit=settings.public_quote_rate_limit,
        window_seconds=settings.public_rate_limit_window_seconds,
    )

    decision = resolve_quote_policy(
        db=db,
        requested_service_type=payload.service_type,
        distance_km=payload.distance_km,
        zone_type=payload.zone_type,
        rural_complexity=payload.rural_complexity,
    )
    lane_decision = resolve_national_lane(
        origin_state_code=payload.origin_state_code,
        destination_state_code=payload.destination_state_code,
        origin_zone_code=payload.origin_zone_code,
        destination_zone_code=payload.destination_zone_code,
        use_station_handoff=payload.use_station_handoff,
    )

    settings_map = {item.key: item.value for item in db.query(OperationalSetting).all()}
    base = _to_float(settings_map.get("quote_base_fare"), 49.0)
    per_km = _to_float(settings_map.get("quote_per_km"), 7.5)
    stop_extra_unit = _to_float(settings_map.get("quote_stop_extra"), 14.0)
    stop_extra = max(0, payload.stops - 1) * stop_extra_unit

    manual_service_multiplier = _to_float(
        settings_map.get(f"quote_manual_service_multiplier_{decision.applied_service_type}"),
        1.0,
    )
    distance_cost = payload.distance_km * per_km
    subtotal = (
        (base + distance_cost + stop_extra)
        * decision.zone_factor
        * decision.service_factor
        * decision.complexity_factor
        * manual_service_multiplier
        * lane_decision.lane_factor
    )

    decision.policy_notes.extend(lane_decision.notes)

    night_start = _to_int(settings_map.get("night_start_hour"), 22)
    night_end = _to_int(settings_map.get("night_end_hour"), 7)
    night_factor = _to_float(settings_map.get("night_surcharge_factor"), 1.15)

    now_hour = datetime.now().hour
    is_night = now_hour >= night_start or now_hour < night_end
    if is_night and night_factor > 0:
        subtotal *= night_factor
        decision.policy_notes.append(
            f"Tarifa nocturna aplicada por ventana {night_start}:00-{night_end}:00 (factor {night_factor:.2f})."
        )

    total = round(subtotal, 2)
    eta_per_km = _to_float(settings_map.get("quote_eta_minutes_per_km"), 5.0)
    eta_per_stop = _to_float(settings_map.get("quote_eta_minutes_per_stop"), 8.0)
    eta_floor = _to_int(settings_map.get("quote_eta_min_floor"), 25)
    eta_base = payload.distance_km * eta_per_km + payload.stops * eta_per_stop
    eta_base += decision.eta_extra_minutes
    eta_minutes = max(eta_floor, int(round(eta_base)))

    message = "Cotizacion referencial calculada con parametros operativos actuales."
    if decision.service_converted:
        message = "Mandadito convertido a paqueteria por politica de distancia maxima."

    return PublicQuoteResponse(
        status="ok",
        currency="MXN",
        total_estimate=total,
        eta_minutes=eta_minutes,
        requested_service_type=decision.requested_service_type,
        applied_service_type=decision.applied_service_type,
        service_converted=decision.service_converted,
        breakdown={
            "base": round(base, 2),
            "distance_cost": round(distance_cost, 2),
            "stops_extra": round(stop_extra, 2),
            "zone_factor": round(decision.zone_factor, 2),
            "service_factor": round(decision.service_factor, 2),
            "area_complexity_factor": round(decision.complexity_factor, 2),
            "manual_service_multiplier": round(manual_service_multiplier, 2),
            "national_lane_factor": round(lane_decision.lane_factor, 2),
        },
        policy_notes=decision.policy_notes,
        message=message,
    )


@router.get("/tracking/{guide_code}", response_model=PublicTrackingResponse)
def get_public_tracking(guide_code: str, request: Request, db: Session = Depends(get_db)) -> PublicTrackingResponse:
    identifier = resolve_client_identifier(request, extra=guide_code)
    enforce_rate_limit(
        "public:tracking",
        identifier,
        limit=settings.public_tracking_rate_limit,
        window_seconds=settings.public_rate_limit_window_seconds,
    )

    normalized_code = guide_code.strip().upper()
    guide = db.query(Guide).filter(Guide.guide_code == normalized_code).first()
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")

    latest_delivery = (
        db.query(Delivery)
        .filter(Delivery.guide_id == guide.id)
        .order_by(Delivery.updated_at.desc())
        .first()
    )
    if not latest_delivery:
        raise HTTPException(status_code=404, detail="Tracking data not found")

    return PublicTrackingResponse(
        guide_code=guide.guide_code,
        customer_name=guide.customer_name,
        destination_name=guide.destination_name,
        stage=latest_delivery.stage,
        updated_at=latest_delivery.updated_at,
        created_at=guide.created_at,
        sale_amount=guide.sale_amount,
        currency=guide.currency,
        has_evidence=latest_delivery.has_evidence,
        has_signature=latest_delivery.has_signature,
    )
