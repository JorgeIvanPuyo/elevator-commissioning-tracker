from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TestType


async def list_test_types(session: AsyncSession, limit: int, offset: int) -> list[TestType]:
    result = await session.scalars(
        select(TestType).where(TestType.is_active.is_(True)).order_by(TestType.sort_order.asc()).limit(limit).offset(offset)
    )
    return list(result)
