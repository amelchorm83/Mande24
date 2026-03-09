from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.core.security import hash_password
from app.db.geo_seed import seed_geo_catalogs
from app.db.sepomex_sync import sync_sepomex_catalog
from app.db.models import (
    ClientKind,
    GeoColony,
    ClientProfile,
    GeoMunicipality,
    GeoPostalCode,
    GeoState,
    Guide,
    GuideParty,
    User,
    UserRole,
)
from app.db.session import get_db
from app.models.schemas import (
    GeoColonyResponse,
    ClientProfileCreate,
    ClientProfileResponse,
    GeoMunicipalityResponse,
    GeoPostalCodeResponse,
    GeoStateResponse,
    MyShipmentsResponse,
    ShipmentGuideSummary,
)

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/geo/states", response_model=list[GeoStateResponse])
def list_geo_states(db: Session = Depends(get_db), _user: User = Depends(get_current_user)) -> list[GeoStateResponse]:
    try:
        sync_sepomex_catalog(db)
    except Exception:
        seed_geo_catalogs(db)
    rows = db.query(GeoState).order_by(GeoState.name.asc()).all()
    return [GeoStateResponse(code=item.code, name=item.name) for item in rows]


@router.get("/geo/municipalities", response_model=list[GeoMunicipalityResponse])
def list_geo_municipalities(
    state_code: str = Query(..., min_length=2, max_length=10),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[GeoMunicipalityResponse]:
    rows = (
        db.query(GeoMunicipality)
        .filter(GeoMunicipality.state_code == state_code.strip().upper())
        .order_by(GeoMunicipality.name.asc())
        .all()
    )
    return [GeoMunicipalityResponse(code=item.code, state_code=item.state_code, name=item.name) for item in rows]


@router.get("/geo/postal-codes", response_model=list[GeoPostalCodeResponse])
def list_geo_postal_codes(
    municipality_code: str = Query(..., min_length=2, max_length=20),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[GeoPostalCodeResponse]:
    rows = (
        db.query(GeoPostalCode)
        .filter(GeoPostalCode.municipality_code == municipality_code.strip().upper())
        .order_by(GeoPostalCode.code.asc())
        .all()
    )
    return [
        GeoPostalCodeResponse(code=item.code, municipality_code=item.municipality_code, settlement=item.settlement)
        for item in rows
    ]


@router.get("/geo/colonies", response_model=list[GeoColonyResponse])
def list_geo_colonies(
    state_code: str = Query(..., min_length=2, max_length=10),
    municipality_code: str = Query(..., min_length=2, max_length=20),
    postal_code: str = Query(..., min_length=3, max_length=10),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[GeoColonyResponse]:
    rows = (
        db.query(GeoColony)
        .filter(
            GeoColony.state_code == state_code.strip().upper(),
            GeoColony.municipality_code == municipality_code.strip().upper(),
            GeoColony.postal_code == postal_code.strip(),
        )
        .order_by(GeoColony.name.asc())
        .all()
    )
    return [
        GeoColonyResponse(
            id=item.id,
            state_code=item.state_code,
            municipality_code=item.municipality_code,
            postal_code=item.postal_code,
            name=item.name,
            settlement_type=item.settlement_type,
        )
        for item in rows
    ]


@router.post("/profiles", response_model=ClientProfileResponse)
def create_client_profile(
    payload: ClientProfileCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.admin, UserRole.station, UserRole.client)),
) -> ClientProfileResponse:
    state = db.query(GeoState).filter(GeoState.code == payload.state_code.strip().upper()).first()
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="State not found")

    municipality = (
        db.query(GeoMunicipality)
        .filter(
            GeoMunicipality.code == payload.municipality_code.strip().upper(),
            GeoMunicipality.state_code == state.code,
        )
        .first()
    )
    if not municipality:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Municipality not found")

    postal_code = (
        db.query(GeoPostalCode)
        .filter(
            GeoPostalCode.code == payload.postal_code.strip(),
            GeoPostalCode.municipality_code == municipality.code,
        )
        .first()
    )
    if not postal_code:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Postal code not found")

    colony = None
    if payload.colony_id:
        colony = (
            db.query(GeoColony)
            .filter(
                GeoColony.id == payload.colony_id.strip(),
                GeoColony.state_code == state.code,
                GeoColony.municipality_code == municipality.code,
                GeoColony.postal_code == postal_code.code,
            )
            .first()
        )
        if not colony:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Colony not found")

    target_user_id: str | None = None
    if payload.create_portal_access:
        if not payload.email or not payload.password:
            raise HTTPException(status_code=400, detail="Email and password are required for portal access")
        email = payload.email.strip().lower()
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            target_user_id = existing_user.id
        else:
            created_user = User(
                email=email,
                full_name=payload.display_name.strip(),
                password_hash=hash_password(payload.password),
                role=UserRole.client,
                is_active=True,
            )
            db.add(created_user)
            db.flush()
            target_user_id = created_user.id
    elif user.role == UserRole.client:
        target_user_id = user.id

    profile = ClientProfile(
        user_id=target_user_id,
        display_name=payload.display_name.strip(),
        client_kind=payload.client_kind,
        state_code=state.code,
        municipality_code=municipality.code,
        postal_code=postal_code.code,
        colony_id=colony.id if colony else None,
        address_line=payload.address_line.strip(),
        wants_invoice=payload.wants_invoice,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return ClientProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        client_kind=profile.client_kind,
        state_code=profile.state_code,
        municipality_code=profile.municipality_code,
        postal_code=profile.postal_code,
        colony_id=profile.colony_id,
        colony_name=colony.name if colony else None,
        address_line=profile.address_line,
        wants_invoice=profile.wants_invoice,
        active=profile.active,
    )


