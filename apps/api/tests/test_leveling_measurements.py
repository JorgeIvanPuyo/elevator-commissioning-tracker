from test_core_crud import create_project
from test_test_runs_and_parameters import create_test_run, get_test_type


async def create_elevator_with_floors(client, code: str = "L9", floor_count: int = 4) -> tuple[dict, list[dict]]:
    project = await create_project(client, name=f"Project {code}", default_floor_count=floor_count)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": code})).json()
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors?limit=100")).json()
    return elevator, floors


async def create_measurement_test_run(client, code: str = "L9") -> tuple[dict, list[dict], dict]:
    elevator, floors = await create_elevator_with_floors(client, code=code)
    test_type = await get_test_type(client, "FINE_LEVELING")
    test_run = (
        await client.post(
            f"/api/v1/elevators/{elevator['id']}/test-runs",
            json={"test_type_id": test_type["id"], "technician_name": "Tech", "status": "draft"},
        )
    ).json()
    return elevator, floors, test_run


def measurement_payload(origin_floor_id: str, destination_floor_id: str, **overrides) -> dict:
    payload = {
        "origin_floor_id": origin_floor_id,
        "destination_floor_id": destination_floor_id,
        "direction": "up",
        "travel_type": "short",
        "landing_mm": 2,
        "final_mm": 1,
        "renivelation_occurred": False,
        "notes": "ok",
    }
    payload.update(overrides)
    return payload


async def test_bulk_save_leveling_measurements(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"])]},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["summary"]["total"] == 1


async def test_list_leveling_measurements_by_test_run(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"])]},
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements")

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1


async def test_effective_final_uses_final_mm_when_provided(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=9, final_mm=4)]},
    )

    assert response.json()["items"][0]["effective_final_mm"] == 4


async def test_effective_final_uses_landing_mm_when_final_is_null(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=-3, final_mm=None)]},
    )

    assert response.json()["items"][0]["effective_final_mm"] == -3


async def test_final_tolerance_true_for_minus_five_zero_and_plus_five(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=-5),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=0),
                measurement_payload(floors[2]["id"], floors[3]["id"], final_mm=5),
            ]
        },
    )

    assert all(item["is_final_within_tolerance"] is True for item in response.json()["items"])


async def test_final_tolerance_false_outside_range(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=-6),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=6),
            ]
        },
    )

    assert all(item["is_final_within_tolerance"] is False for item in response.json()["items"])


async def test_reject_floor_from_other_elevator(client) -> None:
    _, floors_a, test_run = await create_measurement_test_run(client, code="L9")
    _, floors_b = await create_elevator_with_floors(client, code="L10")

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors_a[0]["id"], floors_b[1]["id"])]},
    )

    assert response.status_code == 400
    assert "same elevator" in response.json()["detail"]


async def test_reject_origin_from_other_elevator(client) -> None:
    _, floors_a, test_run = await create_measurement_test_run(client, code="L9")
    _, floors_b = await create_elevator_with_floors(client, code="L10")

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors_b[0]["id"], floors_a[1]["id"])]},
    )

    assert response.status_code == 400
    assert "same elevator" in response.json()["detail"]


async def test_reject_origin_equal_to_destination(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[0]["id"])]},
    )

    assert response.status_code == 400
    assert "different" in response.json()["detail"]


async def test_reject_destination_without_leveling_required(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    update = await client.patch(f"/api/v1/elevator-floors/{floors[1]['id']}", json={"is_leveling_required": False})
    assert update.status_code == 200

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"])]},
    )

    assert response.status_code == 400
    assert "require leveling" in response.json()["detail"]


async def test_reject_invalid_direction(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], direction="sideways")]},
    )

    assert response.status_code == 422


async def test_reject_invalid_travel_type(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], travel_type="medium")]},
    )

    assert response.status_code == 422


async def test_bulk_does_not_partially_write_when_one_item_is_invalid(client) -> None:
    _, floors_a, test_run = await create_measurement_test_run(client, code="L9")
    _, floors_b = await create_elevator_with_floors(client, code="L10")

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors_a[0]["id"], floors_a[1]["id"]),
                measurement_payload(floors_a[1]["id"], floors_b[2]["id"]),
            ]
        },
    )
    persisted = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements")

    assert response.status_code == 400
    assert persisted.status_code == 200
    assert persisted.json()["items"] == []


async def test_upsert_same_measurement_updates_instead_of_duplicate(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    url = f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk"
    first = await client.put(url, json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=2)]})
    second = await client.put(url, json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=7, notes="updated")]})

    assert first.status_code == 200
    assert second.status_code == 200
    body = second.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["final_mm"] == 7
    assert body["items"][0]["notes"] == "updated"
    assert body["summary"]["total"] == 1


