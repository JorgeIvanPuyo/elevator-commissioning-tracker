# Roadmap

Codex debe actualizar este archivo al terminar cada tarea:
- Marcar como completado lo realizado.
- Agregar notas técnicas relevantes.
- Sugerir el siguiente slice recomendado.

Este roadmap queda como vista ejecutiva. El detalle operativo del nuevo enfoque guiado vive en
[`docs/12-guided-commissioning-roadmap.md`](./12-guided-commissioning-roadmap.md).

## 1. Estado implementado hasta ahora

El sistema ya conserva una base funcional para trazabilidad técnica de elevadores:

- Monorepo con `apps/api` y `apps/web`.
- Backend FastAPI, SQLAlchemy async, Alembic, PostgreSQL y pytest.
- Frontend Next.js, TypeScript, Tailwind y UI responsive.
- CI/CD base con GitHub Actions.
- Base de datos de pruebas aislada con `TEST_DATABASE_URL`.
- CRUD/API de proyectos.
- CRUD/API de elevadores.
- Pisos por elevador con `ElevatorFloor`.
- Catálogo `TestType`.
- `TestRun` para pruebas e iteraciones técnicas.
- `TestRunProcessStep` para procesos A61E, A62E, A65E, A66E y A67E.
- `ParameterDefinition` y `TestRunParameterValue`.
- Editor de parámetros HEX con conversión decimal calculada por backend.
- Warnings no bloqueantes para inconsistencias min/max.
- `LevelingMeasurement`.
- Mediciones de nivelación por origen/destino, dirección y tipo de viaje.
- Resumen/KPIs de nivelación por `TestRun`.
- Comparación calculada entre iteraciones de `TestRun`.
- Dashboard, listados globales, navegación principal y documentación Markdown básica.

## 2. Cambio de enfoque del producto

La aplicación deja de estar centrada principalmente en comparación exploratoria de pruebas:

```txt
Elevador -> muchas pruebas -> comparación exploratoria -> encontrar patrón
```

Desde este punto debe evolucionar hacia una herramienta de campo guiada:

```txt
Elevador -> workflow guiado -> pasos técnicos -> cálculo de ajuste -> validación final
```

El producto debe funcionar como:

```txt
Guía técnica + calculadora de nivelación fina + trazabilidad por elevador
```

`TestRun` sigue existiendo y no debe eliminarse, pero ya no será el centro principal de la experiencia de usuario. El centro será el workflow activo por elevador. Los módulos actuales de proyectos, elevadores, pisos, pruebas, parámetros, mediciones, KPIs, comparación y documentación se conservan como soporte del workflow.

Modelo conceptual recomendado para próximos slices:

```txt
Project
  -> Elevator
      -> CommissioningWorkflow
          -> CommissioningStep
              -> TestRun opcional
              -> Evidence futura
          -> TestRuns existentes
          -> Parameters existentes
          -> LevelingMeasurements existentes
```

## 3. Roadmap nuevo desde este punto

### Slice A — Workflow guiado por elevador
- [x] Implementar `CommissioningWorkflow`.
- [x] Implementar `CommissioningStep`.
- [x] Crear workflow activo para un elevador.
- [x] Crear automáticamente los 10 pasos base.
- [x] Ver pantalla de workflow desde detalle del elevador.
- [x] Marcar pasos como `pending`, `in_progress`, `completed`, `skipped`, `not_applicable` o `blocked`.
- [x] Registrar técnico y notas por paso.
- [x] Mostrar progreso general.
- [x] Bloquear visualmente pasos dependientes si carga/pesacargas no están completados.

### Slice B — Análisis por zonas y recomendación de parámetros
- [x] Agrupar mediciones por zona y dirección.
- [x] Calcular promedio de aterrizaje.
- [x] Mapear zona/dirección a parámetros MIN/MAX.
- [x] Calcular delta sugerido.
- [x] Mostrar nuevo HEX y decimal sugerido.
- [x] Mostrar explicación técnica editable/verificable por el técnico.

### Slice C — Tabla especializada de parámetros por zona
- [x] Mostrar zona baja/media/alta.
- [x] Mostrar up/down bias.
- [x] Mostrar MIN/MAX con HEX y decimal.
- [x] Calcular ventana `MAX - MIN`.
- [x] Warning no bloqueante si `MAX <= MIN`.
- [x] Warning no bloqueante si la ventana no está entre 4 y 6 unidades decimales.
- [x] Mostrar sugeridos desde el análisis por zonas cuando existan.
- [x] Enlazar el dashboard operacional a la matriz técnica de la última prueba.

