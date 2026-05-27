"""create core models

Revision ID: 0001_core_models
Revises:
Create Date: 2026-05-26 20:30:00
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_core_models"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("client_name", sa.String(length=160), nullable=True),
        sa.Column("location", sa.String(length=220), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("total_elevators", sa.Integer(), nullable=True),
        sa.Column("default_floor_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_name"), "projects", ["name"], unique=False)

    op.create_table(
        "test_types",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("documentation_slug", sa.String(length=160), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    op.create_table(
        "elevators",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=True),
        sa.Column("floor_count", sa.Integer(), nullable=False),
        sa.Column("controller_model", sa.String(length=160), nullable=True),
        sa.Column("machine_room", sa.String(length=160), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "code", name="uq_elevators_project_code"),
    )
    op.create_index(op.f("ix_elevators_project_id"), "elevators", ["project_id"], unique=False)

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

    test_types_table = sa.table(
        "test_types",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("documentation_slug", sa.String),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        test_types_table,
        [
            {
                "id": uuid4(),
                "code": "LOAD_TEST",
                "name": "Prueba de carga",
                "description": None,
                "documentation_slug": "load-test",
                "is_active": True,
                "sort_order": 10,
            },
            {
                "id": uuid4(),
                "code": "FINE_LEVELING",
                "name": "Nivelación fina",
                "description": None,
                "documentation_slug": "fine-leveling",
                "is_active": True,
                "sort_order": 20,
            },
            {
                "id": uuid4(),
                "code": "LOAD_COMPENSATION",
                "name": "Compensación de carga",
                "description": None,
                "documentation_slug": "load-compensation",
                "is_active": True,
                "sort_order": 30,
            },
            {
                "id": uuid4(),
                "code": "PARAMETER_ADJUSTMENT",
                "name": "Ajuste de parámetros",
                "description": None,
                "documentation_slug": "parameter-adjustment",
                "is_active": True,
                "sort_order": 40,
            },
            {
                "id": uuid4(),
                "code": "FLOOR_MEASUREMENT",
                "name": "Medición piso a piso",
                "description": None,
                "documentation_slug": "floor-measurement",
                "is_active": True,
                "sort_order": 50,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_floor_labels_project_id"), table_name="floor_labels")
    op.drop_table("floor_labels")
    op.drop_index(op.f("ix_elevators_project_id"), table_name="elevators")
    op.drop_table("elevators")
    op.drop_table("test_types")
    op.drop_index(op.f("ix_projects_name"), table_name="projects")
    op.drop_table("projects")