@router.get("/profiles", response_model=list[ClientProfileResponse])
def list_client_profiles(
    client_kind: ClientKind | None = None,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[ClientProfileResponse]:
    query = db.query(ClientProfile).filter(ClientProfile.active.is_(True))
    if client_kind:
        if client_kind == ClientKind.origin:
            query = query.filter(ClientProfile.client_kind.in_([ClientKind.origin, ClientKind.both]))
        elif client_kind == ClientKind.destination:
            query = query.filter(ClientProfile.client_kind.in_([ClientKind.destination, ClientKind.both]))
        else:
            query = query.filter(ClientProfile.client_kind == ClientKind.both)

    rows = query.order_by(ClientProfile.display_name.asc()).all()
    colony_ids = [item.colony_id for item in rows if item.colony_id]
    colonies = {}
    if colony_ids:
        for item in db.query(GeoColony).filter(GeoColony.id.in_(colony_ids)).all():
            colonies[item.id] = item.name
    return [
        ClientProfileResponse(
            id=item.id,
            user_id=item.user_id,
            display_name=item.display_name,
            client_kind=item.client_kind,
            state_code=item.state_code,
            municipality_code=item.municipality_code,
            postal_code=item.postal_code,
            colony_id=item.colony_id,
            colony_name=colonies.get(item.colony_id) if item.colony_id else None,
            address_line=item.address_line,
            wants_invoice=item.wants_invoice,
            active=item.active,
        )
        for item in rows
    ]


@router.get("/shipments/my", response_model=MyShipmentsResponse)
def my_shipments(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> MyShipmentsResponse:
    profile_ids = [item.id for item in db.query(ClientProfile).filter(ClientProfile.user_id == user.id).all()]
    if not profile_ids:
        return MyShipmentsResponse(sent=[], received=[])

    sent_rows = (
        db.query(Guide)
        .join(GuideParty, GuideParty.guide_id == Guide.id)
        .filter(GuideParty.origin_client_id.in_(profile_ids))
        .order_by(Guide.created_at.desc())
        .limit(200)
        .all()
    )
    received_rows = (
        db.query(Guide)
        .join(GuideParty, GuideParty.guide_id == Guide.id)
        .filter(GuideParty.destination_client_id.in_(profile_ids))
        .order_by(Guide.created_at.desc())
        .limit(200)
        .all()
    )

    sent = [
        ShipmentGuideSummary(
            guide_code=item.guide_code,
            customer_name=item.customer_name,
            destination_name=item.destination_name,
            sale_amount=item.sale_amount,
            currency=item.currency,
            created_at=item.created_at,
        )
        for item in sent_rows
    ]
    received = [
        ShipmentGuideSummary(
            guide_code=item.guide_code,
            customer_name=item.customer_name,
            destination_name=item.destination_name,
            sale_amount=item.sale_amount,
            currency=item.currency,
            created_at=item.created_at,
        )
        for item in received_rows
    ]
    return MyShipmentsResponse(sent=sent, received=received)
