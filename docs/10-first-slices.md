# Recommended First Slices

## Slice 1 — Monorepo + backend healthcheck
Objetivo:
Tener estructura base lista, backend levantando en local con Docker, endpoint `/health` y pytest funcionando.

Resultado esperado:
- `apps/api` creado.
- FastAPI responde.
- Docker Compose levanta backend.
- Test de healthcheck pasa.

## Slice 2 — Project + Elevator CRUD
Objetivo:
Crear la base operativa para registrar proyecto y elevadores.

Resultado esperado:
- Modelos Project y Elevator.
- Modelo ElevatorFloor asociado a elevadores.
- Migración Alembic.
- CRUD API.
- Tests.
- Frontend aún no necesario.

## Slice 3 — Frontend shell
Objetivo:
Crear Next.js app con layout principal, dashboard vacío y navegación.

Resultado esperado:
- Vercel-ready.
- API client central.
- Layout responsive.

## Slice 4 — TestRun + Parameters
Objetivo:
Registrar una prueba y sus parámetros, con conversión HEX/decimal y validación min/max.

Resultado esperado:
- Crear prueba.
- Precargar parámetros desde prueba anterior.
- Editar parámetros.
- Guardar.
- Validar min/max.

## Slice 5 — Nivelación piso a piso
Objetivo:
Registrar mediciones y calcular KPIs mínimos.

Resultado esperado:
- Bulk save de mediciones.
- Cálculo de tolerancia.
- Resumen por prueba.
- Mapa inicial de pisos en frontend.

## Slice 6 — Evidencias
Objetivo:
Subir foto/video a GCS y asociarlo a una prueba.

Resultado esperado:
- Upload endpoint.
- Listado evidencias.
- Card en frontend.
