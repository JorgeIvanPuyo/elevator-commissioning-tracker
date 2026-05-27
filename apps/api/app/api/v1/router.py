from fastapi import APIRouter

from app.api.v1.routes import health
from app.api.v1.routers import elevator_floors, elevators, projects, test_types

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(projects.router)
api_router.include_router(elevators.router)
api_router.include_router(elevator_floors.router)
api_router.include_router(test_types.router)
