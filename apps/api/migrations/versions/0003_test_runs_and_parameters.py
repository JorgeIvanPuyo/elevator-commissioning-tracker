"""create test runs and parameter values

Revision ID: 0003_test_runs_and_parameters
Revises: 0002_elevator_floors
Create Date: 2026-05-27 09:00:00
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_test_runs_and_parameters"
down_revision = "0002_elevator_floors"
branch_labels = None
depends_on = None


PARAMETER_SEED_DATA = [
    ("A61E", "0% load setup", "load_test", None, None, None, None, 10),
    ("A62E", "100% load setup", "load_test", None, None, None, None, 20),
    ("A65E", "Automatic leveling without load", "auto_leveling", None, None, None, None, 30),
    ("A66E", "Automatic leveling with 100% load", "auto_leveling", None, None, None, None, 40),
    ("A67E", "Automatic load compensation", "load_compensation", None, None, None, None, 50),
    ("026D", "Low zone up bias minimum", "fine_leveling", "low", "up", "min", "273", 100),
    ("026E", "Low zone down bias minimum", "fine_leveling", "low", "down", "min", "274", 110),
    ("026F", "Mid zone up bias minimum", "fine_leveling", "mid", "up", "min", "275", 120),
    ("270", "Mid zone down bias minimum", "fine_leveling", "mid", "down", "min", "276", 130),
    ("271", "High zone up bias minimum", "fine_leveling", "high", "up", "min", "277", 140),
    ("272", "High zone down bias minimum", "fine_leveling", "high", "down", "min", "278", 150),
    ("273", "Low zone up bias maximum", "fine_leveling", "low", "up", "max", "026D", 160),
    ("274", "Low zone down bias maximum", "fine_leveling", "low", "down", "max", "026E", 170),
    ("275", "Mid zone up bias maximum", "fine_leveling", "mid", "up", "max", "026F", 180),
    ("276", "Mid zone down bias maximum", "fine_leveling", "mid", "down", "max", "270", 190),
    ("277", "High zone up bias maximum", "fine_leveling", "high", "up", "max", "271", 200),
    ("278", "High zone down bias maximum", "fine_leveling", "high", "down", "max", "272", 210),
    ("266", "Load compensation reference", "load_compensation", None, None, None, None, 300),
    ("240", "Load compensation parameter 240", "load_compensation", None, None, None, None, 310),
    ("241", "Load compensation parameter 241", "load_compensation", None, None, None, None, 320),
    ("242", "Load compensation parameter 242", "load_compensation", None, None, None, None, 330),
    ("243", "Load compensation parameter 243", "load_compensation", None, None, None, None, 340),
    ("244", "Load compensation parameter 244", "load_compensation", None, None, None, None, 350),
    ("245", "Load compensation parameter 245", "load_compensation", None, None, None, None, 360),
    ("212", "Manual leveling adjustment 212", "manual_adjustment", None, None, None, None, 400),
    ("214", "Manual leveling adjustment 214", "manual_adjustment", None, None, None, None, 410),
    ("022F", "Manual hysteresis/general adjustment", "manual_adjustment", None, None, None, None, 420),
    ("229", "Manual leveling related adjustment", "manual_adjustment", None, None, None, None, 430),
]


def upgrade() -> None:
    op.create_table(
        "parameter_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=True),
        sa.Column("zone", sa.String(length=80), nullable=True),
        sa.Column("direction", sa.String(length=80), nullable=True),
        sa.Column("bound_type", sa.String(length=16), nullable=True),
        sa.Column("pair_code", sa.String(length=32), nullable=True),
        sa.Column("is_editable", sa.Boolean(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_parameter_definitions_category"), "parameter_definitions", ["category"], unique=False)
    op.create_index(op.f("ix_parameter_definitions_code"), "parameter_definitions", ["code"], unique=False)

    op.create_table(
        "test_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("elevator_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_type_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("technician_name", sa.String(length=160), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["elevator_id"], ["elevators.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_type_id"], ["test_types.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_runs_elevator_id"), "test_runs", ["elevator_id"], unique=False)
    op.create_index(op.f("ix_test_runs_test_type_id"), "test_runs", ["test_type_id"], unique=False)

    op.create_table(
        "test_run_parameter_values",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parameter_definition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("hex_value", sa.String(length=64), nullable=True),
        sa.Column("decimal_value", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["parameter_definition_id"], ["parameter_definitions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_run_id", "parameter_definition_id", name="uq_test_run_parameter_values_run_definition"),
    )
    op.create_index(
        op.f("ix_test_run_parameter_values_parameter_definition_id"),
        "test_run_parameter_values",
        ["parameter_definition_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_test_run_parameter_values_test_run_id"),
        "test_run_parameter_values",
        ["test_run_id"],
        unique=False,
    )

    parameter_table = sa.table(
        "parameter_definitions",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("category", sa.String),
        sa.column("zone", sa.String),
        sa.column("direction", sa.String),
        sa.column("bound_type", sa.String),
        sa.column("pair_code", sa.String),
        sa.column("is_editable", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    op.bulk_insert(
        parameter_table,
        [
            {
                "id": uuid4(),
                "code": code,
                "name": name,
                "description": None,
                "category": category,
                "zone": zone,
                "direction": direction,
                "bound_type": bound_type,
                "pair_code": pair_code,
                "is_editable": True,
                "sort_order": sort_order,
            }
            for code, name, category, zone, direction, bound_type, pair_code, sort_order in PARAMETER_SEED_DATA
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_test_run_parameter_values_test_run_id"), table_name="test_run_parameter_values")
    op.drop_index(op.f("ix_test_run_parameter_values_parameter_definition_id"), table_name="test_run_parameter_values")
    op.drop_table("test_run_parameter_values")
    op.drop_index(op.f("ix_test_runs_test_type_id"), table_name="test_runs")
    op.drop_index(op.f("ix_test_runs_elevator_id"), table_name="test_runs")
    op.drop_table("test_runs")
    op.drop_index(op.f("ix_parameter_definitions_code"), table_name="parameter_definitions")
    op.drop_index(op.f("ix_parameter_definitions_category"), table_name="parameter_definitions")
    op.drop_table("parameter_definitions")
