# Web

Next.js frontend for Megapolis elevator traceability.

## Run Locally

```bash
cd apps/web
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` if the backend is not using the default local URL.

## Checks

```bash
npm run typecheck
npm run build
```

## Optional Docker

From the repository root:

```bash
docker-compose -f docker-compose.yml -f docker-compose.full.yml up --build web
```
