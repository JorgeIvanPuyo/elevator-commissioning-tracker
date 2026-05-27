# CI/CD and Deploy Guide

## Backend CI
GitHub Actions debe ejecutar:
- Instalar dependencias.
- Correr lint opcional.
- Correr pytest.
- Validar import de app.

## Frontend CI
GitHub Actions debe ejecutar:
- Instalar dependencias.
- Typecheck.
- Build.

## Backend Deploy
Cloud Run:
- Imagen Docker.
- Variables:
  - `DATABASE_URL`
  - `GCS_BUCKET_NAME`
  - `ENVIRONMENT`
  - `CORS_ORIGINS`
- Healthcheck:
  - `/health`
  - `/api/v1/health`

## Frontend Deploy
Vercel:
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_APP_NAME`

## Supabase
- Usar PostgreSQL connection string.
- Alembic debe correr contra la base de datos.
- No usar Supabase Auth en MVP porque no se requiere autenticación.

## GCS
- Bucket privado.
- Upload desde backend.
- Frontend recibe URL o signed URL temporal.
- Para MVP se puede guardar `public_url` si el bucket se configura con acceso controlado según necesidad operativa.
