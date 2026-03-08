"""create guides and deliveries tables

Revision ID: 20260308_0001
Revises:
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260308_0001"
down_revision = None
branch_labels = None
depends_on = None


workflow_stage_enum = sa.Enum(
    "assigned",
    "picked_up",
    "in_transit",
    "at_station",
    "out_for_delivery",
    "delivered",
    "failed",
    name="workflow_stage",
)


def upgrade() -> None:
    bind = op.get_bind()
    workflow_stage_enum.create(bind, checkfirst=True)

    op.create_table(
        "guides",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guide_code", sa.String(length=40), nullable=False),
        sa.Column("customer_name", sa.String(length=150), nullable=False),
        sa.Column("destination_name", sa.String(length=150), nullable=False),
        sa.Column("service_type", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("guide_code"),
    )
    op.create_index(op.f("ix_guides_guide_code"), "guides", ["guide_code"], unique=False)

    op.create_table(
        "deliveries",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guide_id", sa.String(length=32), nullable=False),
        sa.Column("stage", workflow_stage_enum, nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("has_evidence", sa.Boolean(), nullable=False),
        sa.Column("has_signature", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["guide_id"], ["guides.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_deliveries_guide_id"), "deliveries", ["guide_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_deliveries_guide_id"), table_name="deliveries")
    op.drop_table("deliveries")
    op.drop_index(op.f("ix_guides_guide_code"), table_name="guides")
    op.drop_table("guides")
    bind = op.get_bind()
    workflow_stage_enum.drop(bind, checkfirst=True)
