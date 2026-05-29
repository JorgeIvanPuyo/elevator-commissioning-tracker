# Web

Next.js frontend for Megapolis elevator traceability.

## Run Locally

```bash
cd apps/web
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` if the backend is not using the default local URL.

## Current Screens

- `/`: dashboard with backend overview data.
- `/projects`: list and create projects.
- `/projects/[projectId]`: project detail, edit/delete project, elevator list and elevator creation.
- `/elevators`: global elevator list.
- `/elevators/[elevatorId]`: elevator detail, floor labels, test run list and test run creation.
- `/test-runs`: global test run list.
- `/test-runs/[testRunId]`: test run detail, A61E-A67E process checklist, HEX parameter editor, technical parameter matrix, zone analysis and flag movement recommendations.
- `/docs`: static Markdown technical documentation.
- `/docs/[slug]`: Markdown document viewer.

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
