from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import ContactLead
from app.db.session import get_db
from app.models.schemas import ContactLeadCreate, ContactLeadResponse

router = APIRouter(prefix="/public", tags=["public"])

ALLOWED_SERVICE_TYPES = {"express", "programada", "recurrente"}


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
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)

    return ContactLeadResponse(
        lead_id=lead.id,
        status="ok",
        message="Solicitud recibida. Nuestro equipo comercial te contactara pronto.",
    )