### Slice D — Cálculo de movimiento de banderas
- [x] Calcular tabla por piso con bajada, subida y movimiento recomendado.
- [x] Mostrar dentro/fuera de tolerancia.
- [x] Recomendar movimiento `0` si subida y bajada están dentro de ±5 mm.
- [x] Usar signo positivo para mover bandera hacia arriba y negativo para moverla hacia abajo.
- [x] Manejar datos parciales y faltantes explícitamente.
- [x] Enlazar el dashboard operacional a recomendaciones de banderas de la última prueba.

### Slice E — FHM y validación final
- [x] Marcar FHM como completado.
- [x] Registrar medición final.
- [x] Mostrar porcentaje de pisos dentro de tolerancia.
- [x] Separar mediciones por `measurement_stage`.
- [x] Mostrar warning no bloqueante si FHM no está completado.
- [x] Enlazar dashboard operacional a validación final.

### Slice F — Evidencias mínimas por paso
- [ ] Cargar fotos/videos por paso crítico.
- [ ] Asociar evidencia al paso de workflow cuando aplique.
- [ ] Mantener GCS como storage de archivos.

### Slice G — Reporte final por elevador
- [ ] Reporte final con prueba de carga.
- [ ] Incluir parámetros finales.
- [ ] Incluir mediciones finales.
- [ ] Incluir movimiento de banderas.
- [ ] Incluir evidencias.

## 4. Próximos slices recomendados

Próximo slice recomendado: **Slice G — Report-ready commissioning overview by elevator**.

Objetivo del slice:
- Ensamblar pasos completados, parámetros finales, análisis por zonas, banderas, FHM y validación final en una vista por elevador.
- Preparar la estructura visual y de datos para un reporte final antes de PDF.
- Mantener evidencias como placeholder hasta que el campo lo necesite.
- Reducir navegación para cierre técnico de cada elevador.

Pasos base iniciales:

1. `LOAD_CELL_MECHANICAL_CALIBRATION`
2. `LOAD_MEMORY_ZERO_FULL`
3. `OVERLOAD_110_TEST`
4. `AUTO_LEVELING_A65E_A66E`
5. `AUTO_GAIN_COMPENSATION_A67E`
6. `ZONE_FINE_LEVELING`
7. `FLOOR_BY_FLOOR_MEASUREMENT`
8. `FLAG_ADJUSTMENT`
9. `FHM_RUN`
10. `FINAL_LEVELING_VALIDATION`

## 5. Slices anteriores marcados como completados

### Fase 0 — Setup del repositorio
- [x] Crear monorepo con `apps/api` y `apps/web`.
- [x] Crear `README.md` raíz con comandos.
- [x] Crear `.gitignore`, `.env.example`, `docker-compose.yml`.
- [x] Crear GitHub Actions base para backend tests y frontend build.

### Fase 1 — Backend base
- [x] Crear FastAPI app con healthcheck.
- [x] Configurar settings/env.
- [x] Configurar SQLAlchemy async.
- [x] Configurar Alembic.
- [x] Configurar pytest.
- [x] Crear middleware de request id y logs básicos.

### Fase 2 — Modelo core
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

### Fase 3 — Pruebas y parámetros
- [x] Crear TestRun.
- [x] Crear TestRunProcessStep para procesos A61E-A67E.
- [x] Crear ParameterDefinition.
- [x] Crear TestRunParameterValue.
- [x] Crear seed de parámetros.
- [ ] Crear endpoint para crear TestRun precargando parámetros desde prueba anterior.
- [x] Crear validación HEX->decimal.
- [x] Crear warnings min/max no bloqueantes.

### Fase 4 — Nivelación
- [x] Crear LevelingMeasurement.
- [x] Crear endpoint bulk save.
- [x] Calcular tolerancia final.
- [x] Calcular `did_relevel` automáticamente desde `landing_mm` y `final_mm`.
- [x] Calcular histerisis.
- [ ] Calcular recomendación de bandera.
- [x] Crear resumen inicial por TestRun en respuesta de mediciones.

### Fase 5 — Evidencias
- [ ] Configurar GCS.
- [ ] Crear Evidence.
- [ ] Endpoint de upload.
- [ ] Endpoint de listado.
- [ ] Tests con mock de storage.

