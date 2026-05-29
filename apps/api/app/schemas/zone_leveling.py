from uuid import UUID

from pydantic import BaseModel


class ZoneLevelingParameterSuggestion(BaseModel):
    code: str
    current_hex: str | None
    current_decimal: int | None
    suggested_decimal: int | None
    suggested_hex: str | None


class ZoneLevelingWarning(BaseModel):
    type: str
    severity: str = "warning"
    message: str


class ZoneLevelingEntry(BaseModel):
    zone: str
    direction: str
    floor_range_label: str
    measurement_count: int
    average_landing_mm: float | None
    rounded_delta_decimal: int | None
    min_parameter: ZoneLevelingParameterSuggestion
    max_parameter: ZoneLevelingParameterSuggestion
    current_window_decimal: int | None
    suggested_window_decimal: int | None
    warnings: list[ZoneLevelingWarning]
    status: str


class ZoneLevelingAnalysisRead(BaseModel):
    test_run_id: UUID
    elevator_id: UUID
    zones: list[ZoneLevelingEntry]
    global_warnings: list[ZoneLevelingWarning] = []
