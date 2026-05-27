# Local Development

## Backend and Database

Run backend and PostgreSQL with Docker Compose from the repository root:

```bash
docker-compose up -d postgres postgres_test
docker-compose up --build api postgres
```

The API starts on `http://localhost:8000` and runs Alembic migrations before Uvicorn.

Databases:
- Development: `postgresql+asyncpg://postgres:postgres@postgres:5432/elevator_commissioning`
- Tests in Docker Compose: `postgresql+asyncpg://postgres:postgres@postgres_test:5432/elevator_commissioning_test`
- Tests from WSL2 host: `postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test`

Useful commands:

```bash
docker-compose run --rm --build api alembic upgrade head
docker-compose run --rm api pytest
docker-compose logs api
```

## Backend Test Safety

Backend tests never use `DATABASE_URL`; pytest creates its own engine from `TEST_DATABASE_URL`.

`TEST_DATABASE_URL` is required. If it is missing, tests fail with:

```txt
TEST_DATABASE_URL is required to run backend tests safely.
```

The fixture also refuses to reset a database URL that does not clearly look like a test database.

Los tests nunca deben ejecutarse contra la base de datos de desarrollo ni contra Supabase. Siempre deben usar `TEST_DATABASE_URL`.

Run tests directly from WSL2:

```bash
cd apps/api
APP_ENV=test \
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/elevator_commissioning_test \
pytest
```

Before opening a PR:

```bash
docker-compose up -d postgres postgres_test
docker-compose run --rm api pytest
cd apps/web
npm run typecheck
npm run build
```

## Frontend

Run the frontend directly from WSL2:

```bash
cd apps/web
npm install
npm run dev
```

The frontend starts on `http://localhost:3000`.

Required local variable:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Optional Full Docker Stack

The web container is available as an alternative, not the primary local flow:

```bash
docker-compose -f docker-compose.yml -f docker-compose.full.yml up --build
```

## LocalStorage Note

Long-form draft persistence with `localStorage` is intentionally deferred to Slice 4, when test runs and parameter forms are implemented.
