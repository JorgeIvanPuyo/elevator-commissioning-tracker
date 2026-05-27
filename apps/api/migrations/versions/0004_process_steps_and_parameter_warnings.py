"""separate process steps from parameter definitions

Revision ID: 0004_process_steps
Revises: 0003_test_runs_and_parameters
Create Date: 2026-05-27 13:00:00
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_process_steps"
down_revision = "0003_test_runs_and_parameters"
branch_labels = None
depends_on = None

PROCESS_STEPS = [
    ("A61E", "Calibración 0% de carga", "Proceso de calibración de potenciómetros a 0% de carga."),
    ("A62E", "Calibración 100% de carga", "Proceso de calibración de potenciómetros a 100% de carga."),
    ("A65E", "Nivelación automática sin carga", "Proceso automático de nivelación sin carga / 0% de carga."),
    ("A66E", "Nivelación automática con 100% de carga", "Proceso automático de nivelación con 100% de carga."),
    ("A67E", "Compensación automática de carga", "Proceso automático de compensación de carga."),
]


def upgrade() -> None:
    op.create_table(
        "test_run_process_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("test_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_run_id", "code", name="uq_test_run_process_steps_run_code"),
    )
    op.create_index(op.f("ix_test_run_process_steps_test_run_id"), "test_run_process_steps", ["test_run_id"], unique=False)

    op.execute(
        sa.text(
            """
            DELETE FROM parameter_definitions
            WHERE code IN ('A61E', 'A62E', 'A65E', 'A66E', 'A67E')
            """
        )
    )

    for code, name, description in PROCESS_STEPS:
        op.execute(
            sa.text(
                """
                INSERT INTO test_run_process_steps (test_run_id, code, name, description, is_completed)
                SELECT id, :code, :name, :description, false
                FROM test_runs
                ON CONFLICT (test_run_id, code) DO NOTHING
                """
            ).bindparams(code=code, name=name, description=description)
        )


def downgrade() -> None:
    op.drop_index(op.f("ix_test_run_process_steps_test_run_id"), table_name="test_run_process_steps")
    op.drop_table("test_run_process_steps")

    parameter_table = sa.table(
        "parameter_definitions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("is_editable", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        parameter_table,
        [
            {
                "id": uuid4(),
                "code": "A61E",
                "name": "0% load setup",
                "description": None,
                "category": "load_test",
                "is_editable": True,
                "sort_order": 10,
            },
            {
                "id": uuid4(),
                "code": "A62E",
                "name": "100% load setup",
                "description": None,
                "category": "load_test",
                "is_editable": True,
                "sort_order": 20,
            },
            {
                "id": uuid4(),
                "code": "A65E",
                "name": "Automatic leveling without load",
                "description": None,
                "category": "auto_leveling",
                "is_editable": True,
                "sort_order": 30,
            },
            {
                "id": uuid4(),
                "code": "A66E",
                "name": "Automatic leveling with 100% load",
                "description": None,
                "category": "auto_leveling",
                "is_editable": True,
                "sort_order": 40,
            },
            {
                "id": uuid4(),
                "code": "A67E",
                "name": "Automatic load compensation",
                "description": None,
                "category": "load_compensation",
                "is_editable": True,
                "sort_order": 50,
            },
        ],
    )
