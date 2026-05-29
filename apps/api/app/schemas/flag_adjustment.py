from uuid import UUID

from pydantic import BaseModel


class FlagAdjustmentSummary(BaseModel):
    total_required_floors: int
    floors_with_complete_data: int
    floors_within_tolerance: int
    floors_requiring_flag_adjustment: int
    floors_missing_data: int
    floors_partial_data: int
    max_abs_recommended_movement_mm: float | None


class FlagAdjustmentRow(BaseModel):
    floor_id: UUID
    floor_label: str
    sort_order: int
    down_final_mm: float | None
    up_final_mm: float | None
    average_final_mm: float | None
    recommended_flag_movement_mm: float | None
    status: str
    within_tolerance: bool | None
    notes: list[str] = []


class FlagAdjustmentRecommendationsRead(BaseModel):
    test_run_id: UUID
    elevator_id: UUID
    tolerance_mm: float
    summary: FlagAdjustmentSummary
    rows: list[FlagAdjustmentRow]
