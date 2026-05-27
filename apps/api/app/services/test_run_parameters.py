from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.models import ParameterDefinition, TestRunParameterValue
from app.schemas.parameter import TestRunParameterValuesUpsert
from app.services.test_runs import get_test_run_model
from app.utils.hex_values import normalize_hex_value


async def list_test_run_parameters(session: AsyncSession, test_run_id: UUID) -> dict:
    await get_test_run_model(session, test_run_id)
    values = await _list_values(session, test_run_id)
    return {"test_run_id": test_run_id, "values": values, "validation_warnings": []}


async def upsert_test_run_parameters(session: AsyncSession, test_run_id: UUID, payload: TestRunParameterValuesUpsert) -> dict:
    await get_test_run_model(session, test_run_id)

    input_codes = [_normalize_parameter_code(item.parameter_code) for item in payload.values]
    if len(input_codes) != len(set(input_codes)):
        raise AppError("Duplicate parameter_code in request")

    definitions_by_code = await _get_definitions_by_code(session, input_codes)
    missing_codes = sorted(set(input_codes) - set(definitions_by_code))
    if missing_codes:
        raise AppError(f"Unknown parameter code: {', '.join(missing_codes)}")

    normalized_inputs = []
    for item, code in zip(payload.values, input_codes, strict=True):
        hex_value, decimal_value = normalize_hex_value(item.hex_value)
        normalized_inputs.append(
            {
                "parameter_code": code,
                "definition": definitions_by_code[code],
                "hex_value": hex_value,
                "decimal_value": decimal_value,
                "source": item.source,
                "notes": item.notes,
            }
        )

    existing_values = await _get_existing_values_by_definition_id(session, test_run_id)
    final_decimals = await _build_final_decimal_map(session, test_run_id)
    for item in normalized_inputs:
        final_decimals[item["parameter_code"]] = item["decimal_value"]
    _validate_min_max_pairs(await _get_all_paired_definitions(session), final_decimals)

    for item in normalized_inputs:
        definition = item["definition"]
        existing = existing_values.get(definition.id)
        if existing is None:
            session.add(
                TestRunParameterValue(
                    test_run_id=test_run_id,
                    parameter_definition_id=definition.id,
                    hex_value=item["hex_value"],
                    decimal_value=item["decimal_value"],
                    source=item["source"],
                    notes=item["notes"],
                )
            )
        else:
            existing.hex_value = item["hex_value"]
            existing.decimal_value = item["decimal_value"]
            existing.source = item["source"]
            existing.notes = item["notes"]

    await session.commit()
    return await list_test_run_parameters(session, test_run_id)


async def _list_values(session: AsyncSession, test_run_id: UUID) -> list[dict]:
    rows = (
        await session.execute(
            select(TestRunParameterValue, ParameterDefinition)
            .join(ParameterDefinition, TestRunParameterValue.parameter_definition_id == ParameterDefinition.id)
            .where(TestRunParameterValue.test_run_id == test_run_id)
            .order_by(ParameterDefinition.sort_order.asc(), ParameterDefinition.code.asc())
        )
    ).all()
    return [_serialize_value(value, definition) for value, definition in rows]


async def _get_definitions_by_code(session: AsyncSession, codes: list[str]) -> dict[str, ParameterDefinition]:
    if not codes:
        return {}
    result = await session.scalars(select(ParameterDefinition).where(ParameterDefinition.code.in_(codes)))
    return {definition.code: definition for definition in result}


async def _get_existing_values_by_definition_id(
    session: AsyncSession,
    test_run_id: UUID,
) -> dict[UUID, TestRunParameterValue]:
    result = await session.scalars(
        select(TestRunParameterValue).where(TestRunParameterValue.test_run_id == test_run_id)
    )
    return {value.parameter_definition_id: value for value in result}


async def _build_final_decimal_map(session: AsyncSession, test_run_id: UUID) -> dict[str, int | None]:
    rows = (
        await session.execute(
            select(TestRunParameterValue, ParameterDefinition)
            .join(ParameterDefinition, TestRunParameterValue.parameter_definition_id == ParameterDefinition.id)
            .where(TestRunParameterValue.test_run_id == test_run_id)
        )
    ).all()
    return {definition.code: value.decimal_value for value, definition in rows}


async def _get_all_paired_definitions(session: AsyncSession) -> list[ParameterDefinition]:
    result = await session.scalars(
        select(ParameterDefinition)
        .where(ParameterDefinition.bound_type.in_(["min", "max"]), ParameterDefinition.pair_code.is_not(None))
        .order_by(ParameterDefinition.sort_order.asc())
    )
    return list(result)


def _validate_min_max_pairs(definitions: list[ParameterDefinition], decimal_values: dict[str, int | None]) -> None:
    definitions_by_code = {definition.code: definition for definition in definitions}
    for definition in definitions:
        if definition.bound_type != "min" or definition.pair_code is None:
            continue
        pair = definitions_by_code.get(definition.pair_code)
        if pair is None:
            continue
        min_value = decimal_values.get(definition.code)
        max_value = decimal_values.get(pair.code)
        if min_value is not None and max_value is not None and max_value < min_value:
            raise AppError(f"Invalid min/max pair: {pair.code} must be greater than or equal to {definition.code}")


def _serialize_value(value: TestRunParameterValue, definition: ParameterDefinition) -> dict:
    return {
        "id": value.id,
        "test_run_id": value.test_run_id,
        "parameter_definition_id": value.parameter_definition_id,
        "parameter_code": definition.code,
        "parameter_name": definition.name,
        "hex_value": value.hex_value,
        "decimal_value": value.decimal_value,
        "source": value.source,
        "notes": value.notes,
        "created_at": value.created_at,
        "updated_at": value.updated_at,
    }


def _normalize_parameter_code(code: str) -> str:
    return code.strip().upper()
