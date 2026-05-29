from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class LevelingMeasurement(Base):
    __tablename__ = "leveling_measurements"
    __table_args__ = (
        UniqueConstraint(
            "test_run_id",
            "origin_floor_id",
            "destination_floor_id",
            "direction",
            "travel_type",
            "measurement_stage",
            name="uq_leveling_measurements_run_route_stage",
        ),
        Index("ix_leveling_measurements_run_direction_travel", "test_run_id", "direction", "travel_type"),
        Index("ix_leveling_measurements_run_stage", "test_run_id", "measurement_stage"),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    test_run_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("test_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    origin_floor_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("elevator_floors.id", ondelete="RESTRICT"),
        nullable=False,
    )
    destination_floor_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("elevator_floors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    measurement_stage: Mapped[str] = mapped_column(String(32), nullable=False, default="floor_by_floor")
    direction: Mapped[str] = mapped_column(String(16), nullable=False)
    travel_type: Mapped[str] = mapped_column(String(16), nullable=False)
    landing_mm: Mapped[int | None] = mapped_column(Integer)
    final_mm: Mapped[int | None] = mapped_column(Integer)
    renivelation_occurred: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    effective_final_mm: Mapped[int | None] = mapped_column(Integer)
    is_final_within_tolerance: Mapped[bool | None] = mapped_column(Boolean)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    test_run = relationship("TestRun", back_populates="leveling_measurements")
    origin_floor = relationship("ElevatorFloor", foreign_keys=[origin_floor_id])
    destination_floor = relationship("ElevatorFloor", foreign_keys=[destination_floor_id])

    @property
    def did_relevel(self) -> bool:
        return self.renivelation_occurred
