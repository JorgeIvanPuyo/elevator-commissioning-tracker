from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, NotFoundError
from app.db.models import ElevatorFloor, LevelingMeasurement, TestRun
from app.schemas.leveling_measurement import LevelingMeasurementBulkItem, LevelingMeasurementBulkRequest


async def list_leveling_measurements(
    session: AsyncSession,
    test_run_id: UUID,
    limit: int,
    offset: int,
    direction: str | None = None,
    travel_type: str | None = None,
    measurement_stage: str | None = None,
) -> dict:
    await _get_test_run(session, test_run_id)
    if direction is not None:
        _validate_direction(direction)
    if travel_type is not None:
        _validate_travel_type(travel_type)
    if measurement_stage is not None:
        _validate_measurement_stage(measurement_stage)

    query = (
        select(LevelingMeasurement)
        .where(LevelingMeasurement.test_run_id == test_run_id)
        .order_by(LevelingMeasurement.created_at.asc())
        .limit(limit)
        .offset(offset)
    )
    if direction is not None:
        query = query.where(LevelingMeasurement.direction == direction)
    if travel_type is not None:
        query = query.where(LevelingMeasurement.travel_type == travel_type)
    if measurement_stage is not None:
        query = query.where(LevelingMeasurement.measurement_stage == measurement_stage)

    items = list(await session.scalars(query))
    return {"items": items, "summary": _build_summary(items)}


async def bulk_upsert_leveling_measurements(
    session: AsyncSession,
    test_run_id: UUID,
    payload: LevelingMeasurementBulkRequest,
) -> dict:
    test_run = await _get_test_run(session, test_run_id)
    _ensure_no_duplicate_payload_items(payload.items)
    floor_ids = {item.origin_floor_id for item in payload.items} | {item.destination_floor_id for item in payload.items}
    floors_by_id = await _get_floors_for_test_run(session, test_run, floor_ids)
    _validate_measurement_routes(payload.items, floors_by_id)
    existing_by_key = await _get_existing_measurements_by_key(session, test_run_id)

    saved_items: list[LevelingMeasurement] = []
    for item in payload.items:
        origin_floor = floors_by_id[item.origin_floor_id]
        destination_floor = floors_by_id[item.destination_floor_id]
        key = _measurement_key(test_run_id, item)
        values = _calculated_values(item)
        existing = existing_by_key.get(key)

        if existing is None:
            measurement = LevelingMeasurement(
                test_run_id=test_run_id,
                origin_floor_id=origin_floor.id,
                destination_floor_id=destination_floor.id,
                direction=item.direction,
                travel_type=item.travel_type,
                measurement_stage=item.measurement_stage,
                **values,
            )
            session.add(measurement)
            saved_items.append(measurement)
        else:
            for field, value in values.items():
                setattr(existing, field, value)
            saved_items.append(existing)

    await session.commit()
    for item in saved_items:
        await session.refresh(item)

    return {"items": saved_items, "summary": _build_summary(saved_items)}


async def delete_leveling_measurement(session: AsyncSession, measurement_id: UUID) -> None:
    measurement = await session.get(LevelingMeasurement, measurement_id)
    if measurement is None:
        raise NotFoundError("Leveling measurement not found")
    await session.delete(measurement)
    await session.commit()


async def clear_leveling_measurements(session: AsyncSession) -> None:
    await session.execute(delete(LevelingMeasurement))
    await session.commit()


async def _get_test_run(session: AsyncSession, test_run_id: UUID) -> TestRun:
    test_run = await session.get(TestRun, test_run_id)
    if test_run is None:
        raise NotFoundError("Test run not found")
    return test_run


