from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.dashboard import DashboardOverviewRead
from app.services import dashboard as dashboard_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview", response_model=DashboardOverviewRead)
async def get_dashboard_overview(session: AsyncSession = Depends(get_db_session)) -> DashboardOverviewRead:
    return await dashboard_service.get_dashboard_overview(session)
