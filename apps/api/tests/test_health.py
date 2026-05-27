async def test_root_healthcheck(client) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}
    assert "x-request-id" in response.headers


async def test_v1_healthcheck(client) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api"}
    assert "x-request-id" in response.headers
