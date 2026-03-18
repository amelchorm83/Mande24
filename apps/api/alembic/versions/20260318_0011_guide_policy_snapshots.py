"""add guide policy snapshots

Revision ID: 20260318_0011
Revises: 20260316_0010
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa


revision = "20260318_0011"
down_revision = "20260316_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "guide_policy_snapshots",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guide_id", sa.String(length=32), nullable=False),
        sa.Column("requester_role", sa.String(length=20), nullable=False, server_default="origin"),
        sa.Column("requested_service_type", sa.String(length=50), nullable=False, server_default="messaging"),
        sa.Column("applied_service_type", sa.String(length=50), nullable=False, server_default="messaging"),
        sa.Column("service_converted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("policy_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["guide_id"], ["guides.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("guide_id"),
    )
    op.create_index("ix_guide_policy_snapshots_guide_id", "guide_policy_snapshots", ["guide_id"])


def downgrade() -> None:
    op.drop_index("ix_guide_policy_snapshots_guide_id", table_name="guide_policy_snapshots")
    op.drop_table("guide_policy_snapshots")
