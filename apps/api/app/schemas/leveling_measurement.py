from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

MeasurementDirection = Literal["up", "down"]
MeasurementTravelType = Literal["short", "long"]
MeasurementStage = Literal["zone_tuning", "floor_by_floor", "final_validation"]


class LevelingMeasurementBulkItem(BaseModel):
    origin_floor_id: UUID
    destination_floor_id: UUID
    direction: MeasurementDirection
    travel_type: MeasurementTravelType
    measurement_stage: MeasurementStage = "floor_by_floor"
    landing_mm: int | None = None
    final_mm: int | None = None
    notes: str | None = None


class LevelingMeasurementBulkRequest(BaseModel):
    items: list[LevelingMeasurementBulkItem]


class LevelingMeasurementRead(BaseModel):
    id: UUID
    test_run_id: UUID
    origin_floor_id: UUID
    destination_floor_id: UUID
    direction: str
    travel_type: str
    measurement_stage: str
    landing_mm: int | None
    final_mm: int | None
    did_relevel: bool
    renivelation_occurred: bool
    effective_final_mm: int | None
    is_final_within_tolerance: bool | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LevelingMeasurementSummary(BaseModel):
    total: int
    with_values: int
    within_tolerance: int
    outside_tolerance: int
    within_tolerance_percentage: float


class LevelingMeasurementBulkResponse(BaseModel):
    items: list[LevelingMeasurementRead]
    summary: LevelingMeasurementSummary
