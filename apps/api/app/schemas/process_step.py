from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TestRunProcessStepUpdate(BaseModel):
    is_completed: bool | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class TestRunProcessStepRead(BaseModel):
    id: UUID
    test_run_id: UUID
    code: str
    name: str
    description: str | None
    is_completed: bool
    completed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
