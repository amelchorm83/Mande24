"""add CommissionClose and RouteLegStatusChange tables

Revision ID: 20260316_0010
Revises: 20260315_0009
Create Date: 2026-03-16
"""

from alembic import op
import sqlalchemy as sa


revision = "20260316_0010"
down_revision = "20260315_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commission_closes",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_progress"),
        sa.Column("rider_snapshots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("station_snapshots", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("week_start", name="uq_commission_close_week"),
    )

    op.create_table(
        "route_leg_status_changes",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("route_leg_id", sa.String(length=32), nullable=False),
        sa.Column("guide_id", sa.String(length=32), nullable=False),
        sa.Column("old_status", sa.String(length=20), nullable=False),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("changed_by_user_id", sa.String(length=32), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["route_leg_id"], ["route_legs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guide_id"], ["guides.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"]),
    )
    op.create_index("ix_route_leg_status_changes_route_leg_id", "route_leg_status_changes", ["route_leg_id"])
    op.create_index("ix_route_leg_status_changes_guide_id", "route_leg_status_changes", ["guide_id"])
    op.create_index("ix_route_leg_status_changes_changed_by_user_id", "route_leg_status_changes", ["changed_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_route_leg_status_changes_changed_by_user_id", table_name="route_leg_status_changes")
    op.drop_index("ix_route_leg_status_changes_guide_id", table_name="route_leg_status_changes")
    op.drop_index("ix_route_leg_status_changes_route_leg_id", table_name="route_leg_status_changes")
    op.drop_table("route_leg_status_changes")
    op.drop_table("commission_closes")
