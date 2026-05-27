from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TestRunParameterValue(Base):
    __tablename__ = "test_run_parameter_values"
    __table_args__ = (
        UniqueConstraint(
            "test_run_id",
            "parameter_definition_id",
            name="uq_test_run_parameter_values_run_definition",
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parameter_definition_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("parameter_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    hex_value: Mapped[str | None] = mapped_column(String(64))
    decimal_value: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str | None] = mapped_column(String(80))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    test_run = relationship("TestRun", back_populates="parameter_values")
    parameter_definition = relationship("ParameterDefinition", back_populates="values")
