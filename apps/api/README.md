# API

FastAPI backend for Megapolis elevator traceability.

## Run Locally

```bash
docker-compose up --build api postgres
```

## Tests

```bash
docker-compose run --rm --build api pytest
```

## Migrations

```bash
docker-compose run --rm --build api alembic upgrade head
```

## Healthchecks

- `GET /health`
- `GET /api/v1/health`
