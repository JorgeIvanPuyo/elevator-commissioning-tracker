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

### Test Types
- `GET /test-types`
- `POST /test-types`
- `PATCH /test-types/{test_type_id}`

### Test Runs
- `GET /elevators/{elevator_id}/test-runs`
- `POST /elevators/{elevator_id}/test-runs`
- `GET /test-runs/{test_run_id}`
- `PATCH /test-runs/{test_run_id}`
- `POST /test-runs/{test_run_id}/complete`
- `DELETE /test-runs/{test_run_id}`

### Parameters
- `GET /parameter-definitions`
- `GET /test-runs/{test_run_id}/parameters`
- `PUT /test-runs/{test_run_id}/parameters`
- `POST /test-runs/{test_run_id}/parameters/validate`

### Measurements
- `GET /test-runs/{test_run_id}/leveling-measurements`
- `PUT /test-runs/{test_run_id}/leveling-measurements/bulk`
- `GET /elevators/{elevator_id}/leveling-summary`

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
- Métricas calculadas deben venir listas para el frontend.
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
