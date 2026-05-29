from uuid import uuid4

from app.services.zone_leveling import calculate_suggested_delta
from test_core_crud import create_project
from test_test_runs_and_parameters import get_test_type


BIAS_CODES = ["026D", "273", "026E", "274", "026F", "275", "270", "276", "271", "277", "272", "278"]


async def create_zone_test_run(client, floor_count: int = 9, code: str = "Z1") -> tuple[dict, list[dict], dict]:
    project = await create_project(client, name=f"Zone Project {code}", default_floor_count=floor_count)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": code})).json()
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors?limit=300")).json()
    test_type = await get_test_type(client, "FINE_LEVELING")
    test_run = (
        await client.post(
            f"/api/v1/elevators/{elevator['id']}/test-runs",
            json={"test_type_id": test_type["id"], "technician_name": "Tech", "status": "draft"},
        )
    ).json()
    return elevator, floors, test_run


async def save_bias_parameters(client, test_run_id: str, min_decimal: int = 100, max_decimal: int = 105, overrides: dict[str, int] | None = None) -> None:
    values_by_code = {
        "026D": min_decimal,
        "273": max_decimal,
        "026E": min_decimal,
        "274": max_decimal,
        "026F": min_decimal,
        "275": max_decimal,
        "270": min_decimal,
        "276": max_decimal,
        "271": min_decimal,
        "277": max_decimal,
        "272": min_decimal,
        "278": max_decimal,
    }
    values_by_code.update(overrides or {})
    response = await client.put(
        f"/api/v1/test-runs/{test_run_id}/parameters",
        json={"values": [{"parameter_code": code, "hex_value": format(decimal, "X")} for code, decimal in values_by_code.items()]},
    )
    assert response.status_code == 200


def measurement(origin: dict, destination: dict, direction: str = "up", landing_mm: int | None = 0, travel_type: str = "short") -> dict:
    return {
        "origin_floor_id": origin["id"],
        "destination_floor_id": destination["id"],
        "direction": direction,
        "travel_type": travel_type,
        "landing_mm": landing_mm,
        "final_mm": 0,
        "notes": "zone",
    }


def zone_entry(body: dict, zone: str, direction: str) -> dict:
    return next(item for item in body["zones"] if item["zone"] == zone and item["direction"] == direction)


def test_suggested_delta_uses_negative_average_landing_rule() -> None:
    assert calculate_suggested_delta(6.2) == -6
    assert calculate_suggested_delta(-6.2) == 6
    assert calculate_suggested_delta(0) == 0


async def test_zone_leveling_analysis_returns_404_for_unknown_test_run(client) -> None:
    response = await client.get(f"/api/v1/test-runs/{uuid4()}/zone-leveling-analysis")

    assert response.status_code == 404


async def test_empty_measurements_returns_all_entries_as_missing_measurements(client) -> None:
    _, _, test_run = await create_zone_test_run(client)
    await save_bias_parameters(client, test_run["id"])

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")

    assert response.status_code == 200
    body = response.json()
    assert len(body["zones"]) == 6
    assert all(item["measurement_count"] == 0 for item in body["zones"])
    assert all(item["status"] == "missing_measurements" for item in body["zones"])


async def test_default_62_floor_zone_ranges_use_sort_order(client) -> None:
    _, _, test_run = await create_zone_test_run(client, floor_count=62, code="Z62")

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json()

    assert zone_entry(body, "low", "up")["floor_range_label"] == "1-20"
    assert zone_entry(body, "mid", "up")["floor_range_label"] == "21-41"
    assert zone_entry(body, "high", "up")["floor_range_label"] == "42-62"


async def test_measurements_are_grouped_by_zone_and_direction(client) -> None:
    _, floors, test_run = await create_zone_test_run(client, floor_count=9)
    await save_bias_parameters(client, test_run["id"])
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement(floors[1], floors[0], "up", 2),
                measurement(floors[0], floors[1], "up", 4),
                measurement(floors[0], floors[4], "down", -3),
                measurement(floors[0], floors[8], "up", 8),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")

    body = response.json()
    assert zone_entry(body, "low", "up")["measurement_count"] == 2
    assert zone_entry(body, "mid", "down")["measurement_count"] == 1
    assert zone_entry(body, "high", "up")["measurement_count"] == 1


async def test_average_delta_and_suggested_hex_values_are_calculated(client) -> None:
    _, floors, test_run = await create_zone_test_run(client, floor_count=9)
    await save_bias_parameters(client, test_run["id"], overrides={"026D": 111, "273": 116})
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement(floors[1], floors[0], "up", -6, "short"),
                measurement(floors[2], floors[1], "up", -6, "short"),
                measurement(floors[3], floors[2], "up", -6, "short"),
                measurement(floors[2], floors[0], "up", -6, "long"),
                measurement(floors[0], floors[1], "up", -7, "long"),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")

    low_up = zone_entry(response.json(), "low", "up")
    assert low_up["average_landing_mm"] == -6.2
    assert low_up["rounded_delta_decimal"] == 6
    assert low_up["min_parameter"]["current_decimal"] == 111
    assert low_up["min_parameter"]["suggested_decimal"] == 117
    assert low_up["min_parameter"]["suggested_hex"] == "75"
    assert low_up["max_parameter"]["current_decimal"] == 116
    assert low_up["max_parameter"]["suggested_decimal"] == 122
    assert low_up["max_parameter"]["suggested_hex"] == "7A"
    assert low_up["current_window_decimal"] == 5
    assert low_up["suggested_window_decimal"] == 5


