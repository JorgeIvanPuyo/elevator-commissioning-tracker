# Business Rules

## Reglas de prueba de carga

### Parámetros clave
- A61E configura referencia 0% de carga.
- A62E configura referencia 100% de carga.

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

### Parámetros calculados por A65E/A66E
- 026D, 026E, 026F, 270, 271, 272
- 273, 274, 275, 276, 277, 278

### Parámetros calculados por A67E
- 266, 240, 241, 242, 243, 244, 245

## Tolerancias

### Nivel final correcto
`final_mm` está correcto si está dentro de ±5 mm.

### Renivelación aceptable
La renivelación es aceptable si:
- La diferencia inicial al aterrizar es menor o igual a 10 mm, y
- El valor final queda dentro de ±5 mm.

### Histerisis aceptable
La histerisis es aceptable si la diferencia absoluta entre resultado final subiendo y bajando para el mismo piso y tipo de viaje es menor o igual a 5 mm.

### Recomendación de mover bandera
Si:
- Histerisis <= 5 mm, pero
- Nivel final está fuera de ±5 mm,
entonces los parámetros pueden estar bien y se recomienda revisar/mover físicamente la bandera.

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
- El informe por elevador queda para una fase posterior.
- La prioridad actual es capturar datos, sostener trazabilidad, comparar iteraciones, calcular KPIs y luego generar reportes.

## Documentación técnica
- Los manuales se manejan como archivos Markdown renderizados en frontend.
- No se requiere descarga de PDF completo en el MVP.

## Validación de parámetros min/max

Para los parámetros de bias por zona, dirección y límite:
- El valor MAX debe ser mayor o igual al valor MIN del mismo campo técnico.
- Si MAX < MIN, mostrar alerta visual y bloquear guardado final, salvo que se permita guardar como borrador.

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
