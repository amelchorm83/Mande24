from datetime import datetime

from pydantic import BaseModel, Field
from app.db.models import ClientKind, RiderState, ServiceType, UserRole, WorkflowStage


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=190)
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.client


class LoginRequest(BaseModel):
    email: str = Field(min_length=5, max_length=190)
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole


class ServiceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    service_type: ServiceType = ServiceType.messaging


class ServiceResponse(BaseModel):
    id: str
    name: str
    description: str | None
    service_type: ServiceType
    active: bool


class ZoneCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=30)


class ZoneResponse(BaseModel):
    id: str
    name: str
    code: str
    active: bool


class StationCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    zone_id: str
    landline_phone: str = Field(default="", max_length=40)
    whatsapp_phone: str = Field(default="", max_length=40)


class StationResponse(BaseModel):
    id: str
    name: str
    zone_id: str
    landline_phone: str
    whatsapp_phone: str
    active: bool


class RiderCreate(BaseModel):
    user_id: str
    zone_id: str | None = None
    vehicle_type: str = Field(default="motorcycle", min_length=2, max_length=30)
    landline_phone: str = Field(default="", max_length=40)
    whatsapp_phone: str = Field(default="", max_length=40)


class RiderResponse(BaseModel):
    id: str
    user_id: str
    zone_id: str | None
    vehicle_type: str
    landline_phone: str
    whatsapp_phone: str
    state: RiderState
    active: bool


class PricingRuleCreate(BaseModel):
    service_id: str
    station_id: str
    price: float = Field(gt=0)
    pickup_fee: float = Field(default=0.0, ge=0)
    delivery_fee: float = Field(default=0.0, ge=0)
    transfer_fee: float = Field(default=0.0, ge=0)
    station_fee: float = Field(default=0.0, ge=0)
    currency: str = Field(default="MXN", min_length=3, max_length=10)


class PricingRuleResponse(BaseModel):
    id: str
    service_id: str
    station_id: str
    price: float
    pickup_fee: float
    delivery_fee: float
    transfer_fee: float
    station_fee: float
    currency: str
    active: bool


class GuideCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    destination_name: str = Field(min_length=2, max_length=150)
    origin_client_id: str | None = None
    destination_client_id: str | None = None
    origin_landline_phone: str | None = Field(default=None, max_length=40)
    origin_whatsapp_phone: str = Field(min_length=3, max_length=40)
    origin_email: str = Field(min_length=5, max_length=190)
    origin_state_code: str = Field(min_length=2, max_length=10)
    origin_municipality_code: str = Field(min_length=2, max_length=20)
    origin_postal_code: str = Field(min_length=3, max_length=10)
    origin_colony_id: str = Field(min_length=1, max_length=64)
    origin_address_line: str = Field(min_length=2, max_length=255)
    destination_landline_phone: str | None = Field(default=None, max_length=40)
    destination_whatsapp_phone: str = Field(min_length=3, max_length=40)
    destination_email: str = Field(min_length=5, max_length=190)
    destination_state_code: str = Field(min_length=2, max_length=10)
    destination_municipality_code: str = Field(min_length=2, max_length=20)
    destination_postal_code: str = Field(min_length=3, max_length=10)
    destination_colony_id: str = Field(min_length=1, max_length=64)
    destination_address_line: str = Field(min_length=2, max_length=255)
    origin_wants_invoice: bool | None = None
    requester_role: str = Field(default="origin", pattern="^(origin|destination|external)$")
    service_id: str
    station_id: str
    destination_station_id: str | None = None
    use_station_handoff: bool = False


class GuideResponse(BaseModel):
    guide_code: str
    customer_name: str
    destination_name: str
    service_type: str
    service_id: str | None
    station_id: str | None
    destination_station_id: str | None
    sale_amount: float
    currency: str
    created_at: datetime


class RouteLegResponse(BaseModel):
    id: str
    guide_code: str
    sequence: int
    leg_type: str
    from_node_type: str
    to_node_type: str
    origin_station_id: str | None
    destination_station_id: str | None
    assigned_rider_id: str | None
    rider_fee_amount: float
    station_fee_amount: float
    currency: str
    status: str
    updated_at: datetime


class RouteLegAssignRequest(BaseModel):
    rider_id: str | None = None
    status: str | None = None


class RouteLegRiderSuggestionResponse(BaseModel):
    rider_id: str
    user_id: str
    zone_id: str | None
    vehicle_type: str
    score: int
    reason: str


class DeliveryStageUpdate(BaseModel):
    stage: WorkflowStage
    note: str | None = None
    has_evidence: bool = False
    has_signature: bool = False