### Fase 6 — Frontend base
- [x] Crear Next.js app.
- [x] Configurar Tailwind.
- [x] Crear layout responsive.
- [x] Crear API client.
- [x] Crear dashboard inicial con datos reales.
- [x] Crear navegación principal.

### Fase 7 — Frontend operativo MVP
- [x] CRUD proyectos.
- [ ] CRUD elevadores.
- [x] Detalle elevador.
- [x] Lista de pruebas.
- [x] Crear nueva prueba.
- [x] Editor de parámetros HEX/decimal.
- [x] Autosave local.

### Fase 8 — Nivelación visual
- [ ] Crear mapa de 62 pisos.
- [x] Crear formulario de mediciones.
- [x] Separar editor de mediciones en cuatro grupos operativos: corto/subiendo, corto/bajando, largo/subiendo y largo/bajando.
- [x] Crear resumen inicial por prueba.
- [x] Mostrar KPIs avanzados y resumen por piso en detalle de prueba.
- [x] Crear comparación prueba actual vs anterior.
- [ ] Crear indicadores verde/amarillo/rojo.

### Fase 9 — Documentación técnica
- [x] Crear página de documentos.
- [x] Renderizar Markdown por slug.
- [x] Enlazar cada test type a su documento.
- [ ] Bloquear descarga directa innecesaria desde UI.

### Fase 10 — Deploy
- [x] Dockerfile backend.
- [ ] Deploy Cloud Run.
- [ ] Configurar Supabase connection string.
- [ ] Deploy Vercel frontend.
- [ ] Variables de entorno.
- [ ] Prueba end-to-end manual en celular.

### Fase 11 — Reportes
- [ ] Diseñar reporte por elevador.
- [ ] Incluir pruebas, resultados y evidencias.
- [ ] Exportar PDF desde backend.

## Historial técnico de slices completados

### Notas de Slice 1
- Se creó una base monorepo con backend FastAPI mínimo y frontend Next.js App Router.
- Backend expone `GET /health` y `GET /api/v1/health`, con CORS configurable y header `x-request-id`.
- SQLAlchemy async y Alembic quedaron configurados sin modelos de negocio todavía.
- Frontend incluye shell responsive inicial y navegación placeholder, sin CRUD.
- Siguiente slice recomendado entonces: Fase 2, crear modelos `Project`, `Elevator`, `TestType`, primera migración Alembic, seed de tipos de prueba y endpoints CRUD mínimos para proyecto/elevadores.

### Notas de Slice 2
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
- Siguiente slice recomendado entonces: Fase 3, crear `TestRun`, `ParameterDefinition`, `TestRunParameterValue`, seed de parámetros y validación HEX/decimal.

### Notas de Slice 3
- Se implementaron `TestRun`, `ParameterDefinition` y `TestRunParameterValue`.
- Se agregó migración Alembic con tablas, índices, constraints y seed inicial de parámetros técnicos.
- Los valores HEX se normalizan en backend, se convierten a decimal y rechazan entradas inválidas.
- El guardado bulk de parámetros valida pares min/max por metadata (`bound_type` + `pair_code`) y evita persistencia parcial si hay errores.
- El frontend permite crear/listar pruebas desde el detalle de elevador y editar parámetros desde `/test-runs/{testRunId}`.
- El editor de parámetros muestra preview decimal, errores HEX inline, errores backend y borrador local en `localStorage`.
- Siguiente slice recomendado entonces: Fase 4, crear mediciones de nivelación piso a piso (`LevelingMeasurement`) con bulk save y tolerancias mínimas.

### Fix intermedio — formularios, procesos técnicos A61E-A67E y warnings de parámetros
- [x] Corregir formularios de creación para no llamar `.reset()` sobre referencias nulas después de submits async.
- [x] Separar A61E, A62E, A65E, A66E y A67E como `TestRunProcessStep`, no como parámetros HEX editables.
- [x] Remover A61E-A67E del seed/listado de `ParameterDefinition`.
- [x] Agregar endpoints para listar y actualizar pasos de proceso de una prueba.
- [x] Cambiar validación min/max para retornar warnings y permitir persistencia.
- [x] Mostrar checklist de procesos y warnings de parámetros en frontend.
- Siguiente slice recomendado entonces: continuar con Fase 4 `LevelingMeasurement`.

