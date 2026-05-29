# Business Rules

## Reglas de prueba de carga

## Workflow guiado de commissioning

### Estado general
- Cada elevador puede tener un workflow activo de commissioning.
- El workflow se inicializa explícitamente desde la pantalla de elevador.
- La inicialización es idempotente: ejecutar initialize varias veces no duplica pasos.
- Estados válidos de workflow: `not_started`, `in_progress`, `completed`, `blocked`, `cancelled`.
- Estados válidos de paso: `pending`, `in_progress`, `completed`, `skipped`, `not_applicable`, `blocked`.

### Pasos bloqueantes
- Los tres primeros pasos son requeridos y bloqueantes:
  - Calibración mecánica de pesacargas.
  - Escritura 0% / 100% en memoria.
  - Prueba 110% de carga.
- Si los pasos bloqueantes no están completados, la UI debe mostrar los pasos dependientes de nivelación como bloqueados visualmente.
- El bloqueo visual no elimina datos existentes ni impide consultar pruebas, parámetros o mediciones ya registrados.

### Trazabilidad de pasos
- Cada paso permite registrar estado, técnico y notas.
- Si un paso se marca `completed`, el backend asigna `completed_at` automáticamente cuando estaba vacío.
- Si un paso deja de estar `completed`, `completed_at` se limpia para mantener consistencia.
- Los pasos opcionales pueden marcarse como `skipped` o `not_applicable`.

### Procesos clave
- A61E ejecuta la calibración de potenciómetros a 0% de carga.
- A62E ejecuta la calibración de potenciómetros a 100% de carga.
- A61E y A62E no son parámetros HEX editables; se registran como pasos completables dentro de la prueba.

### Voltajes esperados
- Potenciómetro 0%: 4.03 VDC.
- Potenciómetro 100%: 1.8 VDC.

### Validación 110%
La prueba se considera exitosa si al ingresar 110% de carga:
- Se activa alarma de sobrepeso.
- Se activa indicador visual FULL en pasillo de PB.
- El elevador no atiende llamadas.
- Al retirar peso de cabina, el elevador recupera operación normal.

## Reglas de nivelación fina

### Pisos por elevador
- La estructura correcta es `Project -> Elevators -> ElevatorFloors`.
- Los pisos configurables dependen del elevador, no únicamente del proyecto.
- Al crear un elevador con `floor_count = 62`, se crean automáticamente 62 pisos base con labels `1` a `62`.
- La nomenclatura puede editarse por elevador, por ejemplo `PB`, `M1`, `E1` a `E19`, `20` a `62`.
- `sort_order` es la posición física/secuencial del piso en el recorrido y debe ser único por elevador.
- `label` debe ser único por elevador solo cuando no sea nulo o vacío.
- Si un piso existe físicamente pero el elevador no se detiene allí, debe configurarse con `is_served = false` y `is_leveling_required = false`.
- Los KPIs de nivelación solo deben contar pisos con `is_served = true` e `is_leveling_required = true`.

### Micros
- DL y UL deben ajustarse a 60 mm de sobrepaso en pisos extremos.
- DL: referencia hacia abajo.
- UL: referencia hacia arriba.

### Ajustes automáticos
- A65E: ajuste automático de nivelación sin carga.
- A66E: ajuste automático de nivelación con 100% de carga.
- A67E: ajuste automático de compensación de carga.
- A65E, A66E y A67E son procesos ejecutados desde el control, no valores de parámetros.

### Parámetros calculados por A65E/A66E
- 026D, 026E, 026F, 270, 271, 272
- 273, 274, 275, 276, 277, 278

### Parámetros calculados por A67E
- 266, 240, 241, 242, 243, 244, 245

## Tolerancias

### Nivel final correcto
`final_mm` está correcto si está dentro de ±5 mm.

Para el registro inicial de mediciones:
- Si `final_mm` existe, se usa como `effective_final_mm`.
- Si `final_mm` no existe, se usa `landing_mm` como `effective_final_mm`.
- Si no hay ningún valor, la tolerancia queda sin evaluar.
- El origen y el destino de una medición deben ser pisos diferentes del mismo elevador.
- El destino debe ser un piso con `is_leveling_required = true`.

### Renivelación aceptable
La renivelación es aceptable si:
- La diferencia inicial al aterrizar es menor o igual a 10 mm, y
- El valor final queda dentro de ±5 mm.

En el registro operativo, `did_relevel` se calcula automáticamente:
- `true` si `final_mm` existe y es diferente de `landing_mm`.
- `false` si `final_mm` es nulo o igual a `landing_mm`.

Los KPIs avanzados de renivelación quedan diferidos.

### Histerisis aceptable
La histerisis es aceptable si la diferencia absoluta entre resultado final subiendo y bajando para el mismo piso y tipo de viaje es menor o igual a 5 mm.

En el resumen inicial también se compara corto vs largo dentro de la misma dirección si existen ambos datos.

### Estados de resumen de nivelación
- `not_required`: piso que no requiere nivelación o no es servido.
- `pending`: piso requerido sin mediciones con valor.
- `ok`: mediciones dentro de tolerancia y sin histerisis incorrecta.
- `warning`: medición fuera de ±5 mm, renivelación no aceptable o histerisis incorrecta.
- `critical`: algún valor final efectivo con desviación absoluta mayor a 10 mm.

### Recomendación de mover bandera
Si:
- Histerisis <= 5 mm, pero
- Nivel final está fuera de ±5 mm,
entonces los parámetros pueden estar bien y se recomienda revisar/mover físicamente la bandera.

