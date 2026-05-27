from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import TestRun, TestRunProcessStep
from app.schemas.process_step import TestRunProcessStepUpdate


PROCESS_STEP_SEED_DATA = [
    {
        "code": "A61E",
        "name": "Calibración 0% de carga",
        "description": "Proceso de calibración de potenciómetros a 0% de carga.",
    },
    {
        "code": "A62E",
        "name": "Calibración 100% de carga",
        "description": "Proceso de calibración de potenciómetros a 100% de carga.",
    },
    {
        "code": "A65E",
        "name": "Nivelación automática sin carga",
        "description": "Proceso automático de nivelación sin carga / 0% de carga.",
    },
    {
        "code": "A66E",
        "name": "Nivelación automática con 100% de carga",
        "description": "Proceso automático de nivelación con 100% de carga.",
    },
    {
        "code": "A67E",
        "name": "Compensación automática de carga",
        "description": "Proceso automático de compensación de carga.",
    },
]


async def create_default_process_steps(session: AsyncSession, test_run_id: UUID) -> None:
    for item in PROCESS_STEP_SEED_DATA:
        session.add(TestRunProcessStep(test_run_id=test_run_id, **item, is_completed=False))


async def list_test_run_process_steps(session: AsyncSession, test_run_id: UUID) -> list[TestRunProcessStep]:
    test_run = await session.get(TestRun, test_run_id)
    if test_run is None:
        raise NotFoundError("Test run not found")
    result = await session.scalars(
        select(TestRunProcessStep)
        .where(TestRunProcessStep.test_run_id == test_run_id)
        .order_by(TestRunProcessStep.code.asc())
    )
    return list(result)


async def get_process_step(session: AsyncSession, process_step_id: UUID) -> TestRunProcessStep:
    process_step = await session.get(TestRunProcessStep, process_step_id)
    if process_step is None:
        raise NotFoundError("Test run process step not found")
    return process_step


async def update_process_step(
    session: AsyncSession,
    process_step_id: UUID,
    payload: TestRunProcessStepUpdate,
) -> TestRunProcessStep:
    process_step = await get_process_step(session, process_step_id)
    data = payload.model_dump(exclude_unset=True)

    if data.get("is_completed") is True and data.get("completed_at") is None and process_step.completed_at is None:
        data["completed_at"] = datetime.now(UTC)
    if data.get("is_completed") is False:
        data.setdefault("completed_at", None)

    for field, value in data.items():
        setattr(process_step, field, value)

    await session.commit()
    await session.refresh(process_step)
    return process_step
