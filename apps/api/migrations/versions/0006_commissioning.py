"""create commissioning workflow

Revision ID: 0006_commissioning
Revises: 0005_leveling
Create Date: 2026-05-29 10:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0006_commissioning"
down_revision = "0005_leveling"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "commissioning_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elevator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("technician_name", sa.String(length=160), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["elevator_id"], ["elevators.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("elevator_id"),
    )
    op.create_index(op.f("ix_commissioning_workflows_elevator_id"), "commissioning_workflows", ["elevator_id"], unique=False)

    op.create_table(
        "commissioning_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False),
        sa.Column("is_blocking", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technician_name", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["commissioning_workflows.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workflow_id", "code", name="uq_commissioning_steps_workflow_code"),
        sa.UniqueConstraint("workflow_id", "sort_order", name="uq_commissioning_steps_workflow_sort_order"),
    )
    op.create_index(op.f("ix_commissioning_steps_status"), "commissioning_steps", ["status"], unique=False)
    op.create_index(op.f("ix_commissioning_steps_workflow_id"), "commissioning_steps", ["workflow_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_commissioning_steps_workflow_id"), table_name="commissioning_steps")
    op.drop_index(op.f("ix_commissioning_steps_status"), table_name="commissioning_steps")
    op.drop_table("commissioning_steps")
    op.drop_index(op.f("ix_commissioning_workflows_elevator_id"), table_name="commissioning_workflows")
    op.drop_table("commissioning_workflows")
