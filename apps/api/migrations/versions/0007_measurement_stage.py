"""add leveling measurement stage

Revision ID: 0007_measure_stage
Revises: 0006_commissioning
Create Date: 2026-05-29 15:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_measure_stage"
down_revision = "0006_commissioning"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "leveling_measurements",
        sa.Column("measurement_stage", sa.String(length=32), server_default="floor_by_floor", nullable=False),
    )
    op.drop_constraint("uq_leveling_measurements_run_route", "leveling_measurements", type_="unique")
    op.create_unique_constraint(
        "uq_leveling_measurements_run_route_stage",
        "leveling_measurements",
        ["test_run_id", "origin_floor_id", "destination_floor_id", "direction", "travel_type", "measurement_stage"],
    )
    op.create_index("ix_leveling_measurements_run_stage", "leveling_measurements", ["test_run_id", "measurement_stage"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_leveling_measurements_run_stage", table_name="leveling_measurements")
    op.drop_constraint("uq_leveling_measurements_run_route_stage", "leveling_measurements", type_="unique")
    op.create_unique_constraint(
        "uq_leveling_measurements_run_route",
        "leveling_measurements",
        ["test_run_id", "origin_floor_id", "destination_floor_id", "direction", "travel_type"],
    )
    op.drop_column("leveling_measurements", "measurement_stage")
