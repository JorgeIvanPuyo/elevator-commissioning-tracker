from test_leveling_measurements import create_elevator_with_floors, create_measurement_test_run, create_test_run_for_elevator, measurement_payload


async def initialize_workflow(client, elevator_id: str) -> dict:
    response = await client.post(f"/api/v1/elevators/{elevator_id}/commissioning-workflow/initialize")
    assert response.status_code in {200, 201}
    return response.json()


async def complete_steps(client, workflow: dict, required_only: bool = False, codes: set[str] | None = None) -> dict:
    for step in workflow["steps"]:
        if required_only and not step["is_required"]:
            continue
        if codes is not None and step["code"] not in codes:
            continue
        response = await client.patch(f"/api/v1/commissioning-steps/{step['id']}", json={"status": "completed"})
        assert response.status_code == 200
    return (await client.get(f"/api/v1/elevators/{workflow['elevator_id']}/commissioning-workflow")).json()


async def save_ok_parameters(client, test_run_id: str) -> None:
    codes = ["026D", "026E", "026F", "270", "271", "272"]
    max_codes = ["273", "274", "275", "276", "277", "278"]
    values = [{"parameter_code": code, "hex_value": "40"} for code in codes]
    values.extend({"parameter_code": code, "hex_value": "45"} for code in max_codes)
    response = await client.put(f"/api/v1/test-runs/{test_run_id}/parameters", json={"values": values})
    assert response.status_code == 200


async def save_measurements(client, test_run_id: str, items: list[dict]) -> None:
    response = await client.put(f"/api/v1/test-runs/{test_run_id}/leveling-measurements/bulk", json={"items": items})
    assert response.status_code == 200


async def test_commissioning_overview_returns_elevator_and_workflow(client) -> None:
    elevator, _, _ = await create_measurement_test_run(client)
    await initialize_workflow(client, elevator["id"])

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")

    assert response.status_code == 200
    body = response.json()
    assert body["elevator"]["id"] == elevator["id"]
    assert body["workflow"]["total_steps"] == 8
    assert len(body["workflow"]["steps"]) == 10


async def test_commissioning_overview_works_without_test_run(client) -> None:
    elevator, _ = await create_elevator_with_floors(client, code="NO-RUN")
    await initialize_workflow(client, elevator["id"])

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")

    body = response.json()
    assert response.status_code == 200
    assert body["latest_test_run"] is None
    assert body["zone_analysis"]["available"] is False
    assert body["final_validation"]["available"] is False


async def test_commissioning_overview_selects_latest_test_run(client) -> None:
    elevator, _, first = await create_measurement_test_run(client)
    second = await create_test_run_for_elevator(client, elevator["id"], "Latest")

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")

    assert response.json()["latest_test_run"]["id"] == second["id"]
    assert response.json()["latest_test_run"]["id"] != first["id"]


async def test_commissioning_overview_load_readiness_false_when_prerequisites_incomplete(client) -> None:
    elevator, _, _ = await create_measurement_test_run(client)
    await initialize_workflow(client, elevator["id"])

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")

    readiness = response.json()["load_readiness"]
    assert readiness["ready_for_leveling"] is False
    assert len(readiness["warnings"]) == 3


async def test_commissioning_overview_load_readiness_true_when_prerequisites_complete(client) -> None:
    elevator, _, _ = await create_measurement_test_run(client)
    workflow = await initialize_workflow(client, elevator["id"])
    await complete_steps(
        client,
        workflow,
        codes={"LOAD_CELL_MECHANICAL_CALIBRATION", "LOAD_MEMORY_ZERO_FULL", "OVERLOAD_110_TEST"},
    )

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")

    readiness = response.json()["load_readiness"]
    assert readiness["ready_for_leveling"] is True
    assert readiness["warnings"] == []


async def test_commissioning_overview_parameter_matrix_counts_ok_warning_and_missing(client) -> None:
    elevator, _, test_run = await create_measurement_test_run(client)
    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={
            "values": [
                {"parameter_code": "026D", "hex_value": "40"},
                {"parameter_code": "273", "hex_value": "45"},
                {"parameter_code": "026E", "hex_value": "40"},
                {"parameter_code": "274", "hex_value": "49"},
                {"parameter_code": "026F", "hex_value": "40"},
            ]
        },
    )

    body = (await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")).json()

    assert body["parameter_matrix"]["ok_windows"] == 1
    assert body["parameter_matrix"]["warning_windows"] == 1
    assert body["parameter_matrix"]["missing_windows"] == 4
    assert body["parameter_matrix"]["most_critical_warning"]


async def test_commissioning_overview_includes_flag_adjustment_summary(client) -> None:
    elevator, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", final_mm=9),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", final_mm=13),
        ],
    )

    body = (await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")).json()

    assert body["flag_adjustments"]["available"] is True
    assert body["flag_adjustments"]["floors_requiring_adjustment"] == 1
    assert body["flag_adjustments"]["max_abs_recommended_movement_mm"] == 11.0


async def test_commissioning_overview_includes_final_validation_summary(client) -> None:
    elevator, floors, test_run = await create_measurement_test_run(client)
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=2),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", measurement_stage="final_validation", final_mm=3),
        ],
    )

    body = (await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")).json()

    assert body["final_validation"]["available"] is True
    assert body["final_validation"]["floors_within_tolerance"] == 1


async def test_commissioning_overview_needs_attention_when_final_validation_out_of_tolerance(client) -> None:
    elevator, floors, test_run = await create_measurement_test_run(client)
    workflow = await initialize_workflow(client, elevator["id"])
    await complete_steps(client, workflow, required_only=True)
    await save_ok_parameters(client, test_run["id"])
    await save_measurements(
        client,
        test_run["id"],
        [
            measurement_payload(floors[0]["id"], floors[1]["id"], direction="down", measurement_stage="final_validation", final_mm=8),
            measurement_payload(floors[2]["id"], floors[1]["id"], direction="up", measurement_stage="final_validation", final_mm=3),
        ],
    )

    body = (await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")).json()

    assert body["overall_status"]["status"] == "needs_attention"
    assert any("fuera de tolerancia" in reason for reason in body["overall_status"]["reasons"])


async def test_commissioning_overview_ready_to_close_when_required_work_is_complete(client) -> None:
    elevator, floors, test_run = await create_measurement_test_run(client)
    workflow = await initialize_workflow(client, elevator["id"])
    await complete_steps(client, workflow, required_only=True)
    await save_ok_parameters(client, test_run["id"])
    items = []
    for index, floor in enumerate(floors):
        origin_down = floors[index - 1] if index > 0 else floors[1]
        origin_up = floors[index + 1] if index < len(floors) - 1 else floors[index - 1]
        items.append(measurement_payload(origin_down["id"], floor["id"], direction="down", measurement_stage="final_validation", final_mm=1))
        items.append(measurement_payload(origin_up["id"], floor["id"], direction="up", measurement_stage="final_validation", final_mm=2))
    await save_measurements(client, test_run["id"], items)

    body = (await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-overview")).json()

    assert body["final_validation"]["ready_to_close"] is True
    assert body["overall_status"]["status"] == "ready_to_close"
