# Megapolis Elevator Traceability

Monorepo for elevator load testing and fine leveling traceability.

## Apps

- `apps/api`: FastAPI backend.
- `apps/web`: Next.js frontend.

## Local Development

Backend and databases run with Docker Compose:

```bash
docker-compose up -d postgres postgres_test
docker-compose up --build api postgres
```

API healthchecks:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/api/v1/health`

Frontend runs directly from WSL2:

```bash
cd apps/web
npm install
npm run dev
```

Open `http://localhost:3000`.

## Backend Commands

```bash
docker-compose run --rm --build api alembic upgrade head
docker-compose run --rm api pytest
```

Backend tests always use `TEST_DATABASE_URL` and reset only the test database.

Never run backend tests against the development database or Supabase.

Direct WSL2 test command:

```bash
cd apps/api
APP_ENV=test \
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
pytest
```

## Optional Full Docker Stack

```bash
docker-compose -f docker-compose.yml -f docker-compose.full.yml up --build
```

## Environment

Copy `.env.example` to `.env` for local development. Do not commit real secrets.
