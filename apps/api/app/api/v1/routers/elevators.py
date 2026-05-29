from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.commissioning_overview import CommissioningOverviewRead
from app.schemas.elevator import ElevatorCreate, ElevatorListItem, ElevatorRead, ElevatorUpdate
from app.services import commissioning_overview as commissioning_overview_service
from app.services import elevators as elevator_service

router = APIRouter(tags=["elevators"])


@router.post("/projects/{project_id}/elevators", response_model=ElevatorRead, status_code=201)
async def create_elevator(
    project_id: UUID,
    payload: ElevatorCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorRead:
    try:
        return await elevator_service.create_elevator(session, project_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/projects/{project_id}/elevators", response_model=list[ElevatorRead])
async def list_project_elevators(
    project_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[ElevatorRead]:
    try:
        return await elevator_service.list_project_elevators(session, project_id, limit=limit, offset=offset)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/elevators", response_model=list[ElevatorListItem])
async def list_elevators(
    project_id: UUID | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[ElevatorListItem]:
    return await elevator_service.list_elevators(
        session,
        limit=limit,
        offset=offset,
        project_id=project_id,
        status=status,
        search=search,
    )


@router.get("/elevators/{elevator_id}", response_model=ElevatorRead)
async def get_elevator(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorRead:
    try:
        return await elevator_service.get_elevator(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/elevators/{elevator_id}/commissioning-overview", response_model=CommissioningOverviewRead)
async def get_commissioning_overview(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CommissioningOverviewRead:
    try:
        return await commissioning_overview_service.get_commissioning_overview(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/elevators/{elevator_id}", response_model=ElevatorRead)
async def update_elevator(
    elevator_id: UUID,
    payload: ElevatorUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorRead:
    try:
        return await elevator_service.update_elevator(session, elevator_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.delete("/elevators/{elevator_id}", status_code=204)
async def delete_elevator(
    elevator_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await elevator_service.delete_elevator(session, elevator_id)
    except AppError as error:
        raise to_http_exception(error) from error
    return Response(status_code=204)