Slice D implementa una recomendación calculada/read-only por piso usando mediciones finales piso a piso:
- Solo se consideran pisos con `is_served = true` e `is_leveling_required = true`.
- Para cada piso se usa la última medición final bajando y la última medición final subiendo del `TestRun`.
- Si no hay mediciones finales, el piso queda `missing_data`.
- Si solo existe una dirección, el piso queda `partial_data` y no se calcula recomendación completa.
- Si ambas direcciones existen y ambas están dentro de ±5 mm, el movimiento recomendado es `0`.
- Si al menos una dirección está fuera de ±5 mm:

```txt
average_final = (down_final_mm + up_final_mm) / 2
recommended_flag_movement_mm = -average_final
```

- La recomendación se redondea a precisión de 0.5 mm.
- Signo positivo significa mover bandera hacia arriba.
- Signo negativo significa mover bandera hacia abajo.
- Las recomendaciones no se persisten como registros; se calculan desde las mediciones actuales.

### FHM y validación final
Después de mover banderas:
- El técnico debe ejecutar FHM para que el controlador almacene las nuevas referencias/alturas de piso.
- FHM se registra con el paso de workflow `FHM_RUN`; no requiere una tabla específica en el MVP.
- Las mediciones posteriores a FHM se guardan con `measurement_stage = final_validation`.
- Las mediciones existentes que no envían etapa quedan como `floor_by_floor`.
- El resumen de validación final solo usa mediciones `final_validation`.
- Un piso queda `ok` si tiene bajada y subida finales dentro de ±5 mm.
- Un piso queda `out_of_tolerance` si tiene bajada y subida finales pero alguna está fuera de ±5 mm.
- Un piso queda `partial_data` si falta una dirección.
- Un piso queda `missing_data` si no tiene medición final usable.
- Si FHM no está completado, la UI debe advertirlo pero no bloquear captura.

### Comparación entre iteraciones
- Una prueba solo puede compararse contra otra prueba del mismo elevador.
- Una métrica mejora si aumenta cuando “más alto es mejor” o disminuye cuando “más bajo es mejor”, como pisos críticos.
- Un piso mejora si pasa de fuera de tolerancia a dentro de tolerancia, o si reduce el error absoluto de nivel final.
- Un piso empeora si pasa de dentro a fuera de tolerancia, o si aumenta el error absoluto de nivel final.
- Un piso queda como `newly_measured` si no tenía medición comparable en baseline y sí la tiene en la prueba actual.
- Un piso queda como `missing_current` si tenía medición en baseline y falta en la prueba actual.
- La comparación de parámetros marca cambios por diferencia de HEX/decimal y muestra warnings vigentes de la prueba actual.

## Colores técnicos de medidas
- Valor positivo: cabina alta respecto al pasillo. Mostrar en azul.
- Valor negativo: cabina baja respecto al pasillo. Mostrar en naranja.
- Dentro de tolerancia: indicador verde.
- Advertencia: amarillo.
- Fuera de rango / falla: rojo.

## Reglas de prueba
- En el MVP no hay autenticación; cada prueba debe registrar manualmente `technician_name`.
- Estados internos aceptados: `draft`, `in_progress`, `completed`, `cancelled`.
- En frontend se muestran traducidos como `Borrador`, `En proceso`, `Completada`, `Cancelada`.

## Evidencias
- Para el MVP, las evidencias se asocian a una prueba completa.
- No se asocian todavía a un piso específico.
- La metadata se guarda en PostgreSQL.
- El archivo se almacena en Google Cloud Storage.

## Informes
- La vista de resumen de commissioning por elevador es read-only y sirve como base previa a reportes PDF.
- Usa el último `TestRun` del elevador para resumir parámetros, análisis por zonas, banderas y validación final.
- El estado `ready_to_close` requiere prerrequisitos de carga completos, pasos requeridos completos, FHM completado, validación final disponible, sin pisos fuera de tolerancia y sin datos finales faltantes.
- El estado `needs_attention` aparece si hay prerrequisitos pendientes, bloqueos críticos, warnings de parámetros, FHM pendiente, pisos fuera de tolerancia o validación final incompleta.
- El resumen no reemplaza los editores operativos; enlaza a la prueba más reciente, matriz de parámetros, recomendaciones de banderas y validación final.

## Documentación técnica
- Los manuales se manejan como archivos Markdown renderizados en frontend.
- No se requiere descarga de PDF completo en el MVP.

## Validación de parámetros min/max

### Captura HEX
- Los parámetros se capturan como HEX sin requerir prefijo `0x`.
- El backend acepta `40`, `0x40` y `0X40`.
- El valor guardado se normaliza a mayúsculas y sin prefijo, por ejemplo `0x40` -> `40`.
- El backend calcula y guarda `decimal_value`, por ejemplo `40` -> `64`.
- Valores no HEX como `ZZ`, `12G` o texto libre se rechazan con error controlado.
- Si el HEX se envía vacío, el valor HEX y decimal quedan nulos.

Para los parámetros de bias por zona, dirección y límite:
- El valor MAX debe ser mayor o igual al valor MIN del mismo campo técnico.
- Si MAX < MIN, el backend permite guardar y retorna warning para trazabilidad.
- El guardado bulk de parámetros debe ser transaccional para errores bloqueantes: un HEX inválido o parámetro desconocido no debe persistir valores parciales.
- Las inconsistencias min/max son warnings no bloqueantes.

Pares conocidos:
- 026D = MIN / low zone / up bias
- 273 = MAX / low zone / up bias
- 026E = MIN / low zone / down bias
- 274 = MAX / low zone / down bias
- 026F = MIN / mid zone / up bias
- 275 = MAX / mid zone / up bias
- 270 = MIN / mid zone / down bias
- 276 = MAX / mid zone / down bias
- 271 = MIN / high zone / up bias
- 277 = MAX / high zone / up bias
- 272 = MIN / high zone / down bias
- 278 = MAX / high zone / down bias
