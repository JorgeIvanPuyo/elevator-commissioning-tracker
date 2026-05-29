# Guided Commissioning Roadmap

Este documento es la guía principal para los próximos slices del producto. El roadmap ejecutivo vive en
[`docs/06-roadmap.md`](./06-roadmap.md).

## Objetivo del nuevo enfoque

La aplicación primero ayudó durante el trabajo de campo exploratorio: permitió registrar iteraciones, comparar comportamiento, detectar patrones y validar el proceso efectivo para nivelar el Elevador 11. Con esa experiencia, el producto ahora se reorienta hacia ejecución guiada para los elevadores restantes.

La aplicación debe evolucionar desde una herramienta exploratoria de comparación de pruebas hacia una herramienta de campo para commissioning:

```txt
Elevador -> workflow guiado -> pasos técnicos -> cálculo de ajuste -> validación final
```

El producto debe funcionar como:

```txt
Guía técnica + calculadora de nivelación fina + trazabilidad por elevador
```

No se elimina lo existente. `TestRun`, parámetros, mediciones, KPIs, comparación y documentación siguen siendo módulos válidos, pero pasan a operar como soporte del workflow activo por elevador.

## Modelo conceptual implementado/progresivo

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
- `id`: UUID.
- `elevator_id`: FK.
- `status`: `not_started`, `in_progress`, `completed`, `blocked`, `cancelled`.
- `technician_name`: string opcional.
- `started_at`: datetime opcional.
- `completed_at`: datetime opcional.
- `notes`: text opcional.
- `created_at`.
- `updated_at`.

Reglas:
- Para MVP, un elevador tiene un workflow activo único.
- La inicialización es perezosa e idempotente desde el endpoint de initialize.
- Si la calibración mecánica de pesacargas no está completada, los pasos dependientes de nivelación se deben mostrar bloqueados visualmente.

### CommissioningStep

Representa cada paso del proceso guiado.

Campos sugeridos:
- `id`: UUID.
- `workflow_id`: FK.
- `code`: string.
- `title`: string.
- `description`: text opcional.
- `status`: `pending`, `in_progress`, `completed`, `skipped`, `not_applicable`, `blocked`.
- `is_required`: boolean.
- `is_blocking`: boolean.
- `sort_order`: integer.
- `completed_at`: datetime opcional.
- `technician_name`: string opcional.
- `notes`: text opcional.
- `created_at`.
- `updated_at`.

Pasos iniciales:

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

### LoadTestChecklist

Puede implementarse en un slice posterior para la prueba de 110%.

Campos sugeridos:
- `id`.
- `workflow_step_id`.
- `overload_alarm_ok`.
- `calls_blocked_ok`.
- `full_indicator_pb_ok`.
- `operation_recovers_after_weight_removed`.
- `result`.
- `notes`.

## Proceso correcto de trabajo

### 1. Calibración mecánica de potenciómetros de pesacargas

Debe realizarse antes de todo.

Reglas:
- Si los pesacargas no están OK, el proceso posterior se considera bloqueado.
- Debe poder marcarse como completado.
- Debe permitir al menos una evidencia fotográfica en una fase posterior.
- La nivelación depende de este paso.

### 2. Escritura de parámetros de 0% y 100% en memoria del ascensor

Procesos relacionados:
- `A61E`: proceso para guardar lectura de 0% de carga.
- `A62E`: proceso para guardar lectura de 100% de carga.

Reglas:
- No son parámetros HEX editables.
- Son procesos completados/no completados.
- Deben poder tener evidencia en una fase posterior.

### 3. Prueba de 110% de carga

Debe registrar:
- Si funciona la alarma de sobrepeso en cabina.
- Si el elevador bloquea llamadas hasta retirar peso.
- Si se enciende el indicador visual `FULL` en botoneras de pasillo, especialmente PB.
- Si el sistema recupera operación al retirar el peso.

### 4. Calibración automática de nivelación 0% y 100%

Procesos relacionados:
- `A65E`: calibración automática de nivelación sin carga.
- `A66E`: calibración automática de nivelación con 100% de carga.

Regla:
- Es opcional/recomendado si la nivelación está muy desajustada o errática.

### 5. Calibración automática de ganancias/compensación

Proceso relacionado:
- `A67E`: compensación/ganancias.