### Notas de Slice 4
- Se implementó `LevelingMeasurement` con origen, destino, dirección, tipo de viaje, aterrizaje, final, `did_relevel` calculado y notas.
- El backend calcula `effective_final_mm` y `is_final_within_tolerance` con tolerancia inicial de ±5 mm.
- Se agregó bulk upsert transaccional para `/test-runs/{testRunId}/leveling-measurements/bulk`.
- El backend valida que los pisos usados pertenezcan al mismo elevador del `TestRun`.
- El frontend incorpora un editor de mediciones en `/test-runs/{testRunId}` con borrador local agrupado por dirección/tipo de viaje.
- Siguiente slice recomendado entonces: histerisis y KPIs avanzados de nivelación, o evidencia/GCS si se prioriza trazabilidad visual.

### Fix intermedio — UX de mediciones de nivelación piso a piso
- [x] Reorganizar el editor en cuatro grupos claros: corto/subiendo, corto/bajando, largo/subiendo y largo/bajando.
- [x] Agregar formulario compacto por grupo con origen, destino, aterrizaje, final y notas.
- [x] Mostrar tabla/lista por grupo con origen y destino explícitos, sin selector global ambiguo.
- [x] Calcular `did_relevel` en backend y frontend de vista previa; no se captura manualmente.
- [x] Validar que origen y destino sean distintos y que el destino requiera nivelación.
- [x] Mantener bulk save transaccional, borrador local y resumen de tolerancia.
- Siguiente slice recomendado entonces: Slice 5, histerisis y KPIs iniciales de nivelación.

### Notas de Slice 5
- Se agregó `GET /api/v1/test-runs/{testRunId}/leveling-summary`.
- El backend calcula cobertura de pisos requeridos, tolerancia final, renivelación aceptable, histerisis inicial y estados por piso.
- La histerisis compara subida vs bajada por tipo de viaje y corto vs largo por dirección cuando hay datos suficientes.
- El endpoint es read-only y no modifica mediciones existentes.
- El frontend muestra cards KPI, estado general y tabla por piso en `/test-runs/{testRunId}`.
- El resumen se refresca después de guardar o eliminar mediciones desde el editor.
- Siguiente slice recomendado entonces: comparación entre iteraciones de `TestRun` para ver si una prueba mejoró o empeoró.

### Notas de Slice 6
- Se agregó `GET /api/v1/test-runs/{testRunId}/comparison-candidates`.
- Se agregó `GET /api/v1/test-runs/{testRunId}/comparison?baseline_test_run_id=...`.
- El backend compara KPIs globales, estados por piso y parámetros HEX/decimal entre dos pruebas del mismo elevador.
- La comparación es calculada/read-only y no requiere migración.
- El frontend permite seleccionar una prueba baseline desde `/test-runs/{testRunId}` y muestra cards, tabla por piso y parámetros modificados.
- Siguiente slice recomendado entonces: mapa visual compacto de pisos con indicadores verde/amarillo/rojo para nivelación.

### Slice intermedio UI/UX: dashboard, navegación, listados globales y documentación Markdown
- [x] Agregar `GET /api/v1/dashboard/overview` con conteos, últimas pruebas y proyectos recientes.
- [x] Agregar `GET /api/v1/elevators` global con filtros simples.
- [x] Agregar `GET /api/v1/test-runs` global con filtros simples.
- [x] Convertir `/` en dashboard conectado al backend.
- [x] Agregar edición y eliminación de proyectos desde el detalle.
- [x] Corregir navegación principal a Dashboard, Proyectos, Elevadores, Pruebas y Documentación.
- [x] Crear `/elevators`, `/test-runs`, `/docs` y `/docs/{slug}`.
- [x] Crear documentos Markdown estáticos para carga, nivelación, compensación, parámetros y medición piso a piso.
- Siguiente slice recomendado ahora: **Slice A — Workflow guiado por elevador**.

### Notas de Slice A — Workflow guiado por elevador
- Se agregaron tablas `commissioning_workflows` y `commissioning_steps` con migración Alembic `0006_commissioning`.
- Se implementó inicialización idempotente de workflow por elevador con los 10 pasos base.
- Se agregaron endpoints para obtener/inicializar workflow, actualizar metadata, actualizar pasos y consultar dashboard operacional.
- El backend asigna `completed_at` automáticamente al completar pasos y lo limpia cuando el paso deja de estar completado.
- El detalle de elevador se reorganizó como dashboard operacional con progreso, bloqueos críticos, workflow, parámetros críticos, resumen de nivelación y acciones rápidas.
- Se conservan `TestRun`, procesos A61E-A67E, parámetros, mediciones, KPIs y comparación.
- Validación ejecutada: `docker-compose run --rm --build api pytest`, `npm run typecheck`, `npm run build`.
- Siguiente slice recomendado: **Slice B — Análisis por zonas y recomendación de parámetros**.

