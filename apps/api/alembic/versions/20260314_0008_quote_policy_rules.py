"""create quote policy and zone surcharge rules

Revision ID: 20260314_0008
Revises: 20260310_0007
Create Date: 2026-03-14
"""

from alembic import op
import sqlalchemy as sa


revision = "20260314_0008"
down_revision = "20260310_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_policy_rules",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("service_type", sa.String(length=40), nullable=False),
        sa.Column("fallback_service_type", sa.String(length=40), nullable=True),
        sa.Column("max_distance_km", sa.Float(), nullable=True),
        sa.Column("service_factor", sa.Float(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quote_policy_rules_service_type", "quote_policy_rules", ["service_type"], unique=False)

    op.create_table(
        "zone_surcharge_rules",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("zone_type", sa.String(length=40), nullable=False),
        sa.Column("rural_complexity", sa.String(length=20), nullable=True),
        sa.Column("zone_factor", sa.Float(), nullable=False, server_default="1"),
        sa.Column("complexity_factor", sa.Float(), nullable=False, server_default="1"),
        sa.Column("eta_extra_minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_zone_surcharge_rules_zone_type", "zone_surcharge_rules", ["zone_type"], unique=False)
    op.create_index("ix_zone_surcharge_rules_rural_complexity", "zone_surcharge_rules", ["rural_complexity"], unique=False)

    op.execute(
        """
        INSERT INTO quote_policy_rules (id, service_type, fallback_service_type, max_distance_km, service_factor, active, notes)
        VALUES
            (md5(random()::text || clock_timestamp()::text), 'programado', NULL, NULL, 1.0, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'express', NULL, NULL, 1.3, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'recurrente', NULL, NULL, 0.9, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'mandaditos', 'paqueteria', 10.0, 1.12, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'paqueteria', NULL, NULL, 1.2, true, 'Semilla inicial');
        """
    )

    op.execute(
        """
        INSERT INTO zone_surcharge_rules (id, zone_type, rural_complexity, zone_factor, complexity_factor, eta_extra_minutes, active, notes)
        VALUES
            (md5(random()::text || clock_timestamp()::text), 'urbana', NULL, 1.0, 1.0, 0, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'metropolitana', NULL, 1.18, 1.0, 0, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'intermunicipal', NULL, 1.35, 1.0, 18, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'rural', 'baja', 1.45, 1.04, 28, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'rural', 'media', 1.45, 1.12, 28, true, 'Semilla inicial'),
            (md5(random()::text || clock_timestamp()::text), 'rural', 'alta', 1.45, 1.25, 28, true, 'Semilla inicial');
        """
    )


def downgrade() -> None:
    op.drop_index("ix_zone_surcharge_rules_rural_complexity", table_name="zone_surcharge_rules")
    op.drop_index("ix_zone_surcharge_rules_zone_type", table_name="zone_surcharge_rules")
    op.drop_table("zone_surcharge_rules")

    op.drop_index("ix_quote_policy_rules_service_type", table_name="quote_policy_rules")
    op.drop_table("quote_policy_rules")
