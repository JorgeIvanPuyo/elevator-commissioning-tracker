# Roadmap

Codex debe actualizar este archivo al terminar cada tarea:
- Marcar como completado lo realizado.
- Agregar notas técnicas relevantes.
- Sugerir el siguiente slice recomendado.

## Fase 0 — Setup del repositorio
- [x] Crear monorepo con `apps/api` y `apps/web`.
- [x] Crear `README.md` raíz con comandos.
- [x] Crear `.gitignore`, `.env.example`, `docker-compose.yml`.
- [x] Crear GitHub Actions base para backend tests y frontend build.

## Fase 1 — Backend base
- [x] Crear FastAPI app con healthcheck.
- [x] Configurar settings/env.
- [x] Configurar SQLAlchemy async.
- [x] Configurar Alembic.
- [x] Configurar pytest.
- [x] Crear middleware de request id y logs básicos.

## Fase 2 — Modelo core
- [x] Crear modelos Project, Elevator, TestType.
- [x] Crear modelo ElevatorFloor para nomenclatura real de pisos por elevador.
- [x] Crear migración Alembic.
- [x] Crear CRUD/API para Project.
- [x] Crear CRUD/API para Elevator.
- [x] Crear CRUD/API para ElevatorFloor.
- [x] Crear endpoint de listado para TestType.
- [x] Crear seed de TestType.
- [x] Crear tests API y servicios.
- [x] Aislar base de datos de pruebas con `TEST_DATABASE_URL`.
- [x] Corregir API CI para levantar PostgreSQL en GitHub Actions.

## Fase 3 — Pruebas y parámetros
- [x] Crear TestRun.
- [x] Crear ParameterDefinition.
- [x] Crear TestRunParameterValue.
- [x] Crear seed de parámetros.
- [ ] Crear endpoint para crear TestRun precargando parámetros desde prueba anterior.
- [x] Crear validación HEX->decimal.
- [x] Crear validación min/max.

## Fase 4 — Nivelación
- [ ] Crear LevelingMeasurement.
- [ ] Crear endpoint bulk save.
- [ ] Calcular tolerancia final.
- [ ] Calcular renivelación.
- [ ] Calcular histerisis.
- [ ] Calcular recomendación de bandera.
- [ ] Crear endpoint resumen por elevador.

## Fase 5 — Evidencias
- [ ] Configurar GCS.
- [ ] Crear Evidence.
- [ ] Endpoint de upload.
- [ ] Endpoint de listado.
- [ ] Tests con mock de storage.

## Fase 6 — Frontend base
- [x] Crear Next.js app.
- [x] Configurar Tailwind.
- [x] Crear layout responsive.
- [x] Crear API client.
- [x] Crear dashboard inicial.
- [x] Crear navegación principal.

## Fase 7 — Frontend operativo MVP
- [ ] CRUD proyectos.
- [ ] CRUD elevadores.
- [x] Detalle elevador.
- [x] Lista de pruebas.
- [x] Crear nueva prueba.
- [x] Editor de parámetros HEX/decimal.
- [x] Autosave local.

## Fase 8 — Nivelación visual
- [ ] Crear mapa de 62 pisos.
- [ ] Crear formulario de mediciones.
- [ ] Crear KPIs por prueba.
- [ ] Crear comparación prueba actual vs anterior.
- [ ] Crear indicadores verde/amarillo/rojo.

## Fase 9 — Documentación técnica
- [ ] Crear página de documentos.
- [ ] Renderizar Markdown por slug.
- [ ] Enlazar cada test type a su documento.
- [ ] Bloquear descarga directa innecesaria desde UI.

## Fase 10 — Deploy
- [x] Dockerfile backend.
- [ ] Deploy Cloud Run.
- [ ] Configurar Supabase connection string.
- [ ] Deploy Vercel frontend.
- [ ] Variables de entorno.
- [ ] Prueba end-to-end manual en celular.

## Fase 11 — Reportes
- [ ] Diseñar reporte por elevador.
- [ ] Incluir pruebas, resultados y evidencias.
- [ ] Exportar PDF desde backend.

## Notas de Slice 1
- Se creó una base monorepo con backend FastAPI mínimo y frontend Next.js App Router.
- Backend expone `GET /health` y `GET /api/v1/health`, con CORS configurable y header `x-request-id`.
- SQLAlchemy async y Alembic quedaron configurados sin modelos de negocio todavía.
- Frontend incluye shell responsive inicial y navegación placeholder, sin CRUD.
- Siguiente slice recomendado: Fase 2, crear modelos `Project`, `Elevator`, `TestType`, primera migración Alembic, seed de tipos de prueba y endpoints CRUD mínimos para proyecto/elevadores.

## Notas de Slice 2
- Se implementaron modelos `Project`, `Elevator`, `TestType` y `ElevatorFloor`.
- La migración crea tablas, índices, constraints únicos y seed inicial de tipos de prueba.
- La decisión de dominio confirmada es `Project -> Elevators -> ElevatorFloors`; no `Project -> FloorLabels`.
- Al crear un elevador se generan automáticamente `ElevatorFloor` del `1` al `floor_count`.
- El código de elevador es único por proyecto.
- El `sort_order` de piso es único por elevador y `label` es único por elevador cuando no es nulo/vacío.
- Los pisos no servidos permanecen visibles, pero no contarán para KPIs futuros de nivelación obligatoria.
- El backend sigue corriendo por Docker Compose; el frontend queda documentado para ejecución directa en WSL2.
- Fix técnico cerrado: pytest usa un engine propio con `TEST_DATABASE_URL`, valida que sea una base de test y no toca la base de desarrollo.
- GitHub Actions de API levanta PostgreSQL como service container y ejecuta pytest con `APP_ENV=test`.
- Siguiente slice recomendado: Fase 3, crear `TestRun`, `ParameterDefinition`, `TestRunParameterValue`, seed de parámetros y validación HEX/decimal.

## Notas de Slice 3
- Se implementaron `TestRun`, `ParameterDefinition` y `TestRunParameterValue`.
- Se agregó migración Alembic con tablas, índices, constraints y seed inicial de parámetros técnicos.
- Los valores HEX se normalizan en backend, se convierten a decimal y rechazan entradas inválidas.
- El guardado bulk de parámetros valida pares min/max por metadata (`bound_type` + `pair_code`) y evita persistencia parcial si hay errores.
- El frontend permite crear/listar pruebas desde el detalle de elevador y editar parámetros desde `/test-runs/{testRunId}`.
- El editor de parámetros muestra preview decimal, errores HEX inline, errores backend y borrador local en `localStorage`.
- Siguiente slice recomendado: Fase 4, crear mediciones de nivelación piso a piso (`LevelingMeasurement`) con bulk save y tolerancias mínimas.
