"""add guide pricing fields and commission tables

Revision ID: 20260308_0004
Revises: 20260308_0003
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0004"
down_revision = "20260308_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("guides", sa.Column("sale_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("guides", sa.Column("currency", sa.String(length=10), nullable=False, server_default="MXN"))

    op.add_column("deliveries", sa.Column("rider_id", sa.String(length=32), nullable=True))
    op.add_column("deliveries", sa.Column("commission_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("deliveries", sa.Column("delivered_at", sa.DateTime(), nullable=True))
    op.create_index(op.f("ix_deliveries_rider_id"), "deliveries", ["rider_id"], unique=False)
    op.create_foreign_key("fk_deliveries_rider_id", "deliveries", "riders", ["rider_id"], ["id"])

    op.create_table(
        "rider_commissions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("rider_id", sa.String(length=32), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("delivery_count", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["rider_id"], ["riders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rider_commissions_rider_id"), "rider_commissions", ["rider_id"], unique=False)

    op.create_table(
        "station_commissions",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("station_id", sa.String(length=32), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("sold_guide_count", sa.Integer(), nullable=False),
        sa.Column("sold_guide_amount", sa.Float(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["station_id"], ["stations.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_station_commissions_station_id"), "station_commissions", ["station_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_station_commissions_station_id"), table_name="station_commissions")
    op.drop_table("station_commissions")

    op.drop_index(op.f("ix_rider_commissions_rider_id"), table_name="rider_commissions")
    op.drop_table("rider_commissions")

    op.drop_constraint("fk_deliveries_rider_id", "deliveries", type_="foreignkey")
    op.drop_index(op.f("ix_deliveries_rider_id"), table_name="deliveries")
    op.drop_column("deliveries", "delivered_at")
    op.drop_column("deliveries", "commission_amount")
    op.drop_column("deliveries", "rider_id")

    op.drop_column("guides", "currency")
    op.drop_column("guides", "sale_amount")
