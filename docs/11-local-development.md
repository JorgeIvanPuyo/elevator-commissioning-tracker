# Local Development

## Backend and Database

Run backend and PostgreSQL with Docker Compose from the repository root:

```bash
docker-compose up --build api postgres
```

The API starts on `http://localhost:8000` and runs Alembic migrations before Uvicorn.

Useful commands:

```bash
docker-compose run --rm --build api alembic upgrade head
docker-compose run --rm --build api pytest
docker-compose logs api
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
