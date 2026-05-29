from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.commissioning import (
    CommissioningStepRead,
    CommissioningStepUpdate,
    CommissioningWorkflowRead,
    CommissioningWorkflowUpdate,
    ElevatorOperationalDashboardRead,
)
from app.services import commissioning as commissioning_service

router = APIRouter(tags=["commissioning"])


@router.get("/elevators/{elevator_id}/commissioning-workflow", response_model=CommissioningWorkflowRead)
async def get_elevator_commissioning_workflow(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CommissioningWorkflowRead:
    try:
        return await commissioning_service.get_workflow_for_elevator(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.post("/elevators/{elevator_id}/commissioning-workflow/initialize", response_model=CommissioningWorkflowRead, status_code=201)
async def initialize_elevator_commissioning_workflow(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CommissioningWorkflowRead:
    try:
        return await commissioning_service.initialize_workflow_for_elevator(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/commissioning-workflows/{workflow_id}", response_model=CommissioningWorkflowRead)
async def update_commissioning_workflow(
    workflow_id: UUID,
    payload: CommissioningWorkflowUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> CommissioningWorkflowRead:
    try:
        return await commissioning_service.update_workflow(session, workflow_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/commissioning-steps/{step_id}", response_model=CommissioningStepRead)
async def update_commissioning_step(
    step_id: UUID,
    payload: CommissioningStepUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> CommissioningStepRead:
    try:
        return await commissioning_service.update_step(session, step_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/elevators/{elevator_id}/operational-dashboard", response_model=ElevatorOperationalDashboardRead)
async def get_elevator_operational_dashboard(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorOperationalDashboardRead:
    try:
        return await commissioning_service.get_operational_dashboard(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error
