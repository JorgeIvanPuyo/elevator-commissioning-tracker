from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.db.models import TestRun, TestType
from app.schemas.test_run import TestRunCreate, TestRunUpdate
from app.services.elevators import get_elevator


async def create_test_run(session: AsyncSession, elevator_id: UUID, payload: TestRunCreate) -> dict:
    await get_elevator(session, elevator_id)
    await _get_test_type(session, payload.test_type_id)

    test_run = TestRun(elevator_id=elevator_id, **payload.model_dump())
    session.add(test_run)
    await session.commit()
    await session.refresh(test_run)
    return await get_test_run(session, test_run.id)


async def list_elevator_test_runs(
    session: AsyncSession,
    elevator_id: UUID,
    limit: int,
    offset: int,
    test_type_code: str | None = None,
    status: str | None = None,
) -> list[dict]:
    await get_elevator(session, elevator_id)
    query = (
        select(TestRun, TestType)
        .join(TestType, TestRun.test_type_id == TestType.id)
        .where(TestRun.elevator_id == elevator_id)
        .order_by(TestRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if test_type_code is not None:
        query = query.where(TestType.code == test_type_code)
    if status is not None:
        _validate_status(status)
        query = query.where(TestRun.status == status)

    rows = (await session.execute(query)).all()
    return [_serialize_test_run(test_run, test_type) for test_run, test_type in rows]


async def get_test_run(session: AsyncSession, test_run_id: UUID) -> dict:
    row = (
        await session.execute(
            select(TestRun, TestType).join(TestType, TestRun.test_type_id == TestType.id).where(TestRun.id == test_run_id)
        )
    ).one_or_none()
    if row is None:
        raise NotFoundError("Test run not found")
    test_run, test_type = row
    return _serialize_test_run(test_run, test_type)


async def get_test_run_model(session: AsyncSession, test_run_id: UUID) -> TestRun:
    test_run = await session.get(TestRun, test_run_id)
    if test_run is None:
        raise NotFoundError("Test run not found")
    return test_run


async def update_test_run(session: AsyncSession, test_run_id: UUID, payload: TestRunUpdate) -> dict:
    test_run = await get_test_run_model(session, test_run_id)
    data = payload.model_dump(exclude_unset=True)
    if "test_type_id" in data:
        await _get_test_type(session, data["test_type_id"])

    for field, value in data.items():
        setattr(test_run, field, value)

    await session.commit()
    await session.refresh(test_run)
    return await get_test_run(session, test_run.id)


async def delete_test_run(session: AsyncSession, test_run_id: UUID) -> None:
    test_run = await get_test_run_model(session, test_run_id)
    await session.delete(test_run)
    await session.commit()


async def _get_test_type(session: AsyncSession, test_type_id: UUID) -> TestType:
    test_type = await session.get(TestType, test_type_id)
    if test_type is None:
        raise NotFoundError("Test type not found")
    return test_type


def _validate_status(status: str) -> None:
    if status not in {"draft", "in_progress", "completed", "cancelled"}:
        raise AppError("Invalid test run status")


def _serialize_test_run(test_run: TestRun, test_type: TestType) -> dict:
    return {
        "id": test_run.id,
        "elevator_id": test_run.elevator_id,
        "test_type_id": test_run.test_type_id,
        "test_type_code": test_type.code,
        "test_type_name": test_type.name,
        "status": test_run.status,
        "technician_name": test_run.technician_name,
        "started_at": test_run.started_at,
        "completed_at": test_run.completed_at,
        "title": test_run.title,
        "summary": test_run.summary,
        "notes": test_run.notes,
        "created_at": test_run.created_at,
        "updated_at": test_run.updated_at,
    }
