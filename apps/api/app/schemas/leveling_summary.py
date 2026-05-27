from uuid import UUID

from pydantic import BaseModel


class LevelingFinalValues(BaseModel):
    short_up: int | None = None
    short_down: int | None = None
    long_up: int | None = None
    long_down: int | None = None


class LevelingHysteresisSummary(BaseModel):
    short_up_vs_down_mm: int | None = None
    short_up_vs_down_ok: bool | None = None
    long_up_vs_down_mm: int | None = None
    long_up_vs_down_ok: bool | None = None
    short_vs_long_up_mm: int | None = None
    short_vs_long_up_ok: bool | None = None
    short_vs_long_down_mm: int | None = None
    short_vs_long_down_ok: bool | None = None
    max_difference_mm: int | None = None
    overall_ok: bool | None = None


class LevelingFloorSummary(BaseModel):
    floor_id: UUID
    floor_label: str
    sort_order: int
    is_served: bool
    is_leveling_required: bool
    measurements_count: int
    final_values_mm: LevelingFinalValues
    within_final_tolerance: bool | None
    has_out_of_tolerance_measurement: bool
    has_renivelation: bool
    renivelation_ok: bool | None
    hysteresis: LevelingHysteresisSummary
    status: str


class LevelingSummaryRead(BaseModel):
    test_run_id: UUID
    elevator_id: UUID
    measurement_count: int
    required_floor_count: int
    measured_required_floor_count: int
    coverage_percentage: float
    within_final_tolerance_count: int
    within_final_tolerance_percentage: float
    out_of_final_tolerance_count: int
    renivelation_count: int
    acceptable_renivelation_count: int
    acceptable_renivelation_percentage: float
    hysteresis_pairs_count: int
    hysteresis_ok_count: int
    hysteresis_ok_percentage: float
    overall_status: str
    floor_summaries: list[LevelingFloorSummary]