async def test_min_max_pair_mapping_is_correct_for_all_zone_direction_combinations(client) -> None:
    _, floors, test_run = await create_zone_test_run(client, floor_count=9)
    await save_bias_parameters(client, test_run["id"])
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement(floors[1], floors[0], "up", 1),
                measurement(floors[0], floors[1], "down", 1),
                measurement(floors[0], floors[3], "up", 1),
                measurement(floors[0], floors[4], "down", 1),
                measurement(floors[0], floors[6], "up", 1),
                measurement(floors[0], floors[7], "down", 1),
            ]
        },
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json()

    assert (zone_entry(body, "low", "up")["min_parameter"]["code"], zone_entry(body, "low", "up")["max_parameter"]["code"]) == ("026D", "273")
    assert (zone_entry(body, "low", "down")["min_parameter"]["code"], zone_entry(body, "low", "down")["max_parameter"]["code"]) == ("026E", "274")
    assert (zone_entry(body, "mid", "up")["min_parameter"]["code"], zone_entry(body, "mid", "up")["max_parameter"]["code"]) == ("026F", "275")
    assert (zone_entry(body, "mid", "down")["min_parameter"]["code"], zone_entry(body, "mid", "down")["max_parameter"]["code"]) == ("270", "276")
    assert (zone_entry(body, "high", "up")["min_parameter"]["code"], zone_entry(body, "high", "up")["max_parameter"]["code"]) == ("271", "277")
    assert (zone_entry(body, "high", "down")["min_parameter"]["code"], zone_entry(body, "high", "down")["max_parameter"]["code"]) == ("272", "278")


async def test_warning_when_max_is_less_than_or_equal_to_min(client) -> None:
    _, floors, test_run = await create_zone_test_run(client)
    await save_bias_parameters(client, test_run["id"], overrides={"026D": 100, "273": 100})
    await client.put(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk", json={"items": [measurement(floors[1], floors[0], "up", 1)]})

    low_up = zone_entry((await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json(), "low", "up")

    assert low_up["status"] == "warning"
    assert low_up["warnings"][0]["type"] == "INVALID_MIN_MAX_WINDOW"
    assert low_up["warnings"][0]["severity"] == "critical"


async def test_warning_when_window_is_below_preferred_range(client) -> None:
    _, floors, test_run = await create_zone_test_run(client)
    await save_bias_parameters(client, test_run["id"], overrides={"026D": 100, "273": 103})
    await client.put(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk", json={"items": [measurement(floors[1], floors[0], "up", 1)]})

    low_up = zone_entry((await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json(), "low", "up")

    assert low_up["current_window_decimal"] == 3
    assert low_up["warnings"][0]["type"] == "WINDOW_BELOW_RECOMMENDED_RANGE"


async def test_warning_when_window_is_above_preferred_range(client) -> None:
    _, floors, test_run = await create_zone_test_run(client)
    await save_bias_parameters(client, test_run["id"], overrides={"026D": 100, "273": 107})
    await client.put(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk", json={"items": [measurement(floors[1], floors[0], "up", 1)]})

    low_up = zone_entry((await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json(), "low", "up")

    assert low_up["current_window_decimal"] == 7
    assert low_up["warnings"][0]["type"] == "WINDOW_ABOVE_RECOMMENDED_RANGE"


async def test_missing_parameter_values_return_missing_parameter_status(client) -> None:
    _, floors, test_run = await create_zone_test_run(client)
    await client.put(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk", json={"items": [measurement(floors[1], floors[0], "up", 1)]})

    low_up = zone_entry((await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json(), "low", "up")

    assert low_up["status"] == "missing_parameters"
    assert low_up["min_parameter"]["current_decimal"] is None
    assert low_up["warnings"][0]["type"] == "MISSING_PARAMETER_VALUE"


async def test_only_served_and_leveling_required_floors_are_used_for_zone_splitting(client) -> None:
    _, floors, test_run = await create_zone_test_run(client, floor_count=6)
    await save_bias_parameters(client, test_run["id"])
    save_response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement(floors[1], floors[0], "up", 8),
                measurement(floors[3], floors[2], "up", 2),
            ]
        },
    )
    assert save_response.status_code == 200
    await client.patch(f"/api/v1/elevator-floors/{floors[0]['id']}", json={"is_served": False})
    await client.patch(f"/api/v1/elevator-floors/{floors[1]['id']}", json={"is_leveling_required": False})

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/zone-leveling-analysis")).json()

    low_up = zone_entry(body, "low", "up")
    assert low_up["floor_range_label"] == "3-3"
    assert low_up["measurement_count"] == 1
    assert low_up["average_landing_mm"] == 2.0
