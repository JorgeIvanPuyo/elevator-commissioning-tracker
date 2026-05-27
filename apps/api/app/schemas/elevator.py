from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ElevatorStatus = Literal["pending", "in_progress", "completed"]


class ElevatorCreate(BaseModel):
    code: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=160)
    floor_count: int | None = Field(default=None, ge=1, le=200)
    controller_model: str | None = Field(default=None, max_length=160)
    machine_room: str | None = Field(default=None, max_length=160)
    notes: str | None = None
    status: ElevatorStatus = "pending"


class ElevatorUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, max_length=160)
    floor_count: int | None = Field(default=None, ge=1, le=200)
    controller_model: str | None = Field(default=None, max_length=160)
    machine_room: str | None = Field(default=None, max_length=160)
    notes: str | None = None
    status: ElevatorStatus | None = None


class ElevatorRead(BaseModel):
    id: UUID
    project_id: UUID
    code: str
    name: str | None
    floor_count: int
    controller_model: str | None
    machine_room: str | None
    notes: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
