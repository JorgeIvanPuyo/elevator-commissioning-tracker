from fastapi import APIRouter

from app.api.v1.routes import health
from app.api.v1.routers import (
    commissioning,
    dashboard,
    elevator_floors,
    elevators,
    leveling_measurements,
    parameter_definitions,
    projects,
    test_runs,
    test_types,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(commissioning.router)
api_router.include_router(dashboard.router)
api_router.include_router(projects.router)
api_router.include_router(elevators.router)
api_router.include_router(elevator_floors.router)
api_router.include_router(test_types.router)
api_router.include_router(test_runs.router)
api_router.include_router(parameter_definitions.router)
api_router.include_router(leveling_measurements.router)
