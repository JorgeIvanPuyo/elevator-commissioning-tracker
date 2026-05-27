from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.parameter import ParameterDefinitionRead
from app.services import parameter_definitions as parameter_definition_service

router = APIRouter(prefix="/parameter-definitions", tags=["parameter-definitions"])


@router.get("", response_model=list[ParameterDefinitionRead])
async def list_parameter_definitions(
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: str | None = None,
    is_editable: bool | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[ParameterDefinitionRead]:
    return await parameter_definition_service.list_parameter_definitions(
        session,
        limit=limit,
        offset=offset,
        category=category,
        is_editable=is_editable,
    )


@router.get("/{parameter_id}", response_model=ParameterDefinitionRead)
async def get_parameter_definition(
    parameter_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ParameterDefinitionRead:
    try:
        return await parameter_definition_service.get_parameter_definition(session, parameter_id)
    except AppError as error:
        raise to_http_exception(error) from error
