"""create catalogs and guide links

Revision ID: 20260308_0003
Revises: 20260308_0002
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0003"
down_revision = "20260308_0002"
branch_labels = None
depends_on = None


service_type_enum = sa.Enum("messaging", "package", "errand", name="service_type")
rider_state_enum = sa.Enum("draft", "approved", "rejected", name="rider_state")


def upgrade() -> None:
    bind = op.get_bind()
    service_type_enum.create(bind, checkfirst=True)
    rider_state_enum.create(bind, checkfirst=True)

    op.create_table(
        "services",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("service_type", service_type_enum, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "zones",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_zones_code"), "zones", ["code"], unique=False)

    op.create_table(
        "stations",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("zone_id", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_stations_zone_id"), "stations", ["zone_id"], unique=False)

    op.create_table(
        "riders",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("zone_id", sa.String(length=32), nullable=True),
        sa.Column("vehicle_type", sa.String(length=30), nullable=False),
        sa.Column("state", rider_state_enum, nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_riders_user_id"), "riders", ["user_id"], unique=False)

    op.create_table(
        "pricing_rules",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("service_id", sa.String(length=32), nullable=False),
        sa.Column("station_id", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"]),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_pricing_rules_service_id"), "pricing_rules", ["service_id"], unique=False)
    op.create_index(op.f("ix_pricing_rules_station_id"), "pricing_rules", ["station_id"], unique=False)

    op.add_column("guides", sa.Column("service_id", sa.String(length=32), nullable=True))
    op.add_column("guides", sa.Column("station_id", sa.String(length=32), nullable=True))
    op.create_foreign_key("fk_guides_service_id", "guides", "services", ["service_id"], ["id"])
    op.create_foreign_key("fk_guides_station_id", "guides", "stations", ["station_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_guides_station_id", "guides", type_="foreignkey")
    op.drop_constraint("fk_guides_service_id", "guides", type_="foreignkey")
    op.drop_column("guides", "station_id")
    op.drop_column("guides", "service_id")

    op.drop_index(op.f("ix_pricing_rules_station_id"), table_name="pricing_rules")
    op.drop_index(op.f("ix_pricing_rules_service_id"), table_name="pricing_rules")
    op.drop_table("pricing_rules")

    op.drop_index(op.f("ix_riders_user_id"), table_name="riders")
    op.drop_table("riders")

    op.drop_index(op.f("ix_stations_zone_id"), table_name="stations")
    op.drop_table("stations")

    op.drop_index(op.f("ix_zones_code"), table_name="zones")
    op.drop_table("zones")

    op.drop_table("services")

    bind = op.get_bind()
    rider_state_enum.drop(bind, checkfirst=True)
    service_type_enum.drop(bind, checkfirst=True)
