from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import ElevatorFloor, LevelingMeasurement, TestRun

FINAL_TOLERANCE_MM = 5
CRITICAL_FINAL_MM = 10
RENIVELATION_DELTA_TOLERANCE_MM = 10
HYSTERESIS_TOLERANCE_MM = 5

ScenarioKey = str


async def get_leveling_summary(session: AsyncSession, test_run_id: UUID) -> dict:
    test_run = await session.get(TestRun, test_run_id)
    if test_run is None:
        raise NotFoundError("Test run not found")

    floors = list(
        await session.scalars(
            select(ElevatorFloor)
            .where(ElevatorFloor.elevator_id == test_run.elevator_id)
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

    measurements_with_values = [measurement for measurement in measurements if measurement.effective_final_mm is not None]
    measurements_by_floor = _group_measurements_by_destination(measurements_with_values)
    required_floors = [floor for floor in floors if floor.is_served and floor.is_leveling_required]

    floor_summaries = [_build_floor_summary(floor, measurements_by_floor.get(floor.id, [])) for floor in floors]
    required_floor_ids = {floor.id for floor in required_floors}
    measured_required_floor_ids = {
        floor_id for floor_id, floor_measurements in measurements_by_floor.items() if floor_id in required_floor_ids and floor_measurements
    }

    within_final_tolerance_count = len([measurement for measurement in measurements_with_values if measurement.is_final_within_tolerance is True])
    out_of_final_tolerance_count = len([measurement for measurement in measurements_with_values if measurement.is_final_within_tolerance is False])
    renivelation_measurements = [measurement for measurement in measurements_with_values if measurement.renivelation_occurred]
    acceptable_renivelation_count = len([measurement for measurement in renivelation_measurements if _renivelation_is_acceptable(measurement)])
    hysteresis_pairs = _collect_hysteresis_pairs(floor_summaries)
    overall_status = _overall_status(floor_summaries, measured_required_floor_ids)

    return {
        "test_run_id": test_run.id,
        "elevator_id": test_run.elevator_id,
        "measurement_count": len(measurements_with_values),
        "required_floor_count": len(required_floors),
        "measured_required_floor_count": len(measured_required_floor_ids),
        "coverage_percentage": _percentage(len(measured_required_floor_ids), len(required_floors)),
        "within_final_tolerance_count": within_final_tolerance_count,
        "within_final_tolerance_percentage": _percentage(within_final_tolerance_count, len(measurements_with_values)),
        "out_of_final_tolerance_count": out_of_final_tolerance_count,
        "renivelation_count": len(renivelation_measurements),
        "acceptable_renivelation_count": acceptable_renivelation_count,
        "acceptable_renivelation_percentage": _percentage(acceptable_renivelation_count, len(renivelation_measurements)),
        "hysteresis_pairs_count": len(hysteresis_pairs),
        "hysteresis_ok_count": len([pair_ok for pair_ok in hysteresis_pairs if pair_ok]),
        "hysteresis_ok_percentage": _percentage(len([pair_ok for pair_ok in hysteresis_pairs if pair_ok]), len(hysteresis_pairs)),
        "overall_status": overall_status,
        "floor_summaries": floor_summaries,
    }


def _group_measurements_by_destination(measurements: list[LevelingMeasurement]) -> dict[UUID, list[LevelingMeasurement]]:
    grouped: dict[UUID, list[LevelingMeasurement]] = {}
    for measurement in measurements:
        grouped.setdefault(measurement.destination_floor_id, []).append(measurement)
    return grouped


def _build_floor_summary(floor: ElevatorFloor, measurements: list[LevelingMeasurement]) -> dict:
    scenario_measurements = _latest_measurements_by_scenario(measurements)
    final_values = {
        "short_up": _scenario_value(scenario_measurements, "short_up"),
        "short_down": _scenario_value(scenario_measurements, "short_down"),
        "long_up": _scenario_value(scenario_measurements, "long_up"),
        "long_down": _scenario_value(scenario_measurements, "long_down"),
    }
    hysteresis = _build_hysteresis(final_values)
    tolerance_values = [measurement.is_final_within_tolerance for measurement in measurements if measurement.is_final_within_tolerance is not None]
    has_out_of_tolerance = any(value is False for value in tolerance_values)
    has_renivelation = any(measurement.renivelation_occurred for measurement in measurements)
    renivelation_measurements = [measurement for measurement in measurements if measurement.renivelation_occurred]
    renivelation_ok = None
    if renivelation_measurements:
        renivelation_ok = all(_renivelation_is_acceptable(measurement) for measurement in renivelation_measurements)

    return {
        "floor_id": floor.id,
        "floor_label": floor.label or str(floor.sort_order),
        "sort_order": floor.sort_order,
        "is_served": floor.is_served,
        "is_leveling_required": floor.is_leveling_required,
        "measurements_count": len(measurements),
        "final_values_mm": final_values,
        "within_final_tolerance": all(tolerance_values) if tolerance_values else None,
        "has_out_of_tolerance_measurement": has_out_of_tolerance,
        "has_renivelation": has_renivelation,
        "renivelation_ok": renivelation_ok,
        "hysteresis": hysteresis,
        "status": _floor_status(floor, measurements, has_out_of_tolerance, renivelation_ok, hysteresis),
    }


def _latest_measurements_by_scenario(measurements: list[LevelingMeasurement]) -> dict[ScenarioKey, LevelingMeasurement]:
    latest: dict[ScenarioKey, LevelingMeasurement] = {}
    for measurement in measurements:
        latest[f"{measurement.travel_type}_{measurement.direction}"] = measurement
    return latest


def _scenario_value(measurements: dict[ScenarioKey, LevelingMeasurement], key: ScenarioKey) -> int | None:
    measurement = measurements.get(key)
    return measurement.effective_final_mm if measurement else None


def _build_hysteresis(final_values: dict[str, int | None]) -> dict:
    pairs = {
        "short_up_vs_down": _difference(final_values["short_up"], final_values["short_down"]),
        "long_up_vs_down": _difference(final_values["long_up"], final_values["long_down"]),
        "short_vs_long_up": _difference(final_values["short_up"], final_values["long_up"]),
        "short_vs_long_down": _difference(final_values["short_down"], final_values["long_down"]),
    }
    pair_values = [value for value in pairs.values() if value is not None]
    pair_results = {key: (value <= HYSTERESIS_TOLERANCE_MM if value is not None else None) for key, value in pairs.items()}

    return {
        "short_up_vs_down_mm": pairs["short_up_vs_down"],
        "short_up_vs_down_ok": pair_results["short_up_vs_down"],
        "long_up_vs_down_mm": pairs["long_up_vs_down"],
        "long_up_vs_down_ok": pair_results["long_up_vs_down"],
        "short_vs_long_up_mm": pairs["short_vs_long_up"],
        "short_vs_long_up_ok": pair_results["short_vs_long_up"],
        "short_vs_long_down_mm": pairs["short_vs_long_down"],
        "short_vs_long_down_ok": pair_results["short_vs_long_down"],
        "max_difference_mm": max(pair_values) if pair_values else None,
        "overall_ok": all(value <= HYSTERESIS_TOLERANCE_MM for value in pair_values) if pair_values else None,
    }


def _difference(a: int | None, b: int | None) -> int | None:
    if a is None or b is None:
        return None
    return abs(a - b)


def _floor_status(
    floor: ElevatorFloor,
    measurements: list[LevelingMeasurement],
    has_out_of_tolerance: bool,
    renivelation_ok: bool | None,
    hysteresis: dict,
) -> str:
    if not floor.is_leveling_required or not floor.is_served:
        return "not_required"
    if not measurements:
        return "pending"
    if any(measurement.effective_final_mm is not None and abs(measurement.effective_final_mm) > CRITICAL_FINAL_MM for measurement in measurements):
        return "critical"
    if has_out_of_tolerance or renivelation_ok is False or hysteresis["overall_ok"] is False:
        return "warning"
    return "ok"


def _overall_status(floor_summaries: list[dict], measured_required_floor_ids: set[UUID]) -> str:
    required_statuses = [floor["status"] for floor in floor_summaries if floor["status"] != "not_required"]
    if not measured_required_floor_ids:
        return "pending"
    if "critical" in required_statuses:
        return "critical"
    if "warning" in required_statuses or "pending" in required_statuses:
        return "warning"
    return "ok"


def _renivelation_is_acceptable(measurement: LevelingMeasurement) -> bool:
    if measurement.final_mm is None or measurement.landing_mm is None or not measurement.renivelation_occurred:
        return False
    return abs(measurement.final_mm - measurement.landing_mm) <= RENIVELATION_DELTA_TOLERANCE_MM and measurement.is_final_within_tolerance is True


def _collect_hysteresis_pairs(floor_summaries: list[dict]) -> list[bool]:
    pairs: list[bool] = []
    for floor_summary in floor_summaries:
        hysteresis = floor_summary["hysteresis"]
        for key in ("short_up_vs_down_ok", "long_up_vs_down_ok", "short_vs_long_up_ok", "short_vs_long_down_ok"):
            if hysteresis[key] is not None:
                pairs.append(hysteresis[key])
    return pairs


def _percentage(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100, 2) if denominator else 0.0
