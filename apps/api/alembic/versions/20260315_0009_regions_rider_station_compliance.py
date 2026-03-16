"""add regions and rider/station compliance fields

Revision ID: 20260315_0009
Revises: 20260314_0008
Create Date: 2026-03-15
"""

from alembic import op
import sqlalchemy as sa


revision = "20260315_0009"
down_revision = "20260314_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "operational_settings",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("description", sa.String(length=255), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "regions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_regions_code", "regions", ["code"], unique=False)

    op.add_column("zones", sa.Column("region_id", sa.String(length=32), nullable=True))
    op.create_index("ix_zones_region_id", "zones", ["region_id"], unique=False)
    op.create_foreign_key("fk_zones_region_id", "zones", "regions", ["region_id"], ["id"])

    op.add_column("riders", sa.Column("license_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("riders", sa.Column("license_expires_at", sa.Date(), nullable=True))
    op.add_column("riders", sa.Column("circulation_card_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("riders", sa.Column("insurance_policy_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("riders", sa.Column("insurance_expires_at", sa.Date(), nullable=True))
    op.add_column("riders", sa.Column("contract_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("riders", sa.Column("contract_signed_at", sa.Date(), nullable=True))
    op.add_column("riders", sa.Column("comprobaciones_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("riders", sa.Column("work_days", sa.String(length=80), nullable=False, server_default="mon,tue,wed,thu,fri,sat"))
    op.add_column("riders", sa.Column("rest_day", sa.String(length=12), nullable=False, server_default="sun"))
    op.add_column("riders", sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.execute("CREATE TYPE rider_account_status AS ENUM ('active', 'suspended', 'deactivated')")
    op.add_column(
        "riders",
        sa.Column(
            "account_status",
            sa.Enum("active", "suspended", "deactivated", name="rider_account_status"),
            nullable=False,
            server_default="active",
        ),
    )

    op.add_column("stations", sa.Column("responsible_name", sa.String(length=150), nullable=False, server_default=""))
    op.add_column("stations", sa.Column("proof_of_address_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("stations", sa.Column("rfc_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("stations", sa.Column("comprobaciones_file", sa.String(length=255), nullable=False, server_default=""))
    op.add_column("stations", sa.Column("work_days", sa.String(length=80), nullable=False, server_default="mon,tue,wed,thu,fri,sat"))
    op.add_column("stations", sa.Column("rest_day", sa.String(length=12), nullable=False, server_default="sun"))
    op.add_column("stations", sa.Column("opening_time", sa.String(length=5), nullable=False, server_default="09:00"))
    op.add_column("stations", sa.Column("closing_time", sa.String(length=5), nullable=False, server_default="18:00"))
    op.add_column("stations", sa.Column("max_active_users", sa.Integer(), nullable=False, server_default="3"))

    op.execute(
        """
        INSERT INTO regions (id, name, code, active)
        VALUES
            (md5(random()::text || clock_timestamp()::text), 'Region General', 'RGN_GENERAL', true)
        """
    )

    op.execute(
        """
        INSERT INTO operational_settings (key, value, description)
        VALUES
            ('errand_24_7', 'true', 'Mandaditos disponible 24 horas 365 dias'),
            ('night_start_hour', '22', 'Hora inicio tarifa nocturna'),
            ('night_end_hour', '7', 'Hora fin tarifa nocturna'),
            ('night_surcharge_factor', '1.15', 'Multiplicador de tarifa nocturna')
        """
    )


def downgrade() -> None:
    op.drop_table("operational_settings")

    op.drop_column("stations", "max_active_users")
    op.drop_column("stations", "closing_time")
    op.drop_column("stations", "opening_time")
    op.drop_column("stations", "rest_day")
    op.drop_column("stations", "work_days")
    op.drop_column("stations", "comprobaciones_file")
    op.drop_column("stations", "rfc_file")
    op.drop_column("stations", "proof_of_address_file")
    op.drop_column("stations", "responsible_name")

    op.drop_column("riders", "account_status")
    op.execute("DROP TYPE rider_account_status")
    op.drop_column("riders", "is_available")
    op.drop_column("riders", "rest_day")
    op.drop_column("riders", "work_days")
    op.drop_column("riders", "comprobaciones_file")
    op.drop_column("riders", "contract_signed_at")
    op.drop_column("riders", "contract_file")
    op.drop_column("riders", "insurance_expires_at")
    op.drop_column("riders", "insurance_policy_file")
    op.drop_column("riders", "circulation_card_file")
    op.drop_column("riders", "license_expires_at")
    op.drop_column("riders", "license_file")

    op.drop_constraint("fk_zones_region_id", "zones", type_="foreignkey")
    op.drop_index("ix_zones_region_id", table_name="zones")
    op.drop_column("zones", "region_id")

    op.drop_index("ix_regions_code", table_name="regions")
    op.drop_table("regions")
