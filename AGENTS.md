# AGENTS.md

This repository contains an elevator load testing and fine leveling traceability app.

## Read first
Before making changes, read:
- `docs/00-project-context.md`
- `docs/01-domain-model.md`
- `docs/02-business-rules.md`
- `docs/06-roadmap.md`
- `docs/07-codex-working-rules.md`

## Architecture
- Monorepo with:
  - `apps/api`: FastAPI backend.
  - `apps/web`: Next.js frontend.
- Backend uses PostgreSQL/Supabase, SQLAlchemy async, Alembic, pytest.
- Frontend uses Next.js, TypeScript, Tailwind and responsive UI.
- Evidence files go to Google Cloud Storage.
- Backend deploys to Cloud Run.
- Frontend deploys to Vercel.

## Development rule
Work slice by slice. Do not build too much at once.

## Done means
- Code implemented.
- Tests added or updated.
- Commands executed.
- Roadmap updated.
- Next slice recommended.