async def test_summary_values_are_correct(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=1),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=8),
                measurement_payload(floors[2]["id"], floors[3]["id"], landing_mm=None, final_mm=None),
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "total": 3,
        "with_values": 2,
        "within_tolerance": 1,
        "outside_tolerance": 1,
        "within_tolerance_percentage": 50.0,
    }


async def test_renivelation_occurs_when_final_differs_from_landing(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=10, final_mm=2, renivelation_occurred=False)]},
    )

    item = response.json()["items"][0]
    assert item["did_relevel"] is True
    assert item["renivelation_occurred"] is True


async def test_did_relevel_false_when_final_equals_landing(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=2, final_mm=2)]},
    )

    item = response.json()["items"][0]
    assert item["did_relevel"] is False
    assert item["renivelation_occurred"] is False


async def test_did_relevel_false_when_final_is_null(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=-9, final_mm=None, renivelation_occurred=True)]},
    )

    item = response.json()["items"][0]
    assert item["did_relevel"] is False
    assert item["renivelation_occurred"] is False
    assert item["effective_final_mm"] == -9


async def test_leveling_summary_empty_without_measurements(client) -> None:
    elevator, _, test_run = await create_measurement_test_run(client)

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["test_run_id"] == test_run["id"]
    assert body["elevator_id"] == elevator["id"]
    assert body["measurement_count"] == 0
    assert body["required_floor_count"] == 4
    assert body["measured_required_floor_count"] == 0
    assert body["coverage_percentage"] == 0.0
    assert body["overall_status"] == "pending"
    assert all(floor["status"] == "pending" for floor in body["floor_summaries"])


async def test_leveling_summary_calculates_required_floor_coverage(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    update = await client.patch(f"/api/v1/elevator-floors/{floors[3]['id']}", json={"is_served": False, "is_leveling_required": False})
    assert update.status_code == 200
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=2)]},
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    assert response.status_code == 200
    body = response.json()
    assert body["required_floor_count"] == 3
    assert body["measured_required_floor_count"] == 1
    assert body["coverage_percentage"] == 33.33
    assert body["floor_summaries"][3]["status"] == "not_required"


async def test_leveling_summary_calculates_final_tolerance_percentages(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=4),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=8),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    body = response.json()
    assert body["measurement_count"] == 2
    assert body["within_final_tolerance_count"] == 1
    assert body["out_of_final_tolerance_count"] == 1
    assert body["within_final_tolerance_percentage"] == 50.0
    assert body["floor_summaries"][2]["has_out_of_tolerance_measurement"] is True


async def test_leveling_summary_detects_renivelation_and_acceptability(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], landing_mm=10, final_mm=2),
                measurement_payload(floors[1]["id"], floors[2]["id"], landing_mm=20, final_mm=3),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    body = response.json()
    assert body["renivelation_count"] == 2
    assert body["acceptable_renivelation_count"] == 1
    assert body["acceptable_renivelation_percentage"] == 50.0
    assert body["floor_summaries"][1]["renivelation_ok"] is True
    assert body["floor_summaries"][2]["renivelation_ok"] is False


async def test_leveling_summary_calculates_short_and_long_hysteresis(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], travel_type="short", direction="up", final_mm=4),
                measurement_payload(floors[2]["id"], floors[1]["id"], travel_type="short", direction="down", final_mm=-1),
                measurement_payload(floors[0]["id"], floors[2]["id"], travel_type="long", direction="up", final_mm=8),
                measurement_payload(floors[3]["id"], floors[2]["id"], travel_type="long", direction="down", final_mm=-3),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    body = response.json()
    floor_2 = body["floor_summaries"][1]
    floor_3 = body["floor_summaries"][2]
    assert floor_2["hysteresis"]["short_up_vs_down_mm"] == 5
    assert floor_2["hysteresis"]["short_up_vs_down_ok"] is True
    assert floor_3["hysteresis"]["long_up_vs_down_mm"] == 11
    assert floor_3["hysteresis"]["long_up_vs_down_ok"] is False
    assert body["hysteresis_pairs_count"] == 2
    assert body["hysteresis_ok_count"] == 1
    assert body["hysteresis_ok_percentage"] == 50.0


async def test_leveling_summary_statuses_pending_ok_warning_and_critical(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=2),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=7),
                measurement_payload(floors[2]["id"], floors[3]["id"], final_mm=12),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-summary")

    body = response.json()
    statuses = {floor["floor_label"]: floor["status"] for floor in body["floor_summaries"]}
    assert statuses["1"] == "pending"
    assert statuses["2"] == "ok"
    assert statuses["3"] == "warning"
    assert statuses["4"] == "critical"
    assert body["overall_status"] == "critical"
