# API

FastAPI backend for Megapolis elevator traceability.

## Run Locally

```bash
docker-compose up -d postgres postgres_test
docker-compose up --build api postgres
```

## Tests

```bash
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
