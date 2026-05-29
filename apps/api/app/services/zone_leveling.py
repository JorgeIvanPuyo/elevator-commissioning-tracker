from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ElevatorFloor, LevelingMeasurement, ParameterDefinition, TestRun, TestRunParameterValue
from app.services.test_runs import get_test_run_model
from app.utils.hex_values import decimal_to_hex

ZoneName = str
Direction = str

ZONE_ORDER = ["low", "mid", "high"]
DIRECTION_ORDER = ["up", "down"]
PREFERRED_WINDOW_MIN = 4
PREFERRED_WINDOW_MAX = 6

BIAS_PARAMETER_PAIRS: dict[tuple[ZoneName, Direction], tuple[str, str]] = {
    ("low", "up"): ("026D", "273"),
    ("low", "down"): ("026E", "274"),
    ("mid", "up"): ("026F", "275"),
    ("mid", "down"): ("270", "276"),
    ("high", "up"): ("271", "277"),
    ("high", "down"): ("272", "278"),
}


async def get_zone_leveling_analysis(session: AsyncSession, test_run_id: UUID) -> dict:
    test_run = await get_test_run_model(session, test_run_id)
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
            .order_by(LevelingMeasurement.created_at.asc())
        )
    )
    parameter_values = await _get_parameter_values(session, test_run_id)
    definitions = await _get_parameter_definitions(session)
    zones = split_floors_into_zones(floors)
    zone_by_floor_id = {floor.id: zone_name for zone_name, zone_floors in zones.items() for floor in zone_floors}
    measurements_by_zone_direction = _group_measurements_by_zone_direction(measurements, zone_by_floor_id)

    return {
        "test_run_id": test_run.id,
        "elevator_id": test_run.elevator_id,
        "zones": [
            _build_zone_entry(
                zone_name,
                direction,
                zones[zone_name],
                measurements_by_zone_direction.get((zone_name, direction), []),
                parameter_values,
                definitions,
            )
            for zone_name in ZONE_ORDER
            for direction in DIRECTION_ORDER
        ],
        "global_warnings": [],
    }


def calculate_suggested_delta(average_landing_mm: float | None) -> int | None:
    if average_landing_mm is None:
        return None
    # MVP field rule: high/positive landings reduce bias, low/negative landings increase bias.
    # Keep this centralized because the sign convention may be refined after field validation.
    return round(-average_landing_mm)


def split_floors_into_zones(floors: list[ElevatorFloor]) -> dict[ZoneName, list[ElevatorFloor]]:
    required_floors = [floor for floor in floors if floor.is_served and floor.is_leveling_required]
    total = len(required_floors)
    low_count = total // 3
    remaining = total - low_count
    mid_count = (remaining + 1) // 2
    return {
        "low": required_floors[:low_count],
        "mid": required_floors[low_count : low_count + mid_count],
        "high": required_floors[low_count + mid_count :],
    }


def resolve_zone_bias_parameter_pair(zone: ZoneName, direction: Direction) -> tuple[str, str]:
    return BIAS_PARAMETER_PAIRS[(zone, direction)]


def calculate_parameter_window_warnings(
    min_decimal: int | None,
    max_decimal: int | None,
    min_code: str,
    max_code: str,
) -> list[dict]:
    if min_decimal is None or max_decimal is None:
        return []

    window = max_decimal - min_decimal
    if max_decimal <= min_decimal:
        return [
            {
                "type": "INVALID_MIN_MAX_WINDOW",
                "severity": "critical",
                "message": f"MAX {max_code} debe ser mayor que MIN {min_code}.",
            }
        ]
    if window < PREFERRED_WINDOW_MIN:
        return [
            {
                "type": "WINDOW_BELOW_RECOMMENDED_RANGE",
                "severity": "warning",
                "message": f"La ventana {max_code}-{min_code} es {window}; recomendado {PREFERRED_WINDOW_MIN}-{PREFERRED_WINDOW_MAX}.",
            }
        ]
    if window > PREFERRED_WINDOW_MAX:
        return [
            {
                "type": "WINDOW_ABOVE_RECOMMENDED_RANGE",
                "severity": "warning",
                "message": f"La ventana {max_code}-{min_code} es {window}; recomendado {PREFERRED_WINDOW_MIN}-{PREFERRED_WINDOW_MAX}.",
            }
        ]
    return []


async def _get_parameter_values(session: AsyncSession, test_run_id: UUID) -> dict[str, TestRunParameterValue]:
    rows = (
        await session.execute(
            select(TestRunParameterValue, ParameterDefinition)
            .join(ParameterDefinition, TestRunParameterValue.parameter_definition_id == ParameterDefinition.id)
            .where(TestRunParameterValue.test_run_id == test_run_id)
        )
    ).all()
    return {definition.code: value for value, definition in rows}


