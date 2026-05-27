# Domain Model

## Entidades principales

### Project
Representa un proyecto físico donde existen múltiples elevadores.

Campos sugeridos:
- `id`
- `name`
- `client_name`
- `location`
- `description`
- `total_elevators`
- `default_floor_count`
- `created_at`
- `updated_at`

### Elevator
Representa un elevador individual dentro de un proyecto.

Campos sugeridos:
- `id`
- `project_id`
- `code` o `number` (ej. 9, 10, 11)
- `name` (ej. Elevador #9)
- `floor_count` (ej. 62)
- `controller_model`
- `status`
- `notes`
- `created_at`
- `updated_at`

Regla:
- `code` debe ser único dentro del mismo proyecto.
- Al crear un elevador se generan automáticamente sus pisos base según `floor_count`.

### ElevatorFloor
Representa un piso físico/secuencial dentro del recorrido de un elevador.

Los pisos dependen del elevador, no solamente del proyecto, porque cada elevador puede tener diferente nomenclatura, paradas omitidas o pisos físicos que no aplican para medición de nivelación.

Campos sugeridos:
- `id`
- `elevator_id`
- `sort_order`
- `label` opcional (PB, M1, E1, 20, 62, etc.)
- `is_served`
- `is_leveling_required`
- `notes`
- `created_at`
- `updated_at`

Reglas:
- `sort_order` representa la posición física/secuencial del piso en el recorrido del elevador.
- `sort_order` debe ser único por elevador.
- `label` debe ser único por elevador solo cuando no sea nulo o vacío.
- Si un piso existe físicamente pero el elevador no se detiene allí, usar `is_served = false` y `is_leveling_required = false`.
- Para KPIs futuros de nivelación solo cuentan pisos con `is_served = true` e `is_leveling_required = true`.

### TestType
Catálogo de tipos de prueba/proceso.

Ejemplos:
- Load Test / Prueba de carga
- Fine Leveling / Nivelación fina
- Auto Leveling Empty Load A65E
- Auto Leveling 100% Load A66E
- Load Compensation A67E
- Manual Parameter Adjustment
- Floor-by-floor Measurement
- Evidence-only Check

Campos:
- `id`
- `code`
- `name`
- `description`
- `documentation_slug`
- `sort_order`
- `is_active`

### TestRun
Ejecución concreta de una prueba o iteración técnica.

Campos:
- `id`
- `project_id`
- `elevator_id`
- `test_type_id`
- `run_number`
- `title`
- `status` (`draft`, `in_progress`, `completed`, `cancelled`)
- `performed_at`
- `technician_name` manual, requerido en MVP porque no hay autenticación
- `summary`
- `observations`
- `previous_test_run_id` opcional para comparar contra ejecución previa
- `created_at`
- `updated_at`

### LoadTestData
Datos específicos de prueba de carga.

Campos:
- `id`
- `test_run_id`
- `pot_0_percent_vdc` esperado 4.03 VDC
- `pot_100_percent_vdc` esperado 1.8 VDC
- `parameter_a61e_hex`
- `parameter_a61e_decimal`
- `parameter_a62e_hex`
- `parameter_a62e_decimal`
- `zero_load_adjusted`
- `full_load_adjusted`
- `overload_110_alarm_ok`
- `full_indicator_pb_ok`
- `calls_blocked_on_overload_ok`
- `result` (`pass`, `warning`, `fail`)
- `notes`

### ParameterDefinition
Catálogo maestro de parámetros.

Campos:
- `id`
- `code` (ej. 026D, 273, 022F)
- `name`
- `description`
- `group`
- `zone` (`low`, `mid`, `high`, null)
- `direction` (`up`, `down`, null)
- `bias_type` (`up_bias`, `down_bias`, null)
- `bound_type` (`min`, `max`, null)
- `unit`
- `is_hex`
- `sort_order`

### TestRunParameterValue
Valor de un parámetro en una prueba.

Campos:
- `id`
- `test_run_id`
- `parameter_definition_id`
- `hex_value`
- `decimal_value`
- `source` (`auto_calculated`, `manual_adjusted`, `copied_from_previous`)
- `changed_from_previous`
- `notes`
- `created_at`
- `updated_at`

Regla:
- El backend debe calcular `decimal_value` a partir de `hex_value`.
- El frontend debe mostrar `HEX (decimal)`.

### LevelingMeasurement
Medición de nivelación por piso y dirección.

Campos:
- `id`
- `test_run_id`
- `elevator_id`
- `floor_label`
- `floor_number`
- `origin_floor_label`
- `destination_floor_label`
- `travel_type` (`short`, `long`)
- `direction` (`up`, `down`)
- `landing_mm` valor inicial al aterrizar. Positivo = cabina alta. Negativo = cabina baja.
- `final_mm` valor final luego de renivelación. Positivo = cabina alta. Negativo = cabina baja.
- `relevel_mm` calculado como `final_mm - landing_mm`
- `within_final_tolerance`
- `relevel_ok`
- `hysteresis_ok`
- `flag_adjustment_recommended`
- `notes`

### Evidence
Fotos/videos/documentos asociados a prueba, elevador o medición.

Campos:
- `id`
- `project_id`
- `elevator_id`
- `test_run_id`
- `file_name`
- `content_type`
- `gcs_bucket`
- `gcs_object_path`
- `public_url` o signed url temporal
- `caption`
- `created_at`

Regla MVP:
- Las evidencias se asocian a una prueba completa. No se asocian a un piso específico todavía.

### TechnicalDocument
Documentación de consulta en el frontend.

Campos:
- `id`
- `slug`
- `title`
- `category`
- `content_md_path`
- `sort_order`
- `is_active`
