from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.leveling_measurement import LevelingMeasurementBulkRequest, LevelingMeasurementBulkResponse
from app.services import leveling_measurements as leveling_measurement_service

router = APIRouter(tags=["leveling-measurements"])


@router.get("/test-runs/{test_run_id}/leveling-measurements", response_model=LevelingMeasurementBulkResponse)
async def list_leveling_measurements(
    test_run_id: UUID,
    direction: str | None = None,
    travel_type: str | None = None,
    limit: int = Query(default=300, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> LevelingMeasurementBulkResponse:
    try:
        return await leveling_measurement_service.list_leveling_measurements(
            session,
            test_run_id,
            limit=limit,
            offset=offset,
            direction=direction,
            travel_type=travel_type,
        )
    except AppError as error:
        raise to_http_exception(error) from error


@router.put("/test-runs/{test_run_id}/leveling-measurements/bulk", response_model=LevelingMeasurementBulkResponse)
async def bulk_upsert_leveling_measurements(
    test_run_id: UUID,
    payload: LevelingMeasurementBulkRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LevelingMeasurementBulkResponse:
    try:
        return await leveling_measurement_service.bulk_upsert_leveling_measurements(session, test_run_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.delete("/leveling-measurements/{measurement_id}", status_code=204)
async def delete_leveling_measurement(
    measurement_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await leveling_measurement_service.delete_leveling_measurement(session, measurement_id)
    except AppError as error:
        raise to_http_exception(error) from error
    return Response(status_code=204)
