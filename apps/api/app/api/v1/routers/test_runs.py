from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.parameter import TestRunParameterValuesResponse, TestRunParameterValuesUpsert
from app.schemas.test_run import TestRunCreate, TestRunRead, TestRunUpdate
from app.services import test_run_parameters as parameter_value_service
from app.services import test_runs as test_run_service

router = APIRouter(tags=["test-runs"])


@router.post("/elevators/{elevator_id}/test-runs", response_model=TestRunRead, status_code=201)
async def create_test_run(
    elevator_id: UUID,
    payload: TestRunCreate,
    session: AsyncSession = Depends(get_db_session),
) -> TestRunRead:
    try:
        return await test_run_service.create_test_run(session, elevator_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/elevators/{elevator_id}/test-runs", response_model=list[TestRunRead])
async def list_elevator_test_runs(
    elevator_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    test_type_code: str | None = None,
    status: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[TestRunRead]:
    try:
        return await test_run_service.list_elevator_test_runs(
            session,
            elevator_id,
            limit=limit,
            offset=offset,
            test_type_code=test_type_code,
            status=status,
        )
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("/test-runs/{test_run_id}", response_model=TestRunRead)
async def get_test_run(
    test_run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TestRunRead:
    try:
        return await test_run_service.get_test_run(session, test_run_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/test-runs/{test_run_id}", response_model=TestRunRead)
async def update_test_run(
    test_run_id: UUID,
    payload: TestRunUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> TestRunRead:
    try:
        return await test_run_service.update_test_run(session, test_run_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.delete("/test-runs/{test_run_id}", status_code=204)
async def delete_test_run(
    test_run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await test_run_service.delete_test_run(session, test_run_id)
    except AppError as error:
        raise to_http_exception(error) from error
    return Response(status_code=204)


@router.get("/test-runs/{test_run_id}/parameters", response_model=TestRunParameterValuesResponse)
async def list_test_run_parameters(
    test_run_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> TestRunParameterValuesResponse:
    try:
        return await parameter_value_service.list_test_run_parameters(session, test_run_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.put("/test-runs/{test_run_id}/parameters", response_model=TestRunParameterValuesResponse)
async def upsert_test_run_parameters(
    test_run_id: UUID,
    payload: TestRunParameterValuesUpsert,
    session: AsyncSession = Depends(get_db_session),
) -> TestRunParameterValuesResponse:
    try:
        return await parameter_value_service.upsert_test_run_parameters(session, test_run_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error
