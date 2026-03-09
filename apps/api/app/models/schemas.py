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


class StationResponse(BaseModel):
    id: str
    name: str
    zone_id: str
    active: bool


class RiderCreate(BaseModel):
    user_id: str
    zone_id: str | None = None
    vehicle_type: str = Field(default="motorcycle", min_length=2, max_length=30)


class RiderResponse(BaseModel):
    id: str
    user_id: str
    zone_id: str | None
    vehicle_type: str
    state: RiderState
    active: bool


class PricingRuleCreate(BaseModel):
    service_id: str
    station_id: str
    price: float = Field(gt=0)
    currency: str = Field(default="MXN", min_length=3, max_length=10)


class PricingRuleResponse(BaseModel):
    id: str
    service_id: str
    station_id: str
    price: float
    currency: str
    active: bool


class GuideCreate(BaseModel):
    customer_name: str = Field(min_length=2, max_length=150)
    destination_name: str = Field(min_length=2, max_length=150)
    origin_client_id: str | None = None
    destination_client_id: str | None = None
    origin_wants_invoice: bool | None = None
    service_id: str
    station_id: str


class GuideResponse(BaseModel):
    guide_code: str
    customer_name: str
    destination_name: str
    service_type: str
    service_id: str | None
    station_id: str | None
    sale_amount: float
    currency: str
    created_at: datetime


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


class StationWeeklyCommissionResponse(BaseModel):
    week_start: str
    week_end: str
    rows: list[StationWeeklyCommissionRow]


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
