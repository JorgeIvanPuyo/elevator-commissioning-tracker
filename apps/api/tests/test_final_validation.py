from test_leveling_measurements import create_measurement_test_run, measurement_payload


async def save_measurements(client, test_run_id: str, items: list[dict]) -> None:
    response = await client.put(f"/api/v1/test-runs/{test_run_id}/leveling-measurements/bulk", json={"items": items})
    assert response.status_code == 200


async def test_measurement_stage_defaults_to_floor_by_floor(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    await save_measurements(client, test_run["id"], [measurement_payload(floors[0]["id"], floors[1]["id"], final_mm=2)])
    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements")

    assert response.status_code == 200
    assert response.json()["items"][0]["measurement_stage"] == "floor_by_floor"


async def test_bulk_save_accepts_final_validation_stage(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)

    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[0]["id"], floors[1]["id"], measurement_stage="final_validation", final_mm=3)],
    )
    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/leveling-measurements?measurement_stage=final_validation")

    assert response.status_code == 200
    assert response.json()["items"][0]["measurement_stage"] == "final_validation"


async def test_final_validation_summary_uses_only_final_validation_measurements(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=12),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=12),
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=2),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", measurement_stage="final_validation", final_mm=3),
        ],
    )

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")

    row = next(item for item in response.json()["rows"] if item["floor_id"] == floors[1]["id"])
    assert row["down_final_mm"] == 2.0
    assert row["up_final_mm"] == 3.0
    assert row["status"] == "ok"


async def test_final_validation_detects_out_of_tolerance(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=2),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", measurement_stage="final_validation", final_mm=8),
        ],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")).json()
    row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])

    assert row["status"] == "out_of_tolerance"
    assert row["within_tolerance"] is False


async def test_final_validation_partial_and_missing_data(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=2)],
    )

    body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")).json()
    partial_row = next(item for item in body["rows"] if item["floor_id"] == floors[1]["id"])
    missing_row = next(item for item in body["rows"] if item["floor_id"] == floors[2]["id"])

    assert partial_row["status"] == "partial_data"
    assert missing_row["status"] == "missing_data"


async def test_final_validation_summary_percentages(client) -> None:
    _, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=2),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", measurement_stage="final_validation", final_mm=3),
            measurement_payload(floors[0]["id"], floors[2]["id"], direction="down", measurement_stage="final_validation", final_mm=8),
            measurement_payload(floors[1]["id"], floors[2]["id"], direction="up", measurement_stage="final_validation", final_mm=4),
            measurement_payload(floors[0]["id"], floors[3]["id"], direction="down", measurement_stage="final_validation", final_mm=1),
        ],
    )

    summary = (await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")).json()["summary"]

    assert summary["total_required_floors"] == 4
    assert summary["floors_with_complete_data"] == 2
    assert summary["floors_within_tolerance"] == 1
    assert summary["floors_out_of_tolerance"] == 1
    assert summary["floors_partial_data"] == 1
    assert summary["floors_missing_data"] == 1
    assert summary["completion_percent"] == 50.0
    assert summary["within_tolerance_percent"] == 50.0
    assert summary["max_abs_final_mm"] == 8.0


async def test_final_validation_exposes_fhm_status(client) -> None:
    elevator, _, test_run = await create_measurement_test_run(client)
    workflow = (await client.post(f"/api/v1/elevators/{elevator['id']}/commissioning-workflow/initialize")).json()
    fhm_step = next(step for step in workflow["steps"] if step["code"] == "FHM_RUN")

    pending_body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")).json()
    await client.patch(f"/api/v1/commissioning-steps/{fhm_step['id']}", json={"status": "completed"})
    completed_body = (await client.get(f"/api/v1/test-runs/{test_run['id']}/final-validation-summary")).json()

    assert pending_body["fhm_completed"] is False
    assert pending_body["fhm_step_status"] == "pending"
    assert completed_body["fhm_completed"] is True
    assert completed_body["fhm_step_status"] == "completed"
