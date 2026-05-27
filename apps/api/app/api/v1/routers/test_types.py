from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.test_type import TestTypeRead
from app.services import test_types as test_type_service

router = APIRouter(prefix="/test-types", tags=["test-types"])


@router.get("", response_model=list[TestTypeRead])
async def list_test_types(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[TestTypeRead]:
    return await test_type_service.list_test_types(session, limit=limit, offset=offset)
