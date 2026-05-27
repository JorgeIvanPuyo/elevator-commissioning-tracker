"""create leveling measurements

Revision ID: 0005_leveling
Revises: 0004_process_steps
Create Date: 2026-05-27 16:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_leveling"
down_revision = "0004_process_steps"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "leveling_measurements",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("origin_floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("destination_floor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("travel_type", sa.String(length=16), nullable=False),
        sa.Column("landing_mm", sa.Integer(), nullable=True),
        sa.Column("final_mm", sa.Integer(), nullable=True),
        sa.Column("renivelation_occurred", sa.Boolean(), nullable=False),
        sa.Column("effective_final_mm", sa.Integer(), nullable=True),
        sa.Column("is_final_within_tolerance", sa.Boolean(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["destination_floor_id"], ["elevator_floors.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["origin_floor_id"], ["elevator_floors.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "test_run_id",
            "origin_floor_id",
            "destination_floor_id",
            "direction",
            "travel_type",
            name="uq_leveling_measurements_run_route",
        ),
    )
    op.create_index(op.f("ix_leveling_measurements_destination_floor_id"), "leveling_measurements", ["destination_floor_id"], unique=False)
    op.create_index("ix_leveling_measurements_run_direction_travel", "leveling_measurements", ["test_run_id", "direction", "travel_type"], unique=False)
    op.create_index(op.f("ix_leveling_measurements_test_run_id"), "leveling_measurements", ["test_run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_leveling_measurements_test_run_id"), table_name="leveling_measurements")
    op.drop_index("ix_leveling_measurements_run_direction_travel", table_name="leveling_measurements")
    op.drop_index(op.f("ix_leveling_measurements_destination_floor_id"), table_name="leveling_measurements")
    op.drop_table("leveling_measurements")
