# Backend/API Guidelines

## Stack
- FastAPI
- SQLAlchemy 2.x async
- Alembic
- PostgreSQL/Supabase
- Pydantic v2
- pytest + pytest-asyncio
- Google Cloud Storage client
- Ruff/Black opcional

## Estructura sugerida

```txt
apps/
  api/
    app/
      api/
        v1/
          routes/
      auth/
      config/
      constants/
      core/
      db/
        models/
        repositories/
        seeders/
      middleware/
      schemas/
      services/
      templates/
      utils/
      main.py
    migrations/
    tests/
    docs/
    Dockerfile
    docker-compose.yml
    alembic.ini
```

## Patrones
- Rutas delgadas.
- Servicios con lógica de negocio.
- Repositorios para queries complejas o reutilizables.
- Schemas Pydantic separados por Create, Update, Read.
- Modelos SQLAlchemy sin lógica pesada.
- Validaciones técnicas críticas en service layer, no solo en frontend.
- Errores HTTP claros y descriptivos.

## Convención de endpoints

Base:
`/api/v1`

### Projects
- `GET /projects`
- `POST /projects`
- `GET /projects/{project_id}`
- `PATCH /projects/{project_id}`
- `DELETE /projects/{project_id}`

### Elevators
- `GET /projects/{project_id}/elevators`
- `POST /projects/{project_id}/elevators`
- `GET /elevators/{elevator_id}`
- `PATCH /elevators/{elevator_id}`
- `DELETE /elevators/{elevator_id}`
- `GET /elevators/{elevator_id}/operational-dashboard`

### Commissioning Workflow
- `GET /elevators/{elevator_id}/commissioning-workflow`
- `POST /elevators/{elevator_id}/commissioning-workflow/initialize`
- `PATCH /commissioning-workflows/{workflow_id}`
- `PATCH /commissioning-steps/{step_id}`

El endpoint initialize es idempotente: crea el workflow y los 10 pasos base si no existen, o devuelve el workflow existente. El dashboard operacional agrega datos compactos de elevador, proyecto, workflow, última prueba, resumen de nivelación y estado de parámetros críticos.

### Test Types
- `GET /test-types`
- `POST /test-types`
- `PATCH /test-types/{test_type_id}`

### Test Runs
- `GET /elevators/{elevator_id}/test-runs`
- `POST /elevators/{elevator_id}/test-runs`
- `GET /test-runs/{test_run_id}`
- `PATCH /test-runs/{test_run_id}`
- `DELETE /test-runs/{test_run_id}`
- `GET /test-runs/{test_run_id}/comparison-candidates`
- `GET /test-runs/{test_run_id}/comparison?baseline_test_run_id=...`
- `GET /test-runs/{test_run_id}/process-steps`
- `PATCH /test-run-process-steps/{process_step_id}`

### Parameters
- `GET /parameter-definitions`
- `GET /parameter-definitions/{parameter_id}`
- `GET /test-runs/{test_run_id}/parameters`
- `PUT /test-runs/{test_run_id}/parameters`

### Measurements
- `GET /test-runs/{test_run_id}/leveling-measurements`
- `PUT /test-runs/{test_run_id}/leveling-measurements/bulk`
- `DELETE /leveling-measurements/{measurement_id}`
- `GET /test-runs/{test_run_id}/leveling-summary`

El bulk de mediciones calcula en backend `effective_final_mm`, `is_final_within_tolerance` y `did_relevel`. El payload no debe depender de una bandera manual de renivelación.
El resumen de nivelación es read-only y retorna KPIs agregados, estados y detalle por piso.
La comparación entre pruebas es read-only y solo permite comparar `TestRun` del mismo elevador.

### Evidence
- `POST /test-runs/{test_run_id}/evidence`
- `GET /test-runs/{test_run_id}/evidence`
- `DELETE /evidence/{evidence_id}`

### Documents
- `GET /technical-documents`
- `GET /technical-documents/{slug}`

### Dashboard
- `GET /projects/{project_id}/dashboard`
- `GET /elevators/{elevator_id}/dashboard`
- `GET /elevators/{elevator_id}/comparison?test_run_id=...&compare_to=...`

## Reglas de respuesta
- Fechas en ISO 8601.
- IDs UUID.
- Decimal derivado de HEX en backend.
- HEX normalizado en mayúsculas y sin prefijo `0x`.
- Validaciones min/max de parámetros ejecutadas en backend como warnings no bloqueantes.
- Errores bloqueantes: HEX inválido, parámetro desconocido, payload inválido.
- Métricas calculadas deben venir listas para el frontend.
- Mediciones de nivelación deben retornar `effective_final_mm`, `is_final_within_tolerance` y resumen agregado.
- No romper contratos una vez usados por frontend.

## Paginación
Para listas grandes:
- `limit`
- `offset`
- `sort`
- `direction`

## Filtros importantes
- `project_id`
- `elevator_id`
- `test_type`
- `status`
- `date_from`
- `date_to`

## Pruebas
Cada slice backend debe incluir:
- Tests de modelo cuando aplique.
- Tests de servicio para reglas críticas.
- Tests de API para endpoint principal.
- Test negativo para validación importante.
