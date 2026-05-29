async def create_project(client, name: str = "Megapolis Tower", default_floor_count: int = 62) -> dict:
    response = await client.post(
        "/api/v1/projects",
        json={
            "name": name,
            "client_name": "Megapolis",
            "location": "Panama",
            "total_elevators": 16,
            "default_floor_count": default_floor_count,
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_create_project(client) -> None:
    project = await create_project(client)

    assert project["name"] == "Megapolis Tower"
    assert project["default_floor_count"] == 62
    assert project["status"] == "active"


async def test_list_projects(client) -> None:
    await create_project(client, name="Project A")
    await create_project(client, name="Project B")

    response = await client.get("/api/v1/projects")

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_project_by_id(client) -> None:
    project = await create_project(client)

    response = await client.get(f"/api/v1/projects/{project['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


async def test_update_project(client) -> None:
    project = await create_project(client)

    response = await client.patch(f"/api/v1/projects/{project['id']}", json={"status": "paused"})

    assert response.status_code == 200
    assert response.json()["status"] == "paused"


async def test_create_elevator_inside_project(client) -> None:
    project = await create_project(client)

    response = await client.post(
        f"/api/v1/projects/{project['id']}/elevators",
        json={"code": "L9", "name": "Elevador #9"},
    )

    assert response.status_code == 201
    elevator = response.json()
    assert elevator["project_id"] == project["id"]
    assert elevator["code"] == "L9"
    assert elevator["floor_count"] == 62


async def test_elevator_code_must_be_unique_inside_project(client) -> None:
    project = await create_project(client)
    payload = {"code": "L10", "name": "Elevador #10"}

    first_response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json=payload)
    second_response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_same_elevator_code_is_allowed_in_different_projects(client) -> None:
    project_a = await create_project(client, name="Tower A")
    project_b = await create_project(client, name="Tower B")

    response_a = await client.post(f"/api/v1/projects/{project_a['id']}/elevators", json={"code": "L11"})
    response_b = await client.post(f"/api/v1/projects/{project_b['id']}/elevators", json={"code": "L11"})

    assert response_a.status_code == 201
    assert response_b.status_code == 201


async def test_list_elevators_for_project(client) -> None:
    project = await create_project(client)
    await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L9"})
    await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L10"})

    response = await client.get(f"/api/v1/projects/{project['id']}/elevators")

    assert response.status_code == 200
    assert [item["code"] for item in response.json()] == ["L10", "L9"]


async def test_elevator_creation_generates_default_elevator_floors(client) -> None:
    project = await create_project(client, default_floor_count=62)
    elevator_response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L12"})
    elevator = elevator_response.json()

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/floors?limit=100")

    assert response.status_code == 200
    floors = response.json()
    assert len(floors) == 62
    assert floors[0]["sort_order"] == 1
    assert floors[0]["label"] == "1"
    assert floors[-1]["label"] == "62"
    assert all(floor["is_served"] is True for floor in floors)
    assert all(floor["is_leveling_required"] is True for floor in floors)


async def test_list_elevator_floors(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator_response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L13"})
    elevator = elevator_response.json()

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/floors")

    assert response.status_code == 200
    assert [floor["label"] for floor in response.json()] == ["1", "2", "3"]


async def test_update_elevator_floor_label(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L14"})).json()
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()

    response = await client.patch(f"/api/v1/elevator-floors/{floors[0]['id']}", json={"label": "PB"})

    assert response.status_code == 200
    assert response.json()["label"] == "PB"


async def test_mark_elevator_floor_not_served(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L15"})).json()
    floor = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()[1]

    response = await client.patch(f"/api/v1/elevator-floors/{floor['id']}", json={"is_served": False})

    assert response.status_code == 200
    assert response.json()["is_served"] is False
    assert response.json()["is_leveling_required"] is False


async def test_mark_elevator_floor_leveling_not_required(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L16"})).json()
    floor = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()[2]

    response = await client.patch(f"/api/v1/elevator-floors/{floor['id']}", json={"is_leveling_required": False})

    assert response.status_code == 200
    assert response.json()["is_served"] is True
    assert response.json()["is_leveling_required"] is False


async def test_elevator_floor_sort_order_must_be_unique_per_elevator(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L17"})).json()
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()

    response = await client.patch(f"/api/v1/elevator-floors/{floors[1]['id']}", json={"sort_order": 1})

    assert response.status_code == 409


async def test_elevator_floor_label_must_be_unique_per_elevator_when_present(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L18"})).json()
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()
    first_update = await client.patch(f"/api/v1/elevator-floors/{floors[0]['id']}", json={"label": "PB"})
    second_update = await client.patch(f"/api/v1/elevator-floors/{floors[1]['id']}", json={"label": "PB"})

    assert first_update.status_code == 200
    assert second_update.status_code == 409


async def test_same_floor_label_is_allowed_in_different_elevators(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator_a = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L19"})).json()
    elevator_b = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L20"})).json()
    floor_a = (await client.get(f"/api/v1/elevators/{elevator_a['id']}/floors")).json()[0]
    floor_b = (await client.get(f"/api/v1/elevators/{elevator_b['id']}/floors")).json()[0]

    response_a = await client.patch(f"/api/v1/elevator-floors/{floor_a['id']}", json={"label": "PB"})
    response_b = await client.patch(f"/api/v1/elevator-floors/{floor_b['id']}", json={"label": "PB"})

    assert response_a.status_code == 200
    assert response_b.status_code == 200


async def test_not_served_floor_remains_visible_but_not_required_for_leveling(client) -> None:
    project = await create_project(client, default_floor_count=3)
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "L21"})).json()
    floor = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()[0]

    await client.patch(f"/api/v1/elevator-floors/{floor['id']}", json={"is_served": False})
    floors = (await client.get(f"/api/v1/elevators/{elevator['id']}/floors")).json()
    visible_floor = next(item for item in floors if item["id"] == floor["id"])
    required_floors = [item for item in floors if item["is_served"] and item["is_leveling_required"]]

    assert visible_floor["is_served"] is False
    assert visible_floor["is_leveling_required"] is False
    assert len(required_floors) == 2


async def test_list_seeded_test_types(client) -> None:
    response = await client.get("/api/v1/test-types")

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()]
    assert codes == [
        "LOAD_TEST",
        "FINE_LEVELING",
        "LOAD_COMPENSATION",
        "PARAMETER_ADJUSTMENT",
        "FLOOR_MEASUREMENT",
    ]


async def test_dashboard_overview_returns_real_counts(client) -> None:
    project = await create_project(client, name="Dashboard Project")
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "D1"})).json()
    test_types = (await client.get("/api/v1/test-types")).json()
    fine_leveling = next(item for item in test_types if item["code"] == "FINE_LEVELING")
    await client.post(
        f"/api/v1/elevators/{elevator['id']}/test-runs",
        json={"test_type_id": fine_leveling["id"], "technician_name": "Tech", "status": "completed", "title": "Final pass"},
    )

    response = await client.get("/api/v1/dashboard/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["projects_count"] == 1
    assert body["active_projects_count"] == 1
    assert body["elevators_count"] == 1
    assert body["test_runs_count"] == 1
    assert body["completed_test_runs_count"] == 1
    assert body["latest_projects"][0]["elevators_count"] == 1
    assert body["latest_test_runs"][0]["elevator_code"] == "D1"
    assert body["latest_test_runs"][0]["project_name"] == "Dashboard Project"


async def test_list_global_elevators_with_search_filter(client) -> None:
    project_a = await create_project(client, name="Tower Alpha")
    project_b = await create_project(client, name="Tower Beta")
    await client.post(f"/api/v1/projects/{project_a['id']}/elevators", json={"code": "A9", "name": "Service A"})
    await client.post(f"/api/v1/projects/{project_b['id']}/elevators", json={"code": "B10", "name": "Service B"})

    response = await client.get("/api/v1/elevators?search=beta")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "B10"
    assert body[0]["project_name"] == "Tower Beta"


async def test_list_global_test_runs_with_status_filter(client) -> None:
    project = await create_project(client, name="Test Run Project")
    elevator = (await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": "TR1"})).json()
    test_types = (await client.get("/api/v1/test-types")).json()
    fine_leveling = next(item for item in test_types if item["code"] == "FINE_LEVELING")
    await client.post(
        f"/api/v1/elevators/{elevator['id']}/test-runs",
        json={"test_type_id": fine_leveling["id"], "technician_name": "Ana", "status": "draft", "title": "Draft run"},
    )
    await client.post(
        f"/api/v1/elevators/{elevator['id']}/test-runs",
        json={"test_type_id": fine_leveling["id"], "technician_name": "Ana", "status": "completed", "title": "Completed run"},
    )

    response = await client.get("/api/v1/test-runs?status=completed")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Completed run"
    assert body[0]["elevator_code"] == "TR1"
    assert body[0]["project_name"] == "Test Run Project"
