from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import ParameterDefinition


async def list_parameter_definitions(
    session: AsyncSession,
    limit: int,
    offset: int,
    category: str | None = None,
    is_editable: bool | None = None,
) -> list[ParameterDefinition]:
    query = select(ParameterDefinition).order_by(ParameterDefinition.sort_order.asc(), ParameterDefinition.code.asc())
    if category is not None:
        query = query.where(ParameterDefinition.category == category)
    if is_editable is not None:
        query = query.where(ParameterDefinition.is_editable.is_(is_editable))

    result = await session.scalars(query.limit(limit).offset(offset))
    return list(result)


async def get_parameter_definition(session: AsyncSession, parameter_id: UUID) -> ParameterDefinition:
    parameter = await session.get(ParameterDefinition, parameter_id)
    if parameter is None:
        raise NotFoundError("Parameter definition not found")
    return parameter
