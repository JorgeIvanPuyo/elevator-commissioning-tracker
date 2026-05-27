"""replace project floor labels with elevator floors

Revision ID: 0002_elevator_floors
Revises: 0001_core_models
Create Date: 2026-05-26 21:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_elevator_floors"
down_revision = "0001_core_models"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(op.f("ix_floor_labels_project_id"), table_name="floor_labels")
    op.drop_table("floor_labels")

    op.create_table(
        "elevator_floors",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elevator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=True),
        sa.Column("is_served", sa.Boolean(), nullable=False),
        sa.Column("is_leveling_required", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["elevator_id"], ["elevators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("elevator_id", "sort_order", name="uq_elevator_floors_elevator_sort_order"),
    )
    op.create_index(op.f("ix_elevator_floors_elevator_id"), "elevator_floors", ["elevator_id"], unique=False)
    op.create_index(
        "uq_elevator_floors_elevator_label_not_empty",
        "elevator_floors",
        ["elevator_id", "label"],
        unique=True,
        postgresql_where=sa.text("label IS NOT NULL AND label <> ''"),
    )


def downgrade() -> None:
    op.drop_index("uq_elevator_floors_elevator_label_not_empty", table_name="elevator_floors")
    op.drop_index(op.f("ix_elevator_floors_elevator_id"), table_name="elevator_floors")
    op.drop_table("elevator_floors")

    op.create_table(
        "floor_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "label", name="uq_floor_labels_project_label"),
    )
    op.create_index(op.f("ix_floor_labels_project_id"), "floor_labels", ["project_id"], unique=False)
