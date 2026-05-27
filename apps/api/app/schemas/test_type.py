from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TestTypeRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    documentation_slug: str | None
    is_active: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
