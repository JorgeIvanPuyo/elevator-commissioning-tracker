from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ParameterDefinitionRead(BaseModel):
    id: UUID
    code: str
    name: str
    description: str | None
    category: str | None
    zone: str | None
    direction: str | None
    bound_type: str | None
    pair_code: str | None
    is_editable: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestRunParameterValueInput(BaseModel):
    parameter_code: str = Field(min_length=1, max_length=32)
    hex_value: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=80)
    notes: str | None = None


class TestRunParameterValuesUpsert(BaseModel):
    values: list[TestRunParameterValueInput]


class TestRunParameterValueRead(BaseModel):
    id: UUID
    test_run_id: UUID
    parameter_definition_id: UUID
    parameter_code: str
    parameter_name: str
    hex_value: str | None
    decimal_value: int | None
    source: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestRunParameterValuesResponse(BaseModel):
    test_run_id: UUID
    values: list[TestRunParameterValueRead]
    validation_warnings: list[str] = []