class DeliveryResponse(BaseModel):
    delivery_id: str
    guide_code: str
    stage: WorkflowStage
    updated_at: datetime


class RiderWeeklyCommissionRow(BaseModel):
    rider_id: str
    delivery_count: int
    total_amount: float


class StationWeeklyCommissionRow(BaseModel):
    station_id: str
    sold_guide_count: int
    sold_guide_amount: float
    total_amount: float


class RiderWeeklyCommissionResponse(BaseModel):
    week_start: str
    week_end: str
    rows: list[RiderWeeklyCommissionRow]


class RiderLegTypeWeeklyCommissionRow(BaseModel):
    rider_id: str
    leg_type: str
    leg_count: int
    total_amount: float


class RiderLegTypeWeeklyCommissionResponse(BaseModel):
    week_start: str
    week_end: str
    rows: list[RiderLegTypeWeeklyCommissionRow]


class StationWeeklyCommissionResponse(BaseModel):
    week_start: str
    week_end: str
    rows: list[StationWeeklyCommissionRow]


class StationLegTypeWeeklyCommissionRow(BaseModel):
    station_id: str
    leg_type: str
    leg_count: int
    total_amount: float


class StationLegTypeWeeklyCommissionResponse(BaseModel):
    week_start: str
    week_end: str
    rows: list[StationLegTypeWeeklyCommissionRow]


class RiderCommissionHistoryRow(BaseModel):
    rider_id: str
    week_start: str
    delivery_count: int
    total_amount: float
    state: str


class StationCommissionHistoryRow(BaseModel):
    station_id: str
    week_start: str
    sold_guide_count: int
    sold_guide_amount: float
    total_amount: float
    state: str


class GeoStateResponse(BaseModel):
    code: str
    name: str


class GeoMunicipalityResponse(BaseModel):
    code: str
    state_code: str
    name: str


class GeoPostalCodeResponse(BaseModel):
    code: str
    municipality_code: str
    settlement: str


class GeoColonyResponse(BaseModel):
    id: str
    state_code: str
    municipality_code: str
    postal_code: str
    name: str
    settlement_type: str


class ClientProfileCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=150)
    client_kind: ClientKind = ClientKind.origin
    state_code: str = Field(min_length=2, max_length=10)
    municipality_code: str = Field(min_length=2, max_length=20)
    postal_code: str = Field(min_length=3, max_length=10)
    colony_id: str | None = Field(default=None, max_length=64)
    address_line: str = Field(default="", max_length=255)
    landline_phone: str = Field(default="", max_length=40)
    whatsapp_phone: str = Field(default="", max_length=40)
    wants_invoice: bool = False
    create_portal_access: bool = False
    email: str | None = None
    password: str | None = None


class ClientProfileResponse(BaseModel):
    id: str
    user_id: str | None
    display_name: str
    client_kind: ClientKind
    state_code: str
    municipality_code: str
    postal_code: str
    colony_id: str | None
    colony_name: str | None
    address_line: str
    landline_phone: str
    whatsapp_phone: str
    wants_invoice: bool
    active: bool


class ShipmentGuideSummary(BaseModel):
    guide_code: str
    customer_name: str
    destination_name: str
    sale_amount: float
    currency: str
    created_at: datetime


class MyShipmentsResponse(BaseModel):
    sent: list[ShipmentGuideSummary]
    received: list[ShipmentGuideSummary]


class ContactLeadCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    company: str = Field(default="", max_length=150)
    email: str = Field(min_length=5, max_length=190)
    phone: str = Field(default="", max_length=40)
    service_interest: str = Field(default="express", max_length=40)
    message: str = Field(min_length=10, max_length=2000)


class ContactLeadResponse(BaseModel):
    lead_id: str
    status: str
    message: str


class PublicQuoteRequest(BaseModel):
    distance_km: float = Field(gt=0, le=500)
    stops: int = Field(ge=1, le=20)
    zone_type: str = Field(default="urbana", max_length=40)
    service_type: str = Field(default="programado", max_length=40)


class PublicQuoteResponse(BaseModel):
    status: str
    currency: str
    total_estimate: float
    eta_minutes: int
    breakdown: dict[str, float]
    message: str


class PublicTrackingResponse(BaseModel):
    guide_code: str
    customer_name: str
    destination_name: str
    stage: WorkflowStage
    updated_at: datetime
    created_at: datetime
    sale_amount: float
    currency: str
    has_evidence: bool
    has_signature: bool
    note: str | None