Regla:
- Es opcional/recomendado si hay tirones, deslizamientos, arranques/frenados erráticos o comportamiento inestable.

### 6. Nivelación fina optimizada

#### 6.1 Parámetros min/max por zona y dirección

Parámetros relevantes:

| Zona | Dirección | MIN | MAX |
|---|---|---:|---:|
| Baja | Subida | `026D` | `273` |
| Baja | Bajada | `026E` | `274` |
| Media | Subida | `026F` | `275` |
| Media | Bajada | `270` | `276` |
| Alta | Subida | `271` | `277` |
| Alta | Bajada | `272` | `278` |

Reglas:
- MAX debe ser mayor que MIN.
- Si `MAX <= MIN`, mostrar warning no bloqueante.
- Una ventana de 4 a 6 unidades decimales entre MAX y MIN ha dado buenos resultados prácticos.
- Si la ventana está fuera de ese rango, mostrar warning no bloqueante.
- La app debe mostrar siempre HEX y decimal.

#### 6.2 División por zonas

Para elevadores de 62 pisos:
- Zona baja: 1 a 20.
- Zona media: 21 a 41.
- Zona alta: 42 a 62.

Estas zonas deben ser configurables posteriormente por elevador. Para el primer slice de análisis pueden calcularse por defecto.

#### 6.3 Mediciones por zona

Se deben medir 5 pisos consecutivos por zona y dirección.

Para cada medición se almacena:
- Piso origen.
- Piso destino.
- Dirección: subida/bajada.
- Tipo de viaje: corto/largo si aplica.
- Aterrizaje en mm.
- Final en mm.
- Notas.

Signos:
- Positivo: cabina queda alta respecto al pasillo.
- Negativo: cabina queda baja respecto al pasillo.

#### 6.4 Cálculo de promedio de aterrizaje

Para cada zona y dirección:

```txt
promedio_aterrizaje = suma(landing_mm de los pisos medidos) / cantidad_mediciones
```

Este valor indica cuánto ajustar los parámetros de bias para esa zona/dirección.

#### 6.5 Recomendación de ajuste

La app debe calcular:
- Parámetro MIN asociado.
- Parámetro MAX asociado.
- Valor actual en HEX y decimal.
- Delta sugerido según promedio de aterrizaje.
- Nuevo valor sugerido en decimal.
- Nuevo valor sugerido en HEX.
- Explicación breve de por qué se recomienda ese ajuste.

Regla funcional inicial:
- Si el promedio indica que la cabina aterriza antes de llegar a nivel y renivela, ajustar MIN y MAX en cantidades iguales según el promedio de aterrizaje.
- La recomendación debe ser editable/verificable por el técnico.
- La app no debe escribir automáticamente parámetros reales del ascensor.

#### 6.6 Iteración

Después de ajustar, se repite la medición por zonas:

```txt
medir -> calcular -> sugerir ajuste -> registrar nuevos parámetros -> medir de nuevo
```

El workflow debe facilitar iterar sin perder trazabilidad entre valores de parámetros, mediciones y notas.

#### 6.7 Medición piso a piso

Cuando se elimina la renivelación por zonas, se mide piso a piso en subida y bajada.

Tolerancia final:

```txt
±5 mm
```

#### 6.8 Movimiento físico de banderas

La app debe calcular posteriormente cuánto mover físicamente la bandera de cada piso.

Tabla esperada:

```txt
Piso | Bajada mm | Subida mm | Movimiento recomendado
```

Reglas:
- Si subida y bajada están dentro de ±5 mm, movimiento recomendado = 0.
- Si está fuera de tolerancia, calcular movimiento recomendado con signo.
- Signo positivo: mover bandera hacia arriba.
- Signo negativo: mover bandera hacia abajo.

#### 6.9 FHM

Después de mover banderas, se debe ejecutar FHM para guardar alturas de piso en memoria.

Debe registrarse como paso completado.

#### 6.10 Validación final

Se repite medición final para confirmar todos los pisos dentro de tolerancia.

## Roadmap de implementación

### Slice A — Workflow guiado por elevador

Implementar `CommissioningWorkflow` y `CommissioningStep`.

