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
- `elevator_id`
- `test_type_id`
- `status` (`draft`, `in_progress`, `completed`, `cancelled`)
- `technician_name` manual, requerido en MVP porque no hay autenticación
- `started_at`
- `completed_at`
- `title`
- `summary`
- `notes`
- `created_at`
- `updated_at`

Reglas:
- Un `TestRun` pertenece a un elevador y a un tipo de prueba.
- Un `TestRun` puede tener pasos técnicos ejecutados y valores de parámetros capturados.
- No se implementa flujo rígido de transiciones todavía.
- La comparación contra una ejecución previa queda para un slice posterior.

### TestRunProcessStep
Paso/proceso técnico ejecutado dentro de una prueba.

Campos:
- `id`
- `test_run_id`
- `code` (`A61E`, `A62E`, `A65E`, `A66E`, `A67E`)
- `name`
- `description`
- `is_completed`
- `completed_at`
- `notes`
- `created_at`
- `updated_at`

Reglas:
- Los códigos `A61E`, `A62E`, `A65E`, `A66E` y `A67E` son procesos técnicos, no parámetros HEX editables.
- Deben mostrarse como checklist técnico asociado al `TestRun`.
- Pueden marcarse como completados/no completados y registrar notas.

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
- `category`
- `zone` (`low`, `mid`, `high`, null)
- `direction` (`up`, `down`, null)
- `bound_type` (`min`, `max`, null)
- `pair_code` para validar pares min/max
- `is_editable`
- `sort_order`
- `created_at`
- `updated_at`

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

Reglas:
- El backend debe calcular `decimal_value` a partir de `hex_value`.
- El frontend debe mostrar `HEX (decimal)`.
- El HEX se guarda normalizado en mayúsculas y sin prefijo `0x`.
- La combinación `test_run_id + parameter_definition_id` es única.
- Si ambos valores de un par min/max existen y el máximo es menor que el mínimo, se genera warning no bloqueante.

### LevelingMeasurement
Medición de nivelación por piso y dirección.

Campos:
- `id`
- `test_run_id`
- `origin_floor_id`
- `destination_floor_id`
- `travel_type` (`short`, `long`)
- `direction` (`up`, `down`)
- `landing_mm` valor inicial al aterrizar. Positivo = cabina alta. Negativo = cabina baja.
- `final_mm` valor final luego de renivelación. Positivo = cabina alta. Negativo = cabina baja.
- `did_relevel` calculado por backend como `true` solo cuando `final_mm` existe y es distinto de `landing_mm`.
- `effective_final_mm` calculado como `final_mm` si existe, si no `landing_mm`
- `is_final_within_tolerance`
- `notes`

Reglas:
- `origin_floor_id` y `destination_floor_id` deben pertenecer al mismo elevador del `TestRun`.
- `origin_floor_id` y `destination_floor_id` deben ser diferentes.
- `destination_floor_id` debe corresponder a un piso con `is_leveling_required = true`.
- La combinación `test_run_id + origin_floor_id + destination_floor_id + direction + travel_type` es única.
- La tolerancia inicial es ±5 mm sobre `effective_final_mm`.
- El resumen técnico por `TestRun` calcula cobertura, tolerancia final, renivelación aceptable e histerisis inicial por piso.
- La recomendación de bandera queda para slices posteriores.

### LevelingSummary
Resumen calculado y read-only de nivelación para una prueba.

Campos principales:
- `test_run_id`
- `elevator_id`
- `measurement_count`
- `required_floor_count`
- `measured_required_floor_count`
- `coverage_percentage`
- `within_final_tolerance_percentage`
- `acceptable_renivelation_percentage`
- `hysteresis_ok_percentage`
- `overall_status` (`pending`, `ok`, `warning`, `critical`, `not_required`)
- `floor_summaries`

Reglas:
- Solo cuenta pisos con `is_served = true` e `is_leveling_required = true` para cobertura.
- Las mediciones sin `landing_mm` ni `final_mm` no afectan KPIs.
- Para valores repetidos de un mismo piso/escenario, se usa la medición más reciente.
- La histerisis inicial compara subida vs bajada por tipo de viaje y corto vs largo dentro de la misma dirección cuando existen datos.

### TestRunComparison
Comparación calculada y read-only entre dos iteraciones de prueba del mismo elevador.

Campos principales:
- `baseline_test_run`
- `current_test_run`
- `global_metrics`
- `floor_comparisons`
- `parameter_comparisons`
- `overall_trend` (`improved`, `worsened`, `mixed`, `unchanged`, `not_comparable`)
- `summary_text`

Reglas:
- Ambas pruebas deben pertenecer al mismo elevador.
- No se guardan resultados de comparación en base de datos.
- Las métricas globales comparan cobertura, tolerancia final, renivelación aceptable, histerisis, pisos medidos y pisos críticos.
- La comparación por piso usa el peor valor final efectivo disponible como representante inicial.
- La comparación de parámetros usa HEX y decimal guardados en cada `TestRun`.

## Entidades de workflow guiado

Estas entidades agregan la capa de ejecución guiada por elevador. La experiencia principal evoluciona desde `TestRun` como centro de pantalla hacia un workflow activo por elevador, sin eliminar pruebas, parámetros ni mediciones existentes.

Modelo conceptual:

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

### CommissioningWorkflow
Representa el proceso completo de commissioning de un elevador.

Campos:
- `id`
- `elevator_id`
- `status` (`not_started`, `in_progress`, `completed`, `blocked`, `cancelled`)
- `technician_name`
- `started_at`
- `completed_at`
- `notes`
- `created_at`
- `updated_at`

Reglas:
- Para MVP se permite un workflow activo por elevador, con constraint único sobre `elevator_id`.
- La inicialización es perezosa: el endpoint de initialize crea el workflow si no existe y devuelve el existente si ya fue creado.
- La calibración mecánica de pesacargas es condición previa para los pasos de nivelación.
- Si los pesacargas no están OK, el workflow debe mostrar bloqueados los pasos dependientes.

### CommissioningStep
Representa cada paso del proceso guiado.

Campos:
- `id`
- `workflow_id`
- `code`
- `title`
- `description`
- `status` (`pending`, `in_progress`, `completed`, `skipped`, `not_applicable`, `blocked`)
- `is_required`
- `sort_order`
- `completed_at`
- `technician_name`
- `notes`
- `created_at`
- `updated_at`

Pasos base iniciales:
- `LOAD_CELL_MECHANICAL_CALIBRATION`
- `LOAD_MEMORY_ZERO_FULL`
- `OVERLOAD_110_TEST`
- `AUTO_LEVELING_A65E_A66E`
- `AUTO_GAIN_COMPENSATION_A67E`
- `ZONE_FINE_LEVELING`
- `FLOOR_BY_FLOOR_MEASUREMENT`
- `FLAG_ADJUSTMENT`
- `FHM_RUN`
- `FINAL_LEVELING_VALIDATION`

Reglas:
- `(workflow_id, code)` es único.
- `(workflow_id, sort_order)` es único.
- Si el estado pasa a `completed`, el backend asigna `completed_at` automáticamente cuando estaba vacío.
- Si el estado cambia fuera de `completed`, el backend limpia `completed_at`.
- A61E, A62E, A65E, A66E y A67E siguen siendo procesos técnicos, no parámetros HEX editables.
- La evidencia por paso queda para una fase posterior.

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
