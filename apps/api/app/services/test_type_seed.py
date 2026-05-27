from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import TestType

TEST_TYPE_SEED_DATA = [
    {
        "code": "LOAD_TEST",
        "name": "Prueba de carga",
        "documentation_slug": "load-test",
        "sort_order": 10,
    },
    {
        "code": "FINE_LEVELING",
        "name": "Nivelación fina",
        "documentation_slug": "fine-leveling",
        "sort_order": 20,
    },
    {
        "code": "LOAD_COMPENSATION",
        "name": "Compensación de carga",
        "documentation_slug": "load-compensation",
        "sort_order": 30,
    },
    {
        "code": "PARAMETER_ADJUSTMENT",
        "name": "Ajuste de parámetros",
        "documentation_slug": "parameter-adjustment",
        "sort_order": 40,
    },
    {
        "code": "FLOOR_MEASUREMENT",
        "name": "Medición piso a piso",
        "documentation_slug": "floor-measurement",
        "sort_order": 50,
    },
]


async def seed_test_types(session: AsyncSession) -> None:
    existing_codes = set(
        await session.scalars(select(TestType.code).where(TestType.code.in_([item["code"] for item in TEST_TYPE_SEED_DATA])))
    )

    for item in TEST_TYPE_SEED_DATA:
        if item["code"] not in existing_codes:
            session.add(TestType(**item, is_active=True))
