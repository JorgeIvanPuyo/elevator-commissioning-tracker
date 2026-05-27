from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.db.models import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


async def create_project(session: AsyncSession, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def list_projects(session: AsyncSession, limit: int, offset: int) -> list[Project]:
    result = await session.scalars(select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset))
    return list(result)


async def get_project(session: AsyncSession, project_id: UUID) -> Project:
    project = await session.get(Project, project_id)
    if project is None:
        raise NotFoundError("Project not found")
    return project


async def update_project(session: AsyncSession, project_id: UUID, payload: ProjectUpdate) -> Project:
    project = await get_project(session, project_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    await session.commit()
    await session.refresh(project)
    return project


async def delete_project(session: AsyncSession, project_id: UUID) -> None:
    project = await get_project(session, project_id)
    await session.delete(project)
    await session.commit()


async def clear_projects(session: AsyncSession) -> None:
    await session.execute(delete(Project))
    await session.commit()