async def _get_floors_for_test_run(
    session: AsyncSession,
    test_run: TestRun,
    floor_ids: set[UUID],
) -> dict[UUID, ElevatorFloor]:
    if not floor_ids:
        return {}

    floors = list(await session.scalars(select(ElevatorFloor).where(ElevatorFloor.id.in_(floor_ids))))
    floors_by_id = {floor.id: floor for floor in floors}
    missing_floor_ids = floor_ids - set(floors_by_id)
    if missing_floor_ids:
        raise AppError("One or more floor references do not exist")

    invalid_floors = [floor for floor in floors if floor.elevator_id != test_run.elevator_id]
    if invalid_floors:
        raise AppError("Floor references must belong to the same elevator as the test run")

    return floors_by_id


async def _get_existing_measurements_by_key(
    session: AsyncSession,
    test_run_id: UUID,
) -> dict[tuple[UUID, UUID, UUID, str, str, str], LevelingMeasurement]:
    result = await session.scalars(select(LevelingMeasurement).where(LevelingMeasurement.test_run_id == test_run_id))
    return {
        (
            measurement.test_run_id,
            measurement.origin_floor_id,
            measurement.destination_floor_id,
            measurement.direction,
            measurement.travel_type,
            measurement.measurement_stage,
        ): measurement
        for measurement in result
    }


def _ensure_no_duplicate_payload_items(items: list[LevelingMeasurementBulkItem]) -> None:
    keys = [(_item_key(item)) for item in items]
    if len(keys) != len(set(keys)):
        raise AppError("Duplicate leveling measurement in request")


def _validate_measurement_routes(items: list[LevelingMeasurementBulkItem], floors_by_id: dict[UUID, ElevatorFloor]) -> None:
    for item in items:
        if item.origin_floor_id == item.destination_floor_id:
            raise AppError("Origin and destination floors must be different")

        destination_floor = floors_by_id[item.destination_floor_id]
        if not destination_floor.is_leveling_required:
            raise AppError("Destination floor must require leveling")


def _item_key(item: LevelingMeasurementBulkItem) -> tuple[UUID, UUID, str, str, str]:
    return (item.origin_floor_id, item.destination_floor_id, item.direction, item.travel_type, item.measurement_stage)


def _measurement_key(test_run_id: UUID, item: LevelingMeasurementBulkItem) -> tuple[UUID, UUID, UUID, str, str, str]:
    return (test_run_id, item.origin_floor_id, item.destination_floor_id, item.direction, item.travel_type, item.measurement_stage)


def _calculated_values(item: LevelingMeasurementBulkItem) -> dict:
    effective_final_mm = item.final_mm if item.final_mm is not None else item.landing_mm
    is_final_within_tolerance = None
    if effective_final_mm is not None:
        is_final_within_tolerance = -5 <= effective_final_mm <= 5

    renivelation_occurred = item.final_mm is not None and item.landing_mm is not None and item.final_mm != item.landing_mm

    return {
        "landing_mm": item.landing_mm,
        "final_mm": item.final_mm,
        "renivelation_occurred": renivelation_occurred,
        "effective_final_mm": effective_final_mm,
        "is_final_within_tolerance": is_final_within_tolerance,
        "notes": item.notes,
    }


def _build_summary(items: list[LevelingMeasurement]) -> dict:
    total = len(items)
    with_values = len([item for item in items if item.effective_final_mm is not None])
    within_tolerance = len([item for item in items if item.is_final_within_tolerance is True])
    outside_tolerance = len([item for item in items if item.is_final_within_tolerance is False])
    percentage = round((within_tolerance / with_values) * 100, 2) if with_values else 0.0
    return {
        "total": total,
        "with_values": with_values,
        "within_tolerance": within_tolerance,
        "outside_tolerance": outside_tolerance,
        "within_tolerance_percentage": percentage,
    }


def _validate_direction(direction: str) -> None:
    if direction not in {"up", "down"}:
        raise AppError("Invalid leveling measurement direction")


def _validate_travel_type(travel_type: str) -> None:
    if travel_type not in {"short", "long"}:
        raise AppError("Invalid leveling measurement travel_type")


def _validate_measurement_stage(measurement_stage: str) -> None:
    if measurement_stage not in {"zone_tuning", "floor_by_floor", "final_validation"}:
        raise AppError("Invalid leveling measurement_stage")
