"""add route legs and destination station support

Revision ID: 20260310_0006
Revises: 20260308_0005
Create Date: 2026-03-10
"""

from alembic import op
import sqlalchemy as sa


revision = "20260310_0006"
down_revision = "20260308_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("guides", sa.Column("destination_station_id", sa.String(length=32), nullable=True))
    op.create_foreign_key(
        "fk_guides_destination_station_id",
        "guides",
        "stations",
        ["destination_station_id"],
        ["id"],
    )

    op.create_table(
        "route_legs",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("guide_id", sa.String(length=32), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("leg_type", sa.String(length=40), nullable=False, server_default="pickup_to_station"),
        sa.Column("from_node_type", sa.String(length=40), nullable=False, server_default="client_origin"),
        sa.Column("to_node_type", sa.String(length=40), nullable=False, server_default="station"),
        sa.Column("origin_station_id", sa.String(length=32), nullable=True),
        sa.Column("destination_station_id", sa.String(length=32), nullable=True),
        sa.Column("assigned_rider_id", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="planned"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["guide_id"], ["guides.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["origin_station_id"], ["stations.id"]),
        sa.ForeignKeyConstraint(["destination_station_id"], ["stations.id"]),
        sa.ForeignKeyConstraint(["assigned_rider_id"], ["riders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_route_legs_guide_id"), "route_legs", ["guide_id"], unique=False)
    op.create_index(op.f("ix_route_legs_origin_station_id"), "route_legs", ["origin_station_id"], unique=False)
    op.create_index(op.f("ix_route_legs_destination_station_id"), "route_legs", ["destination_station_id"], unique=False)
    op.create_index(op.f("ix_route_legs_assigned_rider_id"), "route_legs", ["assigned_rider_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_route_legs_assigned_rider_id"), table_name="route_legs")
    op.drop_index(op.f("ix_route_legs_destination_station_id"), table_name="route_legs")
    op.drop_index(op.f("ix_route_legs_origin_station_id"), table_name="route_legs")
    op.drop_index(op.f("ix_route_legs_guide_id"), table_name="route_legs")
    op.drop_table("route_legs")

    op.drop_constraint("fk_guides_destination_station_id", "guides", type_="foreignkey")
    op.drop_column("guides", "destination_station_id")
