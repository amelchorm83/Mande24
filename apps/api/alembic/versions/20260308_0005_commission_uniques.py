"""add unique constraints for weekly commission snapshots

Revision ID: 20260308_0005
Revises: 20260308_0004
Create Date: 2026-03-08
"""

from alembic import op


revision = "20260308_0005"
down_revision = "20260308_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_rider_commission_week", "rider_commissions", ["rider_id", "week_start"])
    op.create_unique_constraint("uq_station_commission_week", "station_commissions", ["station_id", "week_start"])


def downgrade() -> None:
    op.drop_constraint("uq_station_commission_week", "station_commissions", type_="unique")
    op.drop_constraint("uq_rider_commission_week", "rider_commissions", type_="unique")
