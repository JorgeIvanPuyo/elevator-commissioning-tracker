from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import to_http_exception
from app.core.exceptions import AppError
from app.db.session import get_db_session
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import projects as project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    try:
        return await project_service.create_project(session, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> list[ProjectRead]:
    return await project_service.list_projects(session, limit=limit, offset=offset)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    try:
        return await project_service.get_project(session, project_id)
    except AppError as error:
        raise to_http_exception(error) from error


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRead:
    try:
        return await project_service.update_project(session, project_id, payload)
    except AppError as error:
        raise to_http_exception(error) from error


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    try:
        await project_service.delete_project(session, project_id)
    except AppError as error:
        raise to_http_exception(error) from error
    return Response(status_code=204)
