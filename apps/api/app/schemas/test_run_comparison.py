from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ComparisonTestRunBrief(BaseModel):
    id: UUID
    title: str | None
    name: str
    test_type_code: str
    test_type_name: str
    status: str
    technician_name: str
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


class ComparisonCandidateRead(ComparisonTestRunBrief):
    coverage_percentage: float
    within_final_tolerance_percentage: float
    acceptable_renivelation_percentage: float


class ComparisonMetricRead(BaseModel):
    metric: str
    label: str
    baseline_value: float | int | None
    current_value: float | int | None
    delta: float | int | None
    trend: str


class FloorComparisonRead(BaseModel):
    floor_id: UUID
    floor_label: str
    baseline_status: str
    current_status: str
    baseline_final_mm: int | None
    current_final_mm: int | None
    absolute_delta_mm: int | None
    trend: str


class ParameterComparisonRead(BaseModel):
    parameter_code: str
    name: str
    baseline_hex_value: str | None
    baseline_decimal_value: int | None
    current_hex_value: str | None
    current_decimal_value: int | None
    decimal_delta: int | None
    changed: bool
    warning: str | None = None


class TestRunComparisonRead(BaseModel):
    baseline_test_run: ComparisonTestRunBrief
    current_test_run: ComparisonTestRunBrief
    global_metrics: list[ComparisonMetricRead]
    floor_comparisons: list[FloorComparisonRead]
    parameter_comparisons: list[ParameterComparisonRead]
    overall_trend: str
    summary_text: str
