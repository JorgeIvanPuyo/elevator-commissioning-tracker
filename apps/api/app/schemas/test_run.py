from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TestRunStatus = Literal["draft", "in_progress", "completed", "cancelled"]


class TestRunCreate(BaseModel):
    test_type_id: UUID
    status: TestRunStatus = "draft"
    technician_name: str = Field(min_length=1, max_length=160)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    title: str | None = Field(default=None, max_length=180)
    summary: str | None = None
    notes: str | None = None


class TestRunUpdate(BaseModel):
    test_type_id: UUID | None = None
    status: TestRunStatus | None = None
    technician_name: str | None = Field(default=None, min_length=1, max_length=160)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    title: str | None = Field(default=None, max_length=180)
    summary: str | None = None
    notes: str | None = None


class TestRunRead(BaseModel):
    id: UUID
    elevator_id: UUID
    test_type_id: UUID
    test_type_code: str
    test_type_name: str
    status: str
    technician_name: str
    started_at: datetime | None
    completed_at: datetime | None
    title: str | None
    summary: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestRunListItem(BaseModel):
    id: UUID
    title: str | None
    name: str
    status: str
    test_type_id: UUID
    test_type_code: str
    test_type_name: str
    elevator_id: UUID
    elevator_code: str
    project_id: UUID
    project_name: str
    responsible_technician: str
    created_at: datetime
    updated_at: datetime