### Notas de Slice B — Análisis por zonas y recomendación de parámetros
- Se agregó `GET /api/v1/test-runs/{test_run_id}/zone-leveling-analysis`.
- El backend calcula zonas por `ElevatorFloor.sort_order` usando solo pisos servidos y requeridos para nivelación.
- El análisis agrupa mediciones por zona baja/media/alta y dirección subida/bajada usando el piso destino.
- El promedio usa `landing_mm` y excluye mediciones sin aterrizaje.
- La regla MVP de delta quedó centralizada: `suggested_delta_decimal = round(-average_landing_mm)`.
- Se calculan sugeridos MIN/MAX en decimal y HEX aplicando el mismo delta a ambos valores.
- Se retornan warnings no bloqueantes para `MAX <= MIN`, ventanas fuera de 4..6 y parámetros faltantes.
- El detalle de `TestRun` muestra el panel compacto **Análisis por zonas**.
- El dashboard operacional de elevador enlaza al análisis por zonas de la última prueba cuando existe.
- No hubo migración en este slice; el cálculo es read-only.
- Siguiente slice recomendado: **Slice C — Tabla especializada de parámetros por zona**.

### Notas de Slice C — Tabla especializada de parámetros por zona
- Se agregó una matriz técnica read-only en el detalle de `TestRun` para los parámetros 026D-278.
- La matriz muestra zona, dirección, MIN/MAX, HEX, decimal, ventana `MAX - MIN`, estado y warnings visuales no bloqueantes.
- La UI clasifica valores como `OK`, `MAX <= MIN`, ventana baja, ventana alta, faltantes o HEX inválido.
- Los valores sugeridos vienen del endpoint de análisis por zonas; la matriz solo formatea y clasifica la ventana visible.
- El editor existente de parámetros se conserva como punto de captura/guardado y mantiene el borrador local.
- El dashboard operacional de elevador agrega una tarjeta compacta de parámetros de nivelación fina con enlace a la matriz de la última prueba.
- No hubo migración ni cambios de backend en este slice.
- Siguiente slice recomendado: **Slice D — Cálculo de movimiento de banderas**.

### Notas de Slice D — Cálculo de movimiento de banderas
- Se agregó `GET /api/v1/test-runs/{test_run_id}/flag-adjustment-recommendations`.
- El cálculo usa pisos servidos y requeridos para nivelación, ordenados por `ElevatorFloor.sort_order`.
- Para cada piso se toma la última medición final de bajada y subida.
- Si ambas direcciones están dentro de ±5 mm, recomienda `0`.
- Si alguna dirección queda fuera de tolerancia, calcula `recommended_flag_movement_mm = -average(down_final_mm, up_final_mm)` y redondea a 0.5 mm.
- Los estados `partial_data` y `missing_data` permiten trabajar con mediciones incompletas sin romper la vista.
- El detalle de `TestRun` muestra el panel **Recomendación de movimiento de banderas**.
- El dashboard operacional de elevador agrega una tarjeta **Banderas** con enlace a recomendaciones de la última prueba.
- No hubo migración; las recomendaciones son read-only y derivadas de `LevelingMeasurement`.
- Siguiente slice recomendado: **Slice E — FHM y validación final**.

### Notas de Slice E — FHM y validación final
- Se agregó `measurement_stage` a `LevelingMeasurement` con default `floor_by_floor`.
- La migración `0007_measure_stage` actualiza el constraint único para permitir la misma ruta en etapas diferentes.
- El bulk de mediciones acepta `zone_tuning`, `floor_by_floor` y `final_validation`.
- Se agregó `GET /api/v1/test-runs/{test_run_id}/final-validation-summary`.
- El resumen final usa únicamente mediciones `final_validation` y expone estado FHM desde `CommissioningStep` `FHM_RUN`.
- El detalle de `TestRun` muestra el panel **Validación final de nivelación** y reutiliza el editor de mediciones para capturar validación final.
- El dashboard operacional agrega tarjeta **Validación final** con FHM, porcentaje dentro de tolerancia y enlace.
- Siguiente slice recomendado: **Slice G — Report-ready commissioning overview by elevator**.
