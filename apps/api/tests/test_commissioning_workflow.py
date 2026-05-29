from test_core_crud import create_project
from test_test_runs_and_parameters import get_test_type


EXPECTED_STEP_CODES = [
    "LOAD_CELL_MECHANICAL_CALIBRATION",
    "LOAD_MEMORY_ZERO_FULL",
    "OVERLOAD_110_TEST",
    "AUTO_LEVELING_A65E_A66E",
    "AUTO_GAIN_COMPENSATION_A67E",
    "ZONE_FINE_LEVELING",
    "FLOOR_BY_FLOOR_MEASUREMENT",
    "FLAG_ADJUSTMENT",
    "FHM_RUN",
    "FINAL_LEVELING_VALIDATION",
]


async def create_elevator(client, code: str = "CW1") -> dict:
    project = await create_project(client, name=f"Commissioning {code}", default_floor_count=4)
    response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": code, "name": f"Elevador {code}"})
    assert response.status_code == 201
    return response.json()


async def initialize_workflow(client, elevator_id: str) -> dict:
    response = await client.post(f"/api/v1/elevators/{elevator_id}/commissioning-workflow/initialize")
    assert response.status_code == 201
    return response.json()


async def test_initialize_workflow_for_elevator(client) -> None:
    elevator = await create_elevator(client)

    workflow = await initialize_workflow(client, elevator["id"])

    assert workflow["elevator_id"] == elevator["id"]
    assert workflow["status"] == "not_started"
    assert len(workflow["steps"]) == 10


async def test_initialize_workflow_twice_is_idempotent(client) -> None:
    elevator = await create_elevator(client, code="CW2")

    first = await initialize_workflow(client, elevator["id"])
    second = await initialize_workflow(client, elevator["id"])

    assert second["id"] == first["id"]
    assert len(second["steps"]) == 10
    assert [step["code"] for step in second["steps"]] == EXPECTED_STEP_CODES


async def test_default_workflow_has_expected_ordered_steps(client) -> None:
    elevator = await create_elevator(client, code="CW3")

    workflow = await initialize_workflow(client, elevator["id"])

    assert [step["code"] for step in workflow["steps"]] == EXPECTED_STEP_CODES
    assert [step["sort_order"] for step in workflow["steps"]] == list(range(1, 11))


async def test_required_blocking_flags_are_correct_for_first_three_steps(client) -> None:
    elevator = await create_elevator(client, code="CW4")

    workflow = await initialize_workflow(client, elevator["id"])

    first_three = workflow["steps"][:3]
    assert [step["is_required"] for step in first_three] == [True, True, True]
    assert [step["is_blocking"] for step in first_three] == [True, True, True]
    assert all(step["is_blocking"] is False for step in workflow["steps"][3:])
    assert workflow["steps"][3]["is_required"] is False
    assert workflow["steps"][4]["is_required"] is False


async def test_get_workflow_by_elevator(client) -> None:
    elevator = await create_elevator(client, code="CW5")
    created = await initialize_workflow(client, elevator["id"])

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-workflow")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_workflow_returns_404_when_missing(client) -> None:
    elevator = await create_elevator(client, code="CW6")

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/commissioning-workflow")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


async def test_patch_workflow_metadata(client) -> None:
    elevator = await create_elevator(client, code="CW7")
    workflow = await initialize_workflow(client, elevator["id"])

    response = await client.patch(
        f"/api/v1/commissioning-workflows/{workflow['id']}",
        json={"status": "in_progress", "technician_name": "Ana", "notes": "Carga inicial lista"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["technician_name"] == "Ana"
    assert body["notes"] == "Carga inicial lista"


async def test_patch_step_status_completed_auto_sets_completed_at(client) -> None:
    elevator = await create_elevator(client, code="CW8")
    workflow = await initialize_workflow(client, elevator["id"])
    step = workflow["steps"][0]

    response = await client.patch(f"/api/v1/commissioning-steps/{step['id']}", json={"status": "completed", "technician_name": "Ana"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["technician_name"] == "Ana"
    assert body["completed_at"] is not None


async def test_patch_step_status_away_from_completed_clears_completed_at(client) -> None:
    elevator = await create_elevator(client, code="CW9")
    workflow = await initialize_workflow(client, elevator["id"])
    step = workflow["steps"][0]
    completed = (await client.patch(f"/api/v1/commissioning-steps/{step['id']}", json={"status": "completed"})).json()
    assert completed["completed_at"] is not None

    response = await client.patch(f"/api/v1/commissioning-steps/{step['id']}", json={"status": "in_progress"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["completed_at"] is None


async def test_operational_dashboard_returns_elevator_project_and_workflow_summary(client) -> None:
    elevator = await create_elevator(client, code="CW10")
    workflow = await initialize_workflow(client, elevator["id"])
    await client.patch(f"/api/v1/commissioning-steps/{workflow['steps'][0]['id']}", json={"status": "completed"})
    test_type = await get_test_type(client, "FINE_LEVELING")
    test_run_response = await client.post(
        f"/api/v1/elevators/{elevator['id']}/test-runs",
        json={"test_type_id": test_type["id"], "technician_name": "Luis", "status": "completed", "title": "Medición base"},
    )
    assert test_run_response.status_code == 201

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/operational-dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["elevator"]["id"] == elevator["id"]
    assert body["project"]["name"] == "Commissioning CW10"
    assert body["workflow"]["id"] == workflow["id"]
    assert body["workflow"]["total_steps"] == 10
    assert body["workflow"]["completed_steps"] == 1
    assert body["workflow"]["required_blocking_steps_incomplete"] == 2
    assert body["latest_test_run"]["name"] == "Medición base"
    assert body["leveling_summary"]["overall_status"] == "pending"
    assert body["parameter_summary"]["warning_count"] == 0
    assert body["quick_links"]["latest_test_run_id"] == test_run_response.json()["id"]


async def test_operational_dashboard_handles_elevator_without_workflow(client) -> None:
    elevator = await create_elevator(client, code="CW11")

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/operational-dashboard")

    assert response.status_code == 200
    body = response.json()
    assert body["elevator"]["id"] == elevator["id"]
    assert body["workflow"] is None
    assert body["latest_test_run"] is None
    assert body["leveling_summary"] is None
    assert body["parameter_summary"]["latest_test_run_id"] is None
