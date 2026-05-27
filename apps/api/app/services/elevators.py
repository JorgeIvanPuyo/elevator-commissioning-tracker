from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models import Elevator, ElevatorFloor
from app.schemas.elevator import ElevatorCreate, ElevatorUpdate
from app.services.projects import get_project


async def create_elevator(session: AsyncSession, project_id: UUID, payload: ElevatorCreate) -> Elevator:
    project = await get_project(session, project_id)
    await _ensure_code_available(session, project_id, payload.code)

    data = payload.model_dump()
    if data["floor_count"] is None:
        data["floor_count"] = project.default_floor_count

    elevator = Elevator(project_id=project_id, **data)
    session.add(elevator)
    await session.flush()
    for floor_number in range(1, elevator.floor_count + 1):
        session.add(
            ElevatorFloor(
                elevator_id=elevator.id,
                sort_order=floor_number,
                label=str(floor_number),
                is_served=True,
                is_leveling_required=True,
            )
        )
    await session.commit()
    await session.refresh(elevator)
    return elevator


async def list_project_elevators(session: AsyncSession, project_id: UUID, limit: int, offset: int) -> list[Elevator]:
    await get_project(session, project_id)
    result = await session.scalars(
        select(Elevator)
        .where(Elevator.project_id == project_id)
        .order_by(Elevator.code.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


async def get_elevator(session: AsyncSession, elevator_id: UUID) -> Elevator:
    elevator = await session.get(Elevator, elevator_id)
    if elevator is None:
        raise NotFoundError("Elevator not found")
    return elevator


async def update_elevator(session: AsyncSession, elevator_id: UUID, payload: ElevatorUpdate) -> Elevator:
    elevator = await get_elevator(session, elevator_id)
    data = payload.model_dump(exclude_unset=True)

    new_code = data.get("code")
    if new_code is not None and new_code != elevator.code:
        await _ensure_code_available(session, elevator.project_id, new_code, exclude_elevator_id=elevator.id)

    for field, value in data.items():
        setattr(elevator, field, value)

    await session.commit()
    await session.refresh(elevator)
    return elevator


async def delete_elevator(session: AsyncSession, elevator_id: UUID) -> None:
    elevator = await get_elevator(session, elevator_id)
    await session.delete(elevator)
    await session.commit()


async def _ensure_code_available(
    session: AsyncSession,
    project_id: UUID,
    code: str,
    exclude_elevator_id: UUID | None = None,
) -> None:
    query = select(Elevator).where(Elevator.project_id == project_id, Elevator.code == code)
    if exclude_elevator_id is not None:
        query = query.where(Elevator.id != exclude_elevator_id)
    existing = await session.scalar(query)
    if existing is not None:
        raise ConflictError("Elevator code already exists for this project")
