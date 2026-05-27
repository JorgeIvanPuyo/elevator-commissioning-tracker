import pytest

from app.utils.hex_values import normalize_hex_value

from test_core_crud import create_project


async def create_elevator(client, code: str = "L9") -> dict:
    project = await create_project(client, default_floor_count=3)
    response = await client.post(f"/api/v1/projects/{project['id']}/elevators", json={"code": code})
    assert response.status_code == 201
    return response.json()


async def get_test_type(client, code: str = "FINE_LEVELING") -> dict:
    response = await client.get("/api/v1/test-types")
    assert response.status_code == 200
    return next(item for item in response.json() if item["code"] == code)


async def create_test_run(client, elevator_id: str, test_type_code: str = "FINE_LEVELING") -> dict:
    test_type = await get_test_type(client, test_type_code)
    response = await client.post(
        f"/api/v1/elevators/{elevator_id}/test-runs",
        json={
            "test_type_id": test_type["id"],
            "technician_name": "Ivan Puyo",
            "status": "draft",
            "title": "Iteración inicial",
        },
    )
    assert response.status_code == 201
    return response.json()


async def test_create_test_run_for_elevator(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    assert test_run["elevator_id"] == elevator["id"]
    assert test_run["test_type_code"] == "FINE_LEVELING"
    assert test_run["technician_name"] == "Ivan Puyo"
    assert test_run["status"] == "draft"


async def test_list_test_runs_for_elevator(client) -> None:
    elevator = await create_elevator(client)
    await create_test_run(client, elevator["id"], "FINE_LEVELING")
    await create_test_run(client, elevator["id"], "LOAD_TEST")

    response = await client.get(f"/api/v1/elevators/{elevator['id']}/test-runs")

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_test_run_by_id(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == test_run["id"]


async def test_update_test_run_status_and_notes(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.patch(
        f"/api/v1/test-runs/{test_run['id']}",
        json={"status": "in_progress", "notes": "Ajuste iniciado"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"
    assert response.json()["notes"] == "Ajuste iniciado"


async def test_reject_invalid_test_run_status(client) -> None:
    elevator = await create_elevator(client)
    test_type = await get_test_type(client)

    response = await client.post(
        f"/api/v1/elevators/{elevator['id']}/test-runs",
        json={"test_type_id": test_type["id"], "technician_name": "Ivan", "status": "done"},
    )

    assert response.status_code == 422


async def test_reject_missing_technician_name(client) -> None:
    elevator = await create_elevator(client)
    test_type = await get_test_type(client)

    response = await client.post(f"/api/v1/elevators/{elevator['id']}/test-runs", json={"test_type_id": test_type["id"]})

    assert response.status_code == 422


async def test_list_seeded_parameter_definitions(client) -> None:
    response = await client.get("/api/v1/parameter-definitions?limit=100")

    assert response.status_code == 200
    codes = [item["code"] for item in response.json()]
    assert "026D" in codes
    assert "273" in codes
    assert "022F" in codes
    assert all(code not in codes for code in ["A61E", "A62E", "A65E", "A66E", "A67E"])


async def test_process_steps_are_created_for_test_run(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.get(f"/api/v1/test-runs/{test_run['id']}/process-steps")

    assert response.status_code == 200
    steps = response.json()
    assert [step["code"] for step in steps] == ["A61E", "A62E", "A65E", "A66E", "A67E"]
    assert all(step["is_completed"] is False for step in steps)


async def test_process_step_can_be_completed_with_notes(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])
    steps = (await client.get(f"/api/v1/test-runs/{test_run['id']}/process-steps")).json()

    response = await client.patch(
        f"/api/v1/test-run-process-steps/{steps[0]['id']}",
        json={"is_completed": True, "notes": "Ejecutado en control"},
    )

    assert response.status_code == 200
    assert response.json()["is_completed"] is True
    assert response.json()["completed_at"] is not None
    assert response.json()["notes"] == "Ejecutado en control"


def test_hex_utility_accepts_and_normalizes_values() -> None:
    assert normalize_hex_value("40") == ("40", 64)
    assert normalize_hex_value("0x40") == ("40", 64)
    assert normalize_hex_value("0X40") == ("40", 64)
    assert normalize_hex_value("022f") == ("022F", 559)
    assert normalize_hex_value("") == (None, None)
    assert normalize_hex_value(None) == (None, None)


def test_hex_utility_rejects_invalid_values() -> None:
    with pytest.raises(Exception, match="Invalid HEX value"):
        normalize_hex_value("12G")


async def test_save_parameter_value_and_decimal_conversion(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={"values": [{"parameter_code": "026D", "hex_value": "0x40", "source": "manual", "notes": "Initial"}]},
    )

    assert response.status_code == 200
    value = response.json()["values"][0]
    assert value["parameter_code"] == "026D"
    assert value["hex_value"] == "40"
    assert value["decimal_value"] == 64


async def test_upsert_parameter_value_for_same_test_run_and_parameter(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={"values": [{"parameter_code": "026D", "hex_value": "40", "source": "manual"}]},
    )
    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={"values": [{"parameter_code": "026D", "hex_value": "41", "source": "manual"}]},
    )

    assert response.status_code == 200
    values = response.json()["values"]
    assert len(values) == 1
    assert values[0]["decimal_value"] == 65


async def test_reject_unknown_parameter_code(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={"values": [{"parameter_code": "NOPE", "hex_value": "40"}]},
    )

    assert response.status_code == 400
    assert "Unknown parameter code" in response.json()["detail"]


async def test_min_max_pair_success_when_max_is_greater_or_equal(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={
            "values": [
                {"parameter_code": "026D", "hex_value": "40"},
                {"parameter_code": "273", "hex_value": "45"},
            ]
        },
    )

    assert response.status_code == 200
    values = {item["parameter_code"]: item for item in response.json()["values"]}
    assert values["026D"]["decimal_value"] == 64
    assert values["273"]["decimal_value"] == 69


async def test_min_max_pair_warning_when_max_is_less_than_min(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={
            "values": [
                {"parameter_code": "026D", "hex_value": "45"},
                {"parameter_code": "273", "hex_value": "40"},
            ]
        },
    )

    assert response.status_code == 200
    body = response.json()
    values = {item["parameter_code"]: item for item in body["values"]}
    assert values["026D"]["decimal_value"] == 69
    assert values["273"]["decimal_value"] == 64
    assert body["validation_warnings"] == [
        {
            "type": "MIN_MAX_INCONSISTENCY",
            "parameter_code": "273",
            "paired_parameter_code": "026D",
            "message": "El valor máximo 273 es menor que el mínimo 026D.",
            "severity": "warning",
        }
    ]


async def test_min_max_warning_does_not_roll_back_bulk_save(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={
            "values": [
                {"parameter_code": "026D", "hex_value": "45"},
                {"parameter_code": "273", "hex_value": "40"},
            ]
        },
    )
    persisted = await client.get(f"/api/v1/test-runs/{test_run['id']}/parameters")

    assert response.status_code == 200
    assert persisted.status_code == 200
    assert len(persisted.json()["values"]) == 2
    assert persisted.json()["validation_warnings"]


async def test_invalid_bulk_update_does_not_persist_partial_values(client) -> None:
    elevator = await create_elevator(client)
    test_run = await create_test_run(client, elevator["id"])

    response = await client.put(
        f"/api/v1/test-runs/{test_run['id']}/parameters",
        json={
            "values": [
                {"parameter_code": "026D", "hex_value": "40"},
                {"parameter_code": "273", "hex_value": "ZZ"},
            ]
        },
    )
    persisted = await client.get(f"/api/v1/test-runs/{test_run['id']}/parameters")

    assert response.status_code == 400
    assert persisted.status_code == 200
    assert persisted.json()["values"] == []
