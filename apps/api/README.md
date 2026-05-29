# API

FastAPI backend for Megapolis elevator traceability.

## Implemented Domain

- `Project`
- `Elevator`
- `ElevatorFloor`
- `TestType`
- `TestRun`
- `TestRunProcessStep`
- `ParameterDefinition`
- `TestRunParameterValue`

Parameter values accept HEX input, store normalized HEX, and calculate decimal values in the backend.
A61E, A62E, A65E, A66E and A67E are process steps, not editable HEX parameters.

## Run Locally

```bash
docker-compose up -d postgres postgres_test
docker-compose up --build api postgres
```

## Tests

```bash
docker-compose run --rm --build api pytest
docker-compose run --rm api pytest
```

Tests use `TEST_DATABASE_URL`, not `DATABASE_URL`.

Do not run tests against the development database or Supabase.

Direct WSL2:

```bash
APP_ENV=test \
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
pytest
```

## Migrations

```bash
docker-compose run --rm --build api alembic upgrade head
```

## Healthchecks

- `GET /health`
- `GET /api/v1/health`

## Dashboard/List Endpoints

- `GET /api/v1/dashboard/overview`
- `GET /api/v1/elevators`
- `GET /api/v1/elevators/{elevator_id}/commissioning-overview`
- `GET /api/v1/test-runs`

## Test Run Endpoints

- `GET /api/v1/test-runs/{test_run_id}/process-steps`
- `PATCH /api/v1/test-run-process-steps/{process_step_id}`
- `GET /api/v1/test-runs/{test_run_id}/parameters`
- `PUT /api/v1/test-runs/{test_run_id}/parameters`
- `GET /api/v1/test-runs/{test_run_id}/leveling-summary`
- `GET /api/v1/test-runs/{test_run_id}/zone-leveling-analysis`
- `GET /api/v1/test-runs/{test_run_id}/flag-adjustment-recommendations`
- `GET /api/v1/test-runs/{test_run_id}/final-validation-summary`