async def _get_parameter_definitions(session: AsyncSession) -> dict[str, ParameterDefinition]:
    result = await session.scalars(select(ParameterDefinition).where(ParameterDefinition.code.in_([code for pair in BIAS_PARAMETER_PAIRS.values() for code in pair])))
    return {definition.code: definition for definition in result}


def _group_measurements_by_zone_direction(
    measurements: list[LevelingMeasurement],
    zone_by_floor_id: dict[UUID, ZoneName],
) -> dict[tuple[ZoneName, Direction], list[LevelingMeasurement]]:
    grouped: dict[tuple[ZoneName, Direction], list[LevelingMeasurement]] = {}
    for measurement in measurements:
        if measurement.landing_mm is None:
            continue
        zone = zone_by_floor_id.get(measurement.destination_floor_id)
        if zone is None or measurement.direction not in DIRECTION_ORDER:
            continue
        grouped.setdefault((zone, measurement.direction), []).append(measurement)
    return grouped


def _build_zone_entry(
    zone: ZoneName,
    direction: Direction,
    floors: list[ElevatorFloor],
    measurements: list[LevelingMeasurement],
    parameter_values: dict[str, TestRunParameterValue],
    definitions: dict[str, ParameterDefinition],
) -> dict:
    min_code, max_code = resolve_zone_bias_parameter_pair(zone, direction)
    min_value = parameter_values.get(min_code)
    max_value = parameter_values.get(max_code)
    average_landing_mm = _average([measurement.landing_mm for measurement in measurements if measurement.landing_mm is not None])
    delta = calculate_suggested_delta(average_landing_mm)
    min_parameter = _build_parameter_suggestion(min_code, min_value, delta)
    max_parameter = _build_parameter_suggestion(max_code, max_value, delta)
    current_window = _window(min_parameter["current_decimal"], max_parameter["current_decimal"])
    suggested_window = _window(min_parameter["suggested_decimal"], max_parameter["suggested_decimal"])
    warnings = []

    if min_value is None or max_value is None or min_value.decimal_value is None or max_value.decimal_value is None:
        missing_codes = [code for code, value in ((min_code, min_value), (max_code, max_value)) if value is None or value.decimal_value is None]
        warnings.append(
            {
                "type": "MISSING_PARAMETER_VALUE",
                "severity": "warning",
                "message": f"Faltan valores de parámetros: {', '.join(missing_codes)}.",
            }
        )
    else:
        warnings.extend(calculate_parameter_window_warnings(min_value.decimal_value, max_value.decimal_value, min_code, max_code))

    status = _entry_status(measurements, min_parameter, max_parameter, warnings)
    return {
        "zone": zone,
        "direction": direction,
        "floor_range_label": _floor_range_label(floors),
        "measurement_count": len(measurements),
        "average_landing_mm": round(average_landing_mm, 2) if average_landing_mm is not None else None,
        "rounded_delta_decimal": delta,
        "min_parameter": {
            **min_parameter,
            "code": definitions.get(min_code).code if definitions.get(min_code) else min_code,
        },
        "max_parameter": {
            **max_parameter,
            "code": definitions.get(max_code).code if definitions.get(max_code) else max_code,
        },
        "current_window_decimal": current_window,
        "suggested_window_decimal": suggested_window,
        "warnings": warnings,
        "status": status,
    }


def _build_parameter_suggestion(code: str, value: TestRunParameterValue | None, delta: int | None) -> dict:
    current_decimal = value.decimal_value if value else None
    suggested_decimal = current_decimal + delta if current_decimal is not None and delta is not None else None
    return {
        "code": code,
        "current_hex": value.hex_value if value else None,
        "current_decimal": current_decimal,
        "suggested_decimal": suggested_decimal,
        "suggested_hex": decimal_to_hex(suggested_decimal) if suggested_decimal is not None and suggested_decimal >= 0 else None,
    }


def _entry_status(
    measurements: list[LevelingMeasurement],
    min_parameter: dict,
    max_parameter: dict,
    warnings: list[dict],
) -> str:
    if not measurements:
        return "missing_measurements"
    if min_parameter["current_decimal"] is None or max_parameter["current_decimal"] is None:
        return "missing_parameters"
    if warnings:
        return "warning"
    return "ok"


def _average(values: list[int]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _window(min_decimal: int | None, max_decimal: int | None) -> int | None:
    if min_decimal is None or max_decimal is None:
        return None
    return max_decimal - min_decimal


def _floor_range_label(floors: list[ElevatorFloor]) -> str:
    if not floors:
        return "-"
    first = floors[0].label or str(floors[0].sort_order)
    last = floors[-1].label or str(floors[-1].sort_order)
    return f"{first}-{last}"
