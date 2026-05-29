from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardLatestProject(BaseModel):
    id: UUID
    name: str
    status: str
    elevators_count: int
    created_at: datetime
    updated_at: datetime


class DashboardLatestTestRun(BaseModel):
    id: UUID
    title: str | None
    name: str
    test_type: str
    status: str
    elevator_id: UUID
    elevator_code: str
    project_id: UUID
    project_name: str
    responsible_technician: str
    created_at: datetime
    updated_at: datetime


class DashboardOverviewRead(BaseModel):
    projects_count: int
    active_projects_count: int
    elevators_count: int
    test_runs_count: int
    completed_test_runs_count: int
    in_progress_test_runs_count: int
    draft_test_runs_count: int
    latest_test_runs: list[DashboardLatestTestRun]
    latest_projects: list[DashboardLatestProject]
