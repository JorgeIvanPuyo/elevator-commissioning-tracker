from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import ElevatorFloor, LevelingMeasurement, TestRun
from app.services.leveling_summary import FINAL_TOLERANCE_MM


async def get_flag_adjustment_recommendations(session: AsyncSession, test_run_id: UUID) -> dict:
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
            .where(LevelingMeasurement.test_run_id == test_run_id)
            .order_by(LevelingMeasurement.updated_at.asc(), LevelingMeasurement.created_at.asc())
        )
    )

    latest_by_floor_direction = _latest_final_measurements_by_floor_direction(measurements)
    rows = [_build_row(floor, latest_by_floor_direction) for floor in floors]

    complete_rows = [row for row in rows if row["status"] in {"ok", "requires_adjustment"}]
    adjustment_rows = [row for row in rows if row["status"] == "requires_adjustment"]
    missing_rows = [row for row in rows if row["status"] == "missing_data"]
    partial_rows = [row for row in rows if row["status"] == "partial_data"]
    movements = [
        abs(row["recommended_flag_movement_mm"])
        for row in rows
        if row["recommended_flag_movement_mm"] is not None
    ]

    return {
        "test_run_id": test_run.id,
        "elevator_id": test_run.elevator_id,
        "tolerance_mm": float(FINAL_TOLERANCE_MM),
        "summary": {
            "total_required_floors": len(floors),
            "floors_with_complete_data": len(complete_rows),
            "floors_within_tolerance": len([row for row in rows if row["status"] == "ok"]),
            "floors_requiring_flag_adjustment": len(adjustment_rows),
            "floors_missing_data": len(missing_rows),
            "floors_partial_data": len(partial_rows),
            "max_abs_recommended_movement_mm": max(movements) if movements else None,
        },
        "rows": rows,
    }


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
        return _base_row(floor, down_final, up_final, None, None, "missing_data", None, ["Sin mediciones finales de subida ni bajada."])

    if down_final is None or up_final is None:
        return _base_row(floor, down_final, up_final, None, None, "partial_data", None, ["Falta una dirección para calcular movimiento completo."])

    within_tolerance = _within_tolerance(down_final) and _within_tolerance(up_final)
    if within_tolerance:
        average_final = (down_final + up_final) / 2
        return _base_row(floor, down_final, up_final, average_final, 0.0, "ok", True, [])

    average_final = (down_final + up_final) / 2
    recommended = _round_to_half_mm(-average_final)
    return _base_row(floor, down_final, up_final, average_final, recommended, "requires_adjustment", False, [])


def _base_row(
    floor: ElevatorFloor,
    down_final: float | None,
    up_final: float | None,
    average_final: float | None,
    recommended_movement: float | None,
    status: str,
    within_tolerance: bool | None,
    notes: list[str],
) -> dict:
    return {
        "floor_id": floor.id,
        "floor_label": floor.label or str(floor.sort_order),
        "sort_order": floor.sort_order,
        "down_final_mm": down_final,
        "up_final_mm": up_final,
        "average_final_mm": _round_to_half_mm(average_final) if average_final is not None else None,
        "recommended_flag_movement_mm": recommended_movement,
        "status": status,
        "within_tolerance": within_tolerance,
        "notes": notes,
    }


def _within_tolerance(value: float) -> bool:
    return -FINAL_TOLERANCE_MM <= value <= FINAL_TOLERANCE_MM


def _round_to_half_mm(value: float) -> float:
    return round(value * 2) / 2
