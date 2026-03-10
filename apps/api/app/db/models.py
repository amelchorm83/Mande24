from datetime import date, datetime, timezone
from enum import Enum
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WorkflowStage(str, Enum):
    assigned = "assigned"
    picked_up = "picked_up"
    in_transit = "in_transit"
    at_station = "at_station"
    out_for_delivery = "out_for_delivery"
    delivered = "delivered"
    failed = "failed"


class UserRole(str, Enum):
    admin = "admin"
    station = "station"
    rider = "rider"
    client = "client"


class ServiceType(str, Enum):
    messaging = "messaging"
    package = "package"
    errand = "errand"


class RiderState(str, Enum):
    draft = "draft"
    approved = "approved"
    rejected = "rejected"


class ClientKind(str, Enum):
    origin = "origin"
    destination = "destination"
    both = "both"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"), default=UserRole.client)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class UserRoleAudit(Base):
    __tablename__ = "user_role_audits"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    old_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"))
    new_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"))
    changed_by_role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"), default=UserRole.admin)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True)
    changed_by_email: Mapped[str | None] = mapped_column(String(190), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guide_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    destination_name: Mapped[str] = mapped_column(String(150))
    service_type: Mapped[str] = mapped_column(String(50), default="messaging")
    service_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("services.id"), nullable=True)
    station_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("stations.id"), nullable=True)
    destination_station_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("stations.id"), nullable=True)
    sale_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="MXN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="guide", cascade="all, delete-orphan")
    parties: Mapped[list["GuideParty"]] = relationship(back_populates="guide", cascade="all, delete-orphan")
    route_legs: Mapped[list["RouteLeg"]] = relationship(back_populates="guide", cascade="all, delete-orphan")


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guide_id: Mapped[str] = mapped_column(String(32), ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    stage: Mapped[WorkflowStage] = mapped_column(
        SqlEnum(WorkflowStage, name="workflow_stage"), default=WorkflowStage.assigned
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    has_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    has_signature: Mapped[bool] = mapped_column(Boolean, default=False)
    rider_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("riders.id"), nullable=True, index=True)
    commission_amount: Mapped[float] = mapped_column(Float, default=0.0)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    guide: Mapped[Guide] = relationship(back_populates="deliveries")


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    service_type: Mapped[ServiceType] = mapped_column(
        SqlEnum(ServiceType, name="service_type"),
        default=ServiceType.messaging,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Zone(Base):
    __tablename__ = "zones"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    name: Mapped[str] = mapped_column(String(120))
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Station(Base):
    __tablename__ = "stations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    zone_id: Mapped[str] = mapped_column(String(32), ForeignKey("zones.id"), index=True)
    landline_phone: Mapped[str] = mapped_column(String(40), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(40), default="")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), unique=True, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("zones.id"), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(30), default="motorcycle")
    landline_phone: Mapped[str] = mapped_column(String(40), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(40), default="")
    state: Mapped[RiderState] = mapped_column(SqlEnum(RiderState, name="rider_state"), default=RiderState.draft)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    service_id: Mapped[str] = mapped_column(String(32), ForeignKey("services.id"), index=True)
    station_id: Mapped[str] = mapped_column(String(32), ForeignKey("stations.id"), index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    pickup_fee: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_fee: Mapped[float] = mapped_column(Float, default=0.0)
    transfer_fee: Mapped[float] = mapped_column(Float, default=0.0)
    station_fee: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="MXN")
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class RiderCommission(Base):
    __tablename__ = "rider_commissions"
    __table_args__ = (UniqueConstraint("rider_id", "week_start", name="uq_rider_commission_week"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    rider_id: Mapped[str] = mapped_column(String(32), ForeignKey("riders.id"), index=True)
    week_start: Mapped[date] = mapped_column()
    delivery_count: Mapped[int] = mapped_column(default=0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(20), default="draft")


class StationCommission(Base):
    __tablename__ = "station_commissions"
    __table_args__ = (UniqueConstraint("station_id", "week_start", name="uq_station_commission_week"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    station_id: Mapped[str] = mapped_column(String(32), ForeignKey("stations.id"), index=True)
    week_start: Mapped[date] = mapped_column()
    sold_guide_count: Mapped[int] = mapped_column(default=0)
    sold_guide_amount: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    state: Mapped[str] = mapped_column(String(20), default="draft")


class GeoState(Base):
    __tablename__ = "geo_states"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)


class GeoMunicipality(Base):
    __tablename__ = "geo_municipalities"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    state_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_states.code"), index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)


class GeoPostalCode(Base):
    __tablename__ = "geo_postal_codes"

    code: Mapped[str] = mapped_column(String(10), primary_key=True)
    municipality_code: Mapped[str] = mapped_column(String(20), ForeignKey("geo_municipalities.code"), index=True)
    settlement: Mapped[str] = mapped_column(String(150), default="")


class GeoColony(Base):
    __tablename__ = "geo_colonies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    state_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_states.code"), index=True)
    municipality_code: Mapped[str] = mapped_column(String(20), ForeignKey("geo_municipalities.code"), index=True)
    postal_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_postal_codes.code"), index=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    settlement_type: Mapped[str] = mapped_column(String(60), default="")
    sepomex_code: Mapped[str] = mapped_column(String(20), default="")


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("users.id"), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(150), index=True)
    client_kind: Mapped[ClientKind] = mapped_column(SqlEnum(ClientKind, name="client_kind"), default=ClientKind.origin)
    state_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_states.code"), index=True)
    municipality_code: Mapped[str] = mapped_column(String(20), ForeignKey("geo_municipalities.code"), index=True)
    postal_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_postal_codes.code"), index=True)
    colony_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("geo_colonies.id"), nullable=True, index=True)
    address_line: Mapped[str] = mapped_column(String(255), default="")
    landline_phone: Mapped[str] = mapped_column(String(40), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(40), default="")
    wants_invoice: Mapped[bool] = mapped_column(Boolean, default=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class GuideParty(Base):
    __tablename__ = "guide_parties"
    __table_args__ = (UniqueConstraint("guide_id", name="uq_guide_parties_guide"),)

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guide_id: Mapped[str] = mapped_column(String(32), ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    origin_client_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("client_profiles.id"), nullable=True, index=True)
    destination_client_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("client_profiles.id"), nullable=True, index=True)
    origin_wants_invoice: Mapped[bool] = mapped_column(Boolean, default=False)

    guide: Mapped[Guide] = relationship(back_populates="parties")


