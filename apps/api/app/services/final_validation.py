from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import CommissioningStep, CommissioningWorkflow, ElevatorFloor, LevelingMeasurement, TestRun
from app.services.leveling_summary import FINAL_TOLERANCE_MM

FINAL_VALIDATION_STAGE = "final_validation"


async def get_final_validation_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    test_run = await session.get(TestRun, test_run_id)
    if test_run is None:
        raise NotFoundError("Test run not found")

    floors = list(
        await session.scalars(
            select(ElevatorFloor)
            .where(
                ElevatorFloor.elevator_id == test_run.elevator_id,
                ElevatorFloor.is_served.is_(True),
                ElevatorFloor.is_leveling_required.is_(True),
            )
            .order_by(ElevatorFloor.sort_order.asc())
        )
    )
    measurements = list(
        await session.scalars(
            select(LevelingMeasurement)
            .where(
                LevelingMeasurement.test_run_id == test_run_id,
                LevelingMeasurement.measurement_stage == FINAL_VALIDATION_STAGE,
            )
            .order_by(LevelingMeasurement.updated_at.asc(), LevelingMeasurement.created_at.asc())
        )
    )
    fhm_step_status = await _get_fhm_step_status(session, test_run.elevator_id)
    latest_by_floor_direction = _latest_final_measurements_by_floor_direction(measurements)
    rows = [_build_row(floor, latest_by_floor_direction) for floor in floors]

    complete_rows = [row for row in rows if row["status"] in {"ok", "out_of_tolerance"}]
    ok_rows = [row for row in rows if row["status"] == "ok"]
    out_rows = [row for row in rows if row["status"] == "out_of_tolerance"]
    missing_rows = [row for row in rows if row["status"] == "missing_data"]
    partial_rows = [row for row in rows if row["status"] == "partial_data"]
    final_values = [
        abs(value)
        for row in rows
        for value in (row["down_final_mm"], row["up_final_mm"])
        if value is not None
    ]

    return {
        "test_run_id": test_run.id,
        "elevator_id": test_run.elevator_id,
        "tolerance_mm": float(FINAL_TOLERANCE_MM),
        "fhm_completed": fhm_step_status == "completed",
        "fhm_step_status": fhm_step_status,
        "summary": {
            "total_required_floors": len(floors),
            "floors_with_complete_data": len(complete_rows),
            "floors_within_tolerance": len(ok_rows),
            "floors_out_of_tolerance": len(out_rows),
            "floors_missing_data": len(missing_rows),
            "floors_partial_data": len(partial_rows),
            "completion_percent": _percentage(len(complete_rows), len(floors)),
            "within_tolerance_percent": _percentage(len(ok_rows), len(complete_rows)),
            "max_abs_final_mm": max(final_values) if final_values else None,
        },
        "rows": rows,
    }


async def _get_fhm_step_status(session: AsyncSession, elevator_id: UUID) -> str | None:
    return await session.scalar(
        select(CommissioningStep.status)
        .join(CommissioningWorkflow, CommissioningStep.workflow_id == CommissioningWorkflow.id)
        .where(CommissioningWorkflow.elevator_id == elevator_id, CommissioningStep.code == "FHM_RUN")
        .limit(1)
    )


def _latest_final_measurements_by_floor_direction(measurements: list[LevelingMeasurement]) -> dict[tuple[UUID, str], LevelingMeasurement]:
    latest: dict[tuple[UUID, str], LevelingMeasurement] = {}
    for measurement in measurements:
        if measurement.final_mm is None:
            continue
        latest[(measurement.destination_floor_id, measurement.direction)] = measurement
    return latest


def _build_row(floor: ElevatorFloor, latest_by_floor_direction: dict[tuple[UUID, str], LevelingMeasurement]) -> dict:
    down_measurement = latest_by_floor_direction.get((floor.id, "down"))
    up_measurement = latest_by_floor_direction.get((floor.id, "up"))
    down_final = float(down_measurement.final_mm) if down_measurement else None
    up_final = float(up_measurement.final_mm) if up_measurement else None

    if down_final is None and up_final is None:
        status = "missing_data"
        within_tolerance = None
    elif down_final is None or up_final is None:
        status = "partial_data"
        within_tolerance = None
    elif _within_tolerance(down_final) and _within_tolerance(up_final):
        status = "ok"
        within_tolerance = True
    else:
        status = "out_of_tolerance"
        within_tolerance = False

    return {
        "floor_id": floor.id,
        "floor_label": floor.label or str(floor.sort_order),
        "sort_order": floor.sort_order,
        "down_final_mm": down_final,
        "up_final_mm": up_final,
        "status": status,
        "within_tolerance": within_tolerance,
    }


def _within_tolerance(value: float) -> bool:
    return -FINAL_TOLERANCE_MM <= value <= FINAL_TOLERANCE_MM


def _percentage(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0
