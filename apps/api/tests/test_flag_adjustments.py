from uuid import uuid4

from test_leveling_measurements import create_measurement_test_run, measurement_payload


async def save_measurements(client, test_run_id: str, items: list[dict]) -> None:
    response = await client.put(f"/api/v1/test-runs/{test_run_id}/leveling-measurements/bulk", json={"items": items})
    assert response.status_code == 200


async def test_flag_adjustments_returns_404_for_unknown_test_run(client) -> None:
    response = await client.get(f"/api/v1/test-runs/{uuid4()}/flag-adjustment-recommendations")

    assert response.status_code == 404


async def test_flag_adjustments_returns_required_floor_rows_sorted(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await client.patch(f"/api/v1/elevator-floors/{floors[2]['id']}", json={"is_served": False, "is_leveling_required": False})

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")

    assert response.status_code == 200
    rows = response.json()["rows"]
    assert [row["sort_order"] for row in rows] == [1, 2, 4]
    assert all(row["floor_id"] != floors[2]["id"] for row in rows)


async def test_flag_adjustment_positive_high_average_recommends_negative_movement(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=9),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=13),
        ],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()
    row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])

    assert row["down_final_mm"] == 9.0
    assert row["up_final_mm"] == 13.0
    assert row["average_final_mm"] == 11.0
    assert row["recommended_flag_movement_mm"] == -11.0
    assert row["status"] == "requires_adjustment"


async def test_flag_adjustment_negative_low_average_recommends_positive_half_movement(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=-6),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=-9),
        ],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()
    row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])

    assert row["average_final_mm"] == -7.5
    assert row["recommended_flag_movement_mm"] == 7.5
    assert row["status"] == "requires_adjustment"


async def test_flag_adjustment_within_tolerance_recommends_zero(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=0),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=2),
        ],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()
    row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])

    assert row["recommended_flag_movement_mm"] == 0.0
    assert row["status"] == "ok"
    assert row["within_tolerance"] is True


async def test_flag_adjustment_partial_and_missing_data_statuses(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=8)],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()
    partial_row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])
    missing_row = next(item for item in body["rows"] if item["floor_id"] == floors[2]["id"])

    assert partial_row["status"] == "partial_data"
    assert partial_row["recommended_flag_movement_mm"] is None
    assert missing_row["status"] == "missing_data"
    assert missing_row["recommended_flag_movement_mm"] is None


async def test_flag_adjustment_summary_counts(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=0),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=2),
            measurement_payload(floors[0]["id"], floors[2]["id"], direction="down", final_mm=9),
            measurement_payload(floors[1]["id"], floors[2]["id"], direction="up", final_mm=13),
            measurement_payload(floors[0]["id"], floors[3]["id"], direction="down", final_mm=6),
        ],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()

    assert body["summary"] == {
        "total_required_floors": 4,
        "floors_with_complete_data": 2,
        "floors_within_tolerance": 1,
        "floors_requiring_flag_adjustment": 1,
        "floors_missing_data": 1,
        "floors_partial_data": 1,
        "max_abs_recommended_movement_mm": 11.0,
    }


async def test_flag_adjustment_uses_latest_measurement_per_floor_direction(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", travel_type="short", final_mm=12)],
    )
    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[2]["id"], floors[1]["id"], direction="down", travel_type="long", final_mm=4)],
    )
    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=4)],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/flag-adjustment-recommendations")).json()
    row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])

    assert row["down_final_mm"] == 4.0
    assert row["status"] == "ok"
    assert row["recommended_flag_movement_mm"] == 0.0
