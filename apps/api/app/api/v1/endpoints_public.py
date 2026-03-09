import smtplib
from email.message import EmailMessage

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ContactLead
from app.db.session import get_db
from app.models.schemas import ContactLeadCreate, ContactLeadResponse

router = APIRouter(prefix="/public", tags=["public"])

ALLOWED_SERVICE_TYPES = {"express", "programada", "recurrente"}


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
