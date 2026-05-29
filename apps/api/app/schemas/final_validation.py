from uuid import UUID

from pydantic import BaseModel


class FinalValidationSummary(BaseModel):
    total_required_floors: int
    floors_with_complete_data: int
    floors_within_tolerance: int
    floors_out_of_tolerance: int
    floors_missing_data: int
    floors_partial_data: int
    completion_percent: float
    within_tolerance_percent: float
    max_abs_final_mm: float | None


class FinalValidationRow(BaseModel):
    floor_id: UUID
    floor_label: str
    sort_order: int
    down_final_mm: float | None
    up_final_mm: float | None
    status: str
    within_tolerance: bool | None


class FinalValidationSummaryRead(BaseModel):
    test_run_id: UUID
    elevator_id: UUID
    tolerance_mm: float
    fhm_completed: bool
    fhm_step_status: str | None
    summary: FinalValidationSummary
    rows: list[FinalValidationRow]