Debe permitir:
- [x] Crear workflow activo para un elevador.
- [x] Crear automáticamente los 10 pasos base.
- [x] Ver pantalla de workflow desde detalle del elevador.
- [x] Marcar pasos como `pending`, `in_progress`, `completed`, `skipped`, `not_applicable` o `blocked`.
- [x] Registrar técnico y notas por paso.
- [x] Mostrar progreso general.
- [x] Bloquear visualmente pasos dependientes si los pasos de carga/pesacargas no están completados.
- [x] Agregar dashboard operacional compacto por elevador.
- [x] Agregar endpoint agregado `/elevators/{elevator_id}/operational-dashboard`.

### Slice B — Análisis por zonas y recomendación de parámetros

Implementar endpoint calculado y UI para:
- [x] Agrupar mediciones por zona y dirección.
- [x] Calcular promedio de aterrizaje.
- [x] Mapear zona/dirección a parámetros MIN/MAX.
- [x] Calcular delta sugerido.
- [x] Mostrar nuevo HEX y decimal sugerido.
- [x] Mostrar explicación técnica.
- [x] Manejar mediciones faltantes sin romper la vista.
- [x] Manejar parámetros faltantes con warnings no bloqueantes.
- [x] Centralizar la convención de signo para validación posterior en campo.

Implementación actual:
- Endpoint read-only: `GET /api/v1/test-runs/{test_run_id}/zone-leveling-analysis`.
- La zona se decide por `ElevatorFloor.sort_order` del piso destino.
- Para 62 pisos, las zonas default quedan 1-20, 21-41 y 42-62.
- La regla MVP es `suggested_delta_decimal = round(-average_landing_mm)`.
- La recomendación suma el mismo delta a MIN y MAX.

### Slice C — Tabla especializada de parámetros por zona

Implementar UI técnica parecida a la hoja real:
- [x] Zona baja/media/alta.
- [x] Up/down bias.
- [x] MIN/MAX.
- [x] HEX.
- [x] Decimal.
- [x] Ventana MAX-MIN.
- [x] Warning si `MAX <= MIN`.
- [x] Warning si ventana no está entre 4 y 6 unidades.
- [x] Sugeridos desde el análisis por zonas.
- [x] Enlace desde el dashboard operacional del elevador.

Implementación actual:
- La matriz técnica vive en el detalle de `TestRun` como vista read-only.
- El editor de parámetros sigue siendo el lugar donde se capturan y guardan valores HEX.
- La matriz usa el análisis por zonas como fuente de sugeridos y clasifica localmente la ventana visible para mantener feedback inmediato.
- A61E, A62E, A65E, A66E y A67E permanecen como procesos técnicos, no como parámetros HEX.

### Slice D — Cálculo de movimiento de banderas

Implementar endpoint calculado y UI para:
- Piso.
- Bajada.
- Subida.
- Movimiento recomendado.
- Dentro/fuera de tolerancia.

### Slice E — FHM y validación final

Implementar flujo para:
- Marcar FHM como completado.
- Registrar medición final.
- Mostrar porcentaje de pisos dentro de tolerancia.

### Slice F — Evidencias mínimas por paso

Implementar carga de fotos/videos por paso crítico.

No urgente.

### Slice G — Reporte final por elevador

Implementar reporte final con:
- Prueba de carga.
- Parámetros finales.
- Mediciones finales.
- Movimiento de banderas.
- Evidencias.

No urgente.

## Decisiones que se conservan

- `TestRun` sigue existiendo para capturar pruebas e iteraciones técnicas.
- `TestRunProcessStep` sigue siendo válido para procesos A61E-A67E asociados a pruebas.
- A61E, A62E, A65E, A66E y A67E no son parámetros HEX editables.
- `ParameterDefinition` y `TestRunParameterValue` siguen siendo la fuente de captura de parámetros HEX/decimal.
- El backend sigue calculando decimal desde HEX.
- Las inconsistencias min/max son warnings no bloqueantes.
- `LevelingMeasurement` sigue capturando origen, destino, dirección, tipo de viaje, aterrizaje y final.
- Los KPIs de nivelación por `TestRun` siguen siendo útiles para resumen técnico y comparación.
- La comparación entre iteraciones sigue siendo read-only.
- Evidencias siguen planeadas con metadata en PostgreSQL y archivos en Google Cloud Storage.
