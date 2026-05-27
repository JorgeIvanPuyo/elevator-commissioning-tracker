from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

ProjectStatus = Literal["active", "paused", "completed"]


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    client_name: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=220)
    description: str | None = None
    total_elevators: int | None = Field(default=None, ge=0)
    default_floor_count: int = Field(default=62, ge=1, le=200)
    status: ProjectStatus = "active"


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    client_name: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=220)
    description: str | None = None
    total_elevators: int | None = Field(default=None, ge=0)
    default_floor_count: int | None = Field(default=None, ge=1, le=200)
    status: ProjectStatus | None = None


class ProjectRead(BaseModel):
    id: UUID
    name: str
    client_name: str | None
    location: str | None
    description: str | None
    total_elevators: int | None
    default_floor_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
