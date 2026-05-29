from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

WorkflowStatus = Literal["not_started", "in_progress", "completed", "blocked", "cancelled"]
StepStatus = Literal["pending", "in_progress", "completed", "skipped", "not_applicable", "blocked"]


class CommissioningStepRead(BaseModel):
    id: UUID
    workflow_id: UUID
    code: str
    title: str
    description: str | None
    status: str
    is_required: bool
    is_blocking: bool
    sort_order: int
    completed_at: datetime | None
    technician_name: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommissioningWorkflowRead(BaseModel):
    id: UUID
    elevator_id: UUID
    status: str
    technician_name: str | None
    started_at: datetime | None
    completed_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    steps: list[CommissioningStepRead] = []

    model_config = ConfigDict(from_attributes=True)


class CommissioningWorkflowUpdate(BaseModel):
    status: WorkflowStatus | None = None
    technician_name: str | None = Field(default=None, max_length=160)
    notes: str | None = None


class CommissioningStepUpdate(BaseModel):
    status: StepStatus | None = None
    technician_name: str | None = Field(default=None, max_length=160)
    notes: str | None = None
    completed_at: datetime | None = None


class OperationalProjectBrief(BaseModel):
    id: UUID
    name: str
    client_name: str | None
    location: str | None


class OperationalElevatorBrief(BaseModel):
    id: UUID
    project_id: UUID
    code: str
    name: str | None
    status: str
    floor_count: int
    controller_model: str | None
    machine_room: str | None


class OperationalWorkflowSummary(BaseModel):
    id: UUID
    status: str
    technician_name: str | None
    total_steps: int
    completed_steps: int
    required_steps: int
    required_pending_steps: int
    required_blocking_steps_incomplete: int
    progress_percentage: float


class OperationalLatestTestRun(BaseModel):
    id: UUID
    title: str | None
    name: str
    status: str
    test_type_code: str
    test_type_name: str
    technician_name: str
    created_at: datetime
    updated_at: datetime


class OperationalLevelingSummary(BaseModel):
    test_run_id: UUID
    measurement_count: int
    required_floor_count: int
    measured_required_floor_count: int
    coverage_percentage: float
    within_final_tolerance_percentage: float
    overall_status: str


class OperationalParameterValue(BaseModel):
    parameter_code: str
    parameter_name: str
    hex_value: str | None
    decimal_value: int | None


class OperationalParameterSummary(BaseModel):
    latest_test_run_id: UUID | None
    warning_count: int
    critical_values: list[OperationalParameterValue]


class OperationalQuickLinks(BaseModel):
    latest_test_run_id: UUID | None
    project_id: UUID
    elevator_id: UUID


class ElevatorOperationalDashboardRead(BaseModel):
    elevator: OperationalElevatorBrief
    project: OperationalProjectBrief
    workflow: OperationalWorkflowSummary | None
    latest_test_run: OperationalLatestTestRun | None
    leveling_summary: OperationalLevelingSummary | None
    parameter_summary: OperationalParameterSummary
    quick_links: OperationalQuickLinks
