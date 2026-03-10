"""add pricing and route leg fee fields

Revision ID: 20260310_0007
Revises: 20260310_0006
Create Date: 2026-03-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_0007"
down_revision = "20260310_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("pricing_rules", sa.Column("pickup_fee", sa.Float(), nullable=False, server_default="0"))
    op.add_column("pricing_rules", sa.Column("delivery_fee", sa.Float(), nullable=False, server_default="0"))
    op.add_column("pricing_rules", sa.Column("transfer_fee", sa.Float(), nullable=False, server_default="0"))
    op.add_column("pricing_rules", sa.Column("station_fee", sa.Float(), nullable=False, server_default="0"))

    op.add_column("route_legs", sa.Column("rider_fee_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("route_legs", sa.Column("station_fee_amount", sa.Float(), nullable=False, server_default="0"))
    op.add_column("route_legs", sa.Column("currency", sa.String(length=10), nullable=False, server_default="MXN"))


def downgrade() -> None:
    op.drop_column("route_legs", "currency")
    op.drop_column("route_legs", "station_fee_amount")
    op.drop_column("route_legs", "rider_fee_amount")

    op.drop_column("pricing_rules", "station_fee")
    op.drop_column("pricing_rules", "transfer_fee")
    op.drop_column("pricing_rules", "delivery_fee")
    op.drop_column("pricing_rules", "pickup_fee")
