from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OverviewElevator(BaseModel):
    id: UUID
    code: str
    name: str | None
    project_id: UUID
    project_name: str
    status: str


class OverviewWorkflowStep(BaseModel):
    code: str
    title: str
    status: str
    is_required: bool
    completed_at: datetime | None
    notes: str | None = None


class OverviewWorkflow(BaseModel):
    id: UUID
    status: str
    progress_percent: float
    completed_steps: int
    total_steps: int
    critical_blockers: list[str]
    steps: list[OverviewWorkflowStep]


class OverviewLatestTestRun(BaseModel):
    id: UUID
    name: str
    status: str
    technician_name: str
    created_at: datetime


class OverviewLoadReadiness(BaseModel):
    mechanical_calibration_completed: bool
    zero_full_memory_completed: bool
    overload_110_completed: bool
    ready_for_leveling: bool
    warnings: list[str]


class OverviewParameterMatrix(BaseModel):
    ok_windows: int
    warning_windows: int
    missing_windows: int
    most_critical_warning: str | None


class OverviewZoneAnalysis(BaseModel):
    available: bool
    rows_count: int
    warnings_count: int
    max_abs_average_landing_mm: float | None


class OverviewFlagAdjustments(BaseModel):
    available: bool
    floors_requiring_adjustment: int
    floors_ok: int
    floors_missing_data: int
    max_abs_recommended_movement_mm: float | None


class OverviewFinalValidation(BaseModel):
    available: bool
    fhm_completed: bool
    floors_within_tolerance: int
    floors_out_of_tolerance: int
    floors_missing_data: int
    within_tolerance_percent: float
    ready_to_close: bool


class OverviewOverallStatus(BaseModel):
    status: str
    label: str
    reasons: list[str]


class CommissioningOverviewRead(BaseModel):
    elevator: OverviewElevator
    workflow: OverviewWorkflow | None
    latest_test_run: OverviewLatestTestRun | None
    load_readiness: OverviewLoadReadiness
    parameter_matrix: OverviewParameterMatrix
    zone_analysis: OverviewZoneAnalysis
    flag_adjustments: OverviewFlagAdjustments
    final_validation: OverviewFinalValidation
    overall_status: OverviewOverallStatus
