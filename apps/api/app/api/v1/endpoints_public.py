import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ContactLead, Delivery, Guide
from app.db.session import get_db
from app.models.schemas import (
    ContactLeadCreate,
    ContactLeadResponse,
    PublicQuoteRequest,
    PublicQuoteResponse,
    PublicTrackingResponse,
)

router = APIRouter(prefix="/public", tags=["public"])

ALLOWED_SERVICE_TYPES = {"express", "programada", "recurrente", "mandaditos"}
ALLOWED_QUOTE_ZONE_TYPES = {"urbana", "metropolitana", "intermunicipal"}

ZONE_FACTORS = {
    "urbana": 1.0,
    "metropolitana": 1.18,
    "intermunicipal": 1.35,
}

SERVICE_FACTORS = {
    "programado": 1.0,
    "express": 1.3,
    "recurrente": 0.9,
    "mandaditos": 1.12,
}


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
def create_contact_lead(payload: ContactLeadCreate, db: Session = Depends(get_db)) -> ContactLeadResponse:
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
def estimate_public_quote(payload: PublicQuoteRequest) -> PublicQuoteResponse:
    zone_type = payload.zone_type.strip().lower()
    service_type = payload.service_type.strip().lower()

    if zone_type not in ALLOWED_QUOTE_ZONE_TYPES:
        zone_type = "urbana"
    if service_type not in SERVICE_FACTORS:
        service_type = "programado"

    base = 49.0
    per_km = 7.5
    stop_extra = max(0, payload.stops - 1) * 14.0
    distance_cost = payload.distance_km * per_km
    subtotal = (base + distance_cost + stop_extra) * ZONE_FACTORS[zone_type] * SERVICE_FACTORS[service_type]
    total = round(subtotal, 2)
    eta_minutes = max(25, int(round(payload.distance_km * 5 + payload.stops * 8)))

    return PublicQuoteResponse(
        status="ok",
        currency="MXN",
        total_estimate=total,
        eta_minutes=eta_minutes,
        breakdown={
            "base": round(base, 2),
            "distance_cost": round(distance_cost, 2),
            "stops_extra": round(stop_extra, 2),
            "zone_factor": round(ZONE_FACTORS[zone_type], 2),
            "service_factor": round(SERVICE_FACTORS[service_type], 2),
        },
        message="Cotizacion referencial calculada con parametros operativos actuales.",
    )


@router.get("/tracking/{guide_code}", response_model=PublicTrackingResponse)
def get_public_tracking(guide_code: str, db: Session = Depends(get_db)) -> PublicTrackingResponse:
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
        note=latest_delivery.note,
    )
