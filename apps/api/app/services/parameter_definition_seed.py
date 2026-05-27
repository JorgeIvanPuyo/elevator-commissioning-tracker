from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ParameterDefinition


PARAMETER_DEFINITION_SEED_DATA = [
    {
        "code": "026D",
        "name": "Low zone up bias minimum",
        "category": "fine_leveling",
        "zone": "low",
        "direction": "up",
        "bound_type": "min",
        "pair_code": "273",
        "sort_order": 100,
    },
    {
        "code": "026E",
        "name": "Low zone down bias minimum",
        "category": "fine_leveling",
        "zone": "low",
        "direction": "down",
        "bound_type": "min",
        "pair_code": "274",
        "sort_order": 110,
    },
    {
        "code": "026F",
        "name": "Mid zone up bias minimum",
        "category": "fine_leveling",
        "zone": "mid",
        "direction": "up",
        "bound_type": "min",
        "pair_code": "275",
        "sort_order": 120,
    },
    {
        "code": "270",
        "name": "Mid zone down bias minimum",
        "category": "fine_leveling",
        "zone": "mid",
        "direction": "down",
        "bound_type": "min",
        "pair_code": "276",
        "sort_order": 130,
    },
    {
        "code": "271",
        "name": "High zone up bias minimum",
        "category": "fine_leveling",
        "zone": "high",
        "direction": "up",
        "bound_type": "min",
        "pair_code": "277",
        "sort_order": 140,
    },
    {
        "code": "272",
        "name": "High zone down bias minimum",
        "category": "fine_leveling",
        "zone": "high",
        "direction": "down",
        "bound_type": "min",
        "pair_code": "278",
        "sort_order": 150,
    },
    {
        "code": "273",
        "name": "Low zone up bias maximum",
        "category": "fine_leveling",
        "zone": "low",
        "direction": "up",
        "bound_type": "max",
        "pair_code": "026D",
        "sort_order": 160,
    },
    {
        "code": "274",
        "name": "Low zone down bias maximum",
        "category": "fine_leveling",
        "zone": "low",
        "direction": "down",
        "bound_type": "max",
        "pair_code": "026E",
        "sort_order": 170,
    },
    {
        "code": "275",
        "name": "Mid zone up bias maximum",
        "category": "fine_leveling",
        "zone": "mid",
        "direction": "up",
        "bound_type": "max",
        "pair_code": "026F",
        "sort_order": 180,
    },
    {
        "code": "276",
        "name": "Mid zone down bias maximum",
        "category": "fine_leveling",
        "zone": "mid",
        "direction": "down",
        "bound_type": "max",
        "pair_code": "270",
        "sort_order": 190,
    },
    {
        "code": "277",
        "name": "High zone up bias maximum",
        "category": "fine_leveling",
        "zone": "high",
        "direction": "up",
        "bound_type": "max",
        "pair_code": "271",
        "sort_order": 200,
    },
    {
        "code": "278",
        "name": "High zone down bias maximum",
        "category": "fine_leveling",
        "zone": "high",
        "direction": "down",
        "bound_type": "max",
        "pair_code": "272",
        "sort_order": 210,
    },
    {"code": "266", "name": "Load compensation reference", "category": "load_compensation", "sort_order": 300},
    {"code": "240", "name": "Load compensation parameter 240", "category": "load_compensation", "sort_order": 310},
    {"code": "241", "name": "Load compensation parameter 241", "category": "load_compensation", "sort_order": 320},
    {"code": "242", "name": "Load compensation parameter 242", "category": "load_compensation", "sort_order": 330},
    {"code": "243", "name": "Load compensation parameter 243", "category": "load_compensation", "sort_order": 340},
    {"code": "244", "name": "Load compensation parameter 244", "category": "load_compensation", "sort_order": 350},
    {"code": "245", "name": "Load compensation parameter 245", "category": "load_compensation", "sort_order": 360},
    {"code": "212", "name": "Manual leveling adjustment 212", "category": "manual_adjustment", "sort_order": 400},
    {"code": "214", "name": "Manual leveling adjustment 214", "category": "manual_adjustment", "sort_order": 410},
    {"code": "022F", "name": "Manual hysteresis/general adjustment", "category": "manual_adjustment", "sort_order": 420},
    {"code": "229", "name": "Manual leveling related adjustment", "category": "manual_adjustment", "sort_order": 430},
]


async def seed_parameter_definitions(session: AsyncSession) -> None:
    codes = [item["code"] for item in PARAMETER_DEFINITION_SEED_DATA]
    existing_codes = set(await session.scalars(select(ParameterDefinition.code).where(ParameterDefinition.code.in_(codes))))

    for item in PARAMETER_DEFINITION_SEED_DATA:
        if item["code"] not in existing_codes:
            session.add(ParameterDefinition(**item, is_editable=True))
