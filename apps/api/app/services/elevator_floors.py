from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models import ElevatorFloor
from app.schemas.elevator_floor import ElevatorFloorCreate, ElevatorFloorUpdate
from app.services.elevators import get_elevator


async def create_elevator_floor(session: AsyncSession, elevator_id: UUID, payload: ElevatorFloorCreate) -> ElevatorFloor:
    await get_elevator(session, elevator_id)
    label = _normalize_label(payload.label)
    await _ensure_sort_order_available(session, elevator_id, payload.sort_order)
    if label:
        await _ensure_label_available(session, elevator_id, label)

    floor = ElevatorFloor(elevator_id=elevator_id, **payload.model_dump(exclude={"label"}), label=label)
    session.add(floor)
    await session.commit()
    await session.refresh(floor)
    return floor


async def list_elevator_floors(session: AsyncSession, elevator_id: UUID, limit: int, offset: int) -> list[ElevatorFloor]:
    await get_elevator(session, elevator_id)
    result = await session.scalars(
        select(ElevatorFloor)
        .where(ElevatorFloor.elevator_id == elevator_id)
        .order_by(ElevatorFloor.sort_order.asc())
        .limit(limit)
        .offset(offset)
    )
    return list(result)


async def get_elevator_floor(session: AsyncSession, floor_id: UUID) -> ElevatorFloor:
    floor = await session.get(ElevatorFloor, floor_id)
    if floor is None:
        raise NotFoundError("Elevator floor not found")
    return floor


async def update_elevator_floor(session: AsyncSession, floor_id: UUID, payload: ElevatorFloorUpdate) -> ElevatorFloor:
    floor = await get_elevator_floor(session, floor_id)
    data = payload.model_dump(exclude_unset=True)

    new_sort_order = data.get("sort_order")
    if new_sort_order is not None and new_sort_order != floor.sort_order:
        await _ensure_sort_order_available(session, floor.elevator_id, new_sort_order, exclude_floor_id=floor.id)

    if "label" in data:
        data["label"] = _normalize_label(data["label"])
        if data["label"] and data["label"] != floor.label:
            await _ensure_label_available(session, floor.elevator_id, data["label"], exclude_floor_id=floor.id)

    if data.get("is_served") is False:
        data.setdefault("is_leveling_required", False)

    for field, value in data.items():
        setattr(floor, field, value)

    await session.commit()
    await session.refresh(floor)
    return floor


async def delete_elevator_floor(session: AsyncSession, floor_id: UUID) -> None:
    floor = await get_elevator_floor(session, floor_id)
    await session.delete(floor)
    await session.commit()


async def create_default_elevator_floors(session: AsyncSession, elevator_id: UUID, floor_count: int) -> None:
    for floor_number in range(1, floor_count + 1):
        session.add(
            ElevatorFloor(
                elevator_id=elevator_id,
                sort_order=floor_number,
                label=str(floor_number),
                is_served=True,
                is_leveling_required=True,
            )
        )


async def _ensure_sort_order_available(
    session: AsyncSession,
    elevator_id: UUID,
    sort_order: int,
    exclude_floor_id: UUID | None = None,
) -> None:
    query = select(ElevatorFloor).where(ElevatorFloor.elevator_id == elevator_id, ElevatorFloor.sort_order == sort_order)
    if exclude_floor_id is not None:
        query = query.where(ElevatorFloor.id != exclude_floor_id)
    existing = await session.scalar(query)
    if existing is not None:
        raise ConflictError("Elevator floor sort_order already exists for this elevator")


async def _ensure_label_available(
    session: AsyncSession,
    elevator_id: UUID,
    label: str,
    exclude_floor_id: UUID | None = None,
) -> None:
    query = select(ElevatorFloor).where(ElevatorFloor.elevator_id == elevator_id, ElevatorFloor.label == label)
    if exclude_floor_id is not None:
        query = query.where(ElevatorFloor.id != exclude_floor_id)
    existing = await session.scalar(query)
    if existing is not None:
        raise ConflictError("Elevator floor label already exists for this elevator")


def _normalize_label(label: str | None) -> str | None:
    if label is None:
        return None
    normalized = label.strip()
    return normalized or None
