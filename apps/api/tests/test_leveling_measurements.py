from uuid import uuid4

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


async def create_test_run_for_elevator(client, elevator_id: str, title: str) -> dict:
    test_type = await get_test_type(client, "FINE_LEVELING")
    return (
        await client.post(
            f"/api/v1/elevators/{elevator_id}/test-runs",
            json={"test_type_id": test_type["id"], "technician_name": "Tech", "status": "completed", "title": title},
        )
    ).json()


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


async def test_comparison_rejects_test_runs_from_different_elevators(client) -> None:
    elevator_a, _, current = await create_measurement_test_run(client, code="L9")
    elevator_b, _ = await create_elevator_with_floors(client, code="L10")
    baseline = await create_test_run_for_elevator(client, elevator_b["id"], "Baseline")

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={baseline['id']}")

    assert elevator_a["id"] != elevator_b["id"]
    assert response.status_code == 400
    assert "same elevator" in response.json()["detail"]


async def test_comparison_returns_404_when_baseline_does_not_exist(client) -> None:
    _, _, current = await create_measurement_test_run(client)

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={uuid4()}")

    assert response.status_code == 404


async def test_comparison_candidates_exclude_current_test_run(client) -> None:
    elevator, _, current = await create_measurement_test_run(client)
    baseline = await create_test_run_for_elevator(client, elevator["id"], "Baseline")

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison-candidates")

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert baseline["id"] in ids
    assert current["id"] not in ids
    assert response.json()[0]["within_final_tolerance_percentage"] == 0.0


async def test_comparison_calculates_global_kpis_and_improvement(client) -> None:
    elevator, floors, baseline = await create_measurement_test_run(client)
    current = await create_test_run_for_elevator(client, elevator["id"], "Current")
    await client.put(
        f"/api/v1/test-runs/{baseline['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=8),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=2),
            ]
        },
    )
    await client.put(
        f"/api/v1/test-runs/{current['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=3),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=2),
                measurement_payload(floors[2]["id"], floors[3]["id"], final_mm=1),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={baseline['id']}")

    assert response.status_code == 200
    metrics = {item["metric"]: item for item in response.json()["global_metrics"]}
    assert metrics["coverage_percent"]["baseline_value"] == 50.0
    assert metrics["coverage_percent"]["current_value"] == 75.0
    assert metrics["coverage_percent"]["trend"] == "improved"
    assert metrics["final_tolerance_percent"]["baseline_value"] == 50.0
    assert metrics["final_tolerance_percent"]["current_value"] == 100.0
    assert metrics["final_tolerance_percent"]["trend"] == "improved"


async def test_comparison_detects_worsened_final_tolerance(client) -> None:
    elevator, floors, baseline = await create_measurement_test_run(client)
    current = await create_test_run_for_elevator(client, elevator["id"], "Current")
    await client.put(
        f"/api/v1/test-runs/{baseline['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=2)]},
    )
    await client.put(
        f"/api/v1/test-runs/{current['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=9)]},
    )

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={baseline['id']}")

    metrics = {item["metric"]: item for item in response.json()["global_metrics"]}
    assert metrics["final_tolerance_percent"]["trend"] == "worsened"


async def test_comparison_compares_floor_tolerance_and_newly_measured(client) -> None:
    elevator, floors, baseline = await create_measurement_test_run(client)
    current = await create_test_run_for_elevator(client, elevator["id"], "Current")
    await client.put(
        f"/api/v1/test-runs/{baseline['id']}/leveling-measurements/bulk",
        json={"items": [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=8)]},
    )
    await client.put(
        f"/api/v1/test-runs/{current['id']}/leveling-measurements/bulk",
        json={
            "items": [
                measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=3),
                measurement_payload(floors[1]["id"], floors[2]["id"], final_mm=4),
            ]
        },
    )

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={baseline['id']}")

    floors_by_label = {item["floor_label"]: item for item in response.json()["floor_comparisons"]}
    assert floors_by_label["2"]["baseline_status"] == "warning"
    assert floors_by_label["2"]["current_status"] == "ok"
    assert floors_by_label["2"]["trend"] == "improved"
    assert floors_by_label["3"]["trend"] == "newly_measured"


async def test_comparison_compares_modified_parameters_and_decimal_delta(client) -> None:
    elevator, _, baseline = await create_measurement_test_run(client)
    current = await create_test_run_for_elevator(client, elevator["id"], "Current")
    await client.put(
        f"/api/v1/test-runs/{baseline['id']}/parameters",
        json={"values": [{"parameter_code": "026D", "hex_value": "40"}]},
    )
    await client.put(
        f"/api/v1/test-runs/{current['id']}/parameters",
        json={"values": [{"parameter_code": "026D", "hex_value": "45"}]},
    )

    response = await client.get(f"/api/v1/test-runs/{current['id']}/comparison?baseline_test_run_id={baseline['id']}")

    parameters = {item["parameter_code"]: item for item in response.json()["parameter_comparisons"]}
    assert parameters["026D"]["baseline_decimal_value"] == 64
    assert parameters["026D"]["current_decimal_value"] == 69
    assert parameters["026D"]["decimal_delta"] == 5
    assert parameters["026D"]["changed"] is True
