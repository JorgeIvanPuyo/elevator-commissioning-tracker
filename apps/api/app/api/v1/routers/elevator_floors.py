from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.elevator_floor import ElevatorFloorCreate, ElevatorFloorRead, ElevatorFloorUpdate
from app.services import elevator_floors as floor_service

router = APIRouter(tags=["elevator-floors"])


@router.get("/elevators/{elevator_id}/floors", response_model=list[ElevatorFloorRead])
async def list_elevator_floors(
    elevator_id: UUID,
    limit: int = Query(default=100, ge=1, le=300),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[ElevatorFloorRead]:
    try:
        return await floor_service.list_elevator_floors(session, elevator_id, limit=limit, offset=offset)
    except AppError as error:
        raise to_http_exception(error) from error


@router.post("/elevators/{elevator_id}/floors", response_model=ElevatorFloorRead, status_code=201)
async def create_elevator_floor(
    elevator_id: UUID,
    payload: ElevatorFloorCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorFloorRead:
    try:
        return await floor_service.create_elevator_floor(session, elevator_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/elevator-floors/{floor_id}", response_model=ElevatorFloorRead)
async def update_elevator_floor(
    floor_id: UUID,
    payload: ElevatorFloorUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ElevatorFloorRead:
    try:
        return await floor_service.update_elevator_floor(session, floor_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.delete("/elevator-floors/{floor_id}", status_code=204)
async def delete_elevator_floor(
    floor_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await floor_service.delete_elevator_floor(session, floor_id)
    except AppError as error:
        raise to_http_exception(error) from error
    return Response(status_code=204)
