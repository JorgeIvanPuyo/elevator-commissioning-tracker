from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ElevatorFloorCreate(BaseModel):
    sort_order: int = Field(ge=1, le=300)
    label: str | None = Field(default=None, max_length=64)
    is_served: bool = True
    is_leveling_required: bool = True
    notes: str | None = None


class ElevatorFloorUpdate(BaseModel):
    sort_order: int | None = Field(default=None, ge=1, le=300)
    label: str | None = Field(default=None, max_length=64)
    is_served: bool | None = None
    is_leveling_required: bool | None = None
    notes: str | None = None


class ElevatorFloorRead(BaseModel):
    id: UUID
    elevator_id: UUID
    sort_order: int
    label: str | None
    is_served: bool
    is_leveling_required: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