class RouteLeg(Base):
    __tablename__ = "route_legs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guide_id: Mapped[str] = mapped_column(String(32), ForeignKey("guides.id", ondelete="CASCADE"), index=True)
    sequence: Mapped[int] = mapped_column(default=1)
    leg_type: Mapped[str] = mapped_column(String(40), default="pickup_to_station")
    from_node_type: Mapped[str] = mapped_column(String(40), default="client_origin")
    to_node_type: Mapped[str] = mapped_column(String(40), default="station")
    origin_station_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("stations.id"), nullable=True, index=True)
    destination_station_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("stations.id"), nullable=True, index=True)
    assigned_rider_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("riders.id"), nullable=True, index=True)
    rider_fee_amount: Mapped[float] = mapped_column(Float, default=0.0)
    station_fee_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="MXN")
    status: Mapped[str] = mapped_column(String(20), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    guide: Mapped[Guide] = relationship(back_populates="route_legs")


class ZoneGeoRule(Base):
    __tablename__ = "zone_geo_rules"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    zone_id: Mapped[str] = mapped_column(String(32), ForeignKey("zones.id", ondelete="CASCADE"), index=True)
    state_code: Mapped[str] = mapped_column(String(10), ForeignKey("geo_states.code"), index=True)
    municipality_code: Mapped[str | None] = mapped_column(String(20), ForeignKey("geo_municipalities.code"), nullable=True, index=True)
    postal_code: Mapped[str | None] = mapped_column(String(10), ForeignKey("geo_postal_codes.code"), nullable=True, index=True)
    colony_id: Mapped[str | None] = mapped_column(String(64), ForeignKey("geo_colonies.id"), nullable=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class GeoCatalogSync(Base):
    __tablename__ = "geo_catalog_sync"

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(255), default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ContactLead(Base):
    __tablename__ = "contact_leads"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    full_name: Mapped[str] = mapped_column(String(150), index=True)
    company: Mapped[str] = mapped_column(String(150), default="")
    email: Mapped[str] = mapped_column(String(190), index=True)
    phone: Mapped[str] = mapped_column(String(40), default="")
    service_interest: Mapped[str] = mapped_column(String(40), default="express")
    message: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(40), default="web_contact")
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
