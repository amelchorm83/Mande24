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


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(SqlEnum(UserRole, name="user_role"), default=UserRole.client)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Guide(Base):
    __tablename__ = "guides"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    guide_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(150))
    destination_name: Mapped[str] = mapped_column(String(150))
    service_type: Mapped[str] = mapped_column(String(50), default="messaging")
    service_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("services.id"), nullable=True)
    station_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("stations.id"), nullable=True)
    sale_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="MXN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    deliveries: Mapped[list["Delivery"]] = relationship(back_populates="guide", cascade="all, delete-orphan")


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
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Rider(Base):
    __tablename__ = "riders"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    user_id: Mapped[str] = mapped_column(String(32), ForeignKey("users.id"), unique=True, index=True)
    zone_id: Mapped[str | None] = mapped_column(String(32), ForeignKey("zones.id"), nullable=True)
    vehicle_type: Mapped[str] = mapped_column(String(30), default="motorcycle")
    state: Mapped[RiderState] = mapped_column(SqlEnum(RiderState, name="rider_state"), default=RiderState.draft)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid4().hex)
    service_id: Mapped[str] = mapped_column(String(32), ForeignKey("services.id"), index=True)
    station_id: Mapped[str] = mapped_column(String(32), ForeignKey("stations.id"), index=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)
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
