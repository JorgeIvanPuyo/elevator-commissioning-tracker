from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Elevator, Project, TestRun, TestType


async def get_dashboard_overview(session: AsyncSession) -> dict:
    projects_count = await session.scalar(select(func.count(Project.id)))
    active_projects_count = await session.scalar(select(func.count(Project.id)).where(Project.status == "active"))
    elevators_count = await session.scalar(select(func.count(Elevator.id)))
    test_runs_count = await session.scalar(select(func.count(TestRun.id)))
    completed_test_runs_count = await session.scalar(select(func.count(TestRun.id)).where(TestRun.status == "completed"))
    in_progress_test_runs_count = await session.scalar(select(func.count(TestRun.id)).where(TestRun.status == "in_progress"))
    draft_test_runs_count = await session.scalar(select(func.count(TestRun.id)).where(TestRun.status == "draft"))

    latest_test_runs_rows = (
        await session.execute(
            select(TestRun, TestType, Elevator, Project)
            .join(TestType, TestRun.test_type_id == TestType.id)
            .join(Elevator, TestRun.elevator_id == Elevator.id)
            .join(Project, Elevator.project_id == Project.id)
            .order_by(TestRun.created_at.desc())
            .limit(5)
        )
    ).all()
    latest_projects_rows = (
        await session.execute(
            select(Project, func.count(Elevator.id))
            .outerjoin(Elevator, Elevator.project_id == Project.id)
            .group_by(Project.id)
            .order_by(Project.created_at.desc())
            .limit(5)
        )
    ).all()

    return {
        "projects_count": projects_count or 0,
        "active_projects_count": active_projects_count or 0,
        "elevators_count": elevators_count or 0,
        "test_runs_count": test_runs_count or 0,
        "completed_test_runs_count": completed_test_runs_count or 0,
        "in_progress_test_runs_count": in_progress_test_runs_count or 0,
        "draft_test_runs_count": draft_test_runs_count or 0,
        "latest_test_runs": [_serialize_latest_test_run(*row) for row in latest_test_runs_rows],
        "latest_projects": [_serialize_latest_project(project, elevators_count) for project, elevators_count in latest_projects_rows],
    }


def _serialize_latest_test_run(test_run: TestRun, test_type: TestType, elevator: Elevator, project: Project) -> dict:
    return {
        "id": test_run.id,
        "title": test_run.title,
        "name": test_run.title or test_type.name,
        "test_type": test_type.name,
        "status": test_run.status,
        "elevator_id": elevator.id,
        "elevator_code": elevator.code,
        "project_id": project.id,
        "project_name": project.name,
        "responsible_technician": test_run.technician_name,
        "created_at": test_run.created_at,
        "updated_at": test_run.updated_at,
    }


def _serialize_latest_project(project: Project, elevators_count: int) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "elevators_count": elevators_count,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
