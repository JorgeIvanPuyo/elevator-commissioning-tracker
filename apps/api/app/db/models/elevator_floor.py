from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ElevatorFloor(Base):
    __tablename__ = "elevator_floors"
    __table_args__ = (
        UniqueConstraint("elevator_id", "sort_order", name="uq_elevator_floors_elevator_sort_order"),
        Index(
            "uq_elevator_floors_elevator_label_not_empty",
            "elevator_id",
            "label",
            unique=True,
            postgresql_where=text("label IS NOT NULL AND label <> ''"),
        ),
    )

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    elevator_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        ForeignKey("elevators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str | None] = mapped_column(String(64))
    is_served: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_leveling_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    elevator = relationship("Elevator", back_populates="floors")
