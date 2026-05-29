# Frontend Guidelines

## Stack
- Next.js App Router
- TypeScript
- Tailwind CSS
- React Hook Form
- Zod
- TanStack Query o fetcher centralizado
- LocalStorage para autosave temporal
- Vercel deploy

## Principio UX
La app se usa en campo, con presión, ruido, señal inestable y necesidad de rapidez. Priorizar:
- Inputs grandes y legibles en celular.
- Flujo de guardado claro.
- Autosave local.
- Estados visuales obvios.
- Comparación rápida antes/después.
- Pocos clics para registrar una medición.

## Layout
### Desktop
- Sidebar izquierda fija.
- Header superior con proyecto/elevador activo.
- Área central con cards y tablas.
- Panel derecho opcional para resumen técnico, documentación o comparación.

### Mobile
- Header compacto.
- Navegación inferior o menú hamburguesa.
- Cards apiladas.
- Tablas convertidas en listas editables.
- Botón flotante para guardar/continuar.

## Secciones principales
- Dashboard proyecto
- Elevadores
- Detalle elevador
- Pruebas
- Nueva prueba
- Nivelación piso a piso
- Parámetros
- Evidencias
- Documentación
- Reportes

## Dashboard operacional de elevador
El detalle de elevador es el centro de trabajo de campo.

Debe mostrar en la primera vista:
- Proyecto, elevador, estado y responsable/workflow si existe.
- Progreso del workflow guiado.
- Pasos requeridos pendientes.
- Bloqueos críticos de carga/pesacargas.
- Última prueba técnica.
- Resumen compacto de nivelación.
- Warnings/resumen de parámetros críticos.
- Acciones rápidas para crear TestRun, abrir última prueba, editar pisos y consultar documentación.

La vista debe ser compacta y técnica:
- Workflow como lista de pasos numerados.
- Badges para requerido/opcional, bloqueante y estado.
- Acciones simples por paso: iniciar, completar, no aplica y bloquear.
- Notas por paso guardadas directamente en backend.
- Paneles laterales para parámetros críticos, zonas, resumen de nivelación y acciones rápidas.

## Visualización 62 pisos
Crear componente `ElevatorShaftMap`.
Debe mostrar:
- 62 pisos en columna o grid compacto.
- LED por piso:
  - Verde: correcto.
  - Amarillo: advertencia.
  - Rojo: fuera de tolerancia.
  - Gris: sin medición.
  - Azul/naranja en detalle de medida positiva/negativa.
- Al tocar/click sobre un piso, abrir detalle con mediciones.

## Formularios de parámetros
Cada campo HEX debe mostrar:
- Input HEX editable.
- Conversión decimal al lado: `(96)`.
- Indicador de cambio vs prueba anterior.
- Warning si el valor viola min/max, sin bloquear guardado.

Ejemplo:
`273 = 60 (96)`

El detalle de `TestRun` debe mostrar además una matriz técnica compacta para los bias de nivelación fina `026D`-`278`:
- Zona baja/media/alta y dirección subida/bajada.
- Pares MIN/MAX lado a lado.
- Valor actual en HEX y decimal.
- Ventana `MAX - MIN`.
- Estado visual para `OK`, `MAX <= MIN`, ventana baja, ventana alta, valor faltante o HEX inválido.
- Sugeridos de MIN/MAX provenientes del análisis por zonas cuando existan.

La matriz es una vista operacional read-only. El editor de parámetros sigue siendo el punto de captura y guardado para conservar el borrador local y evitar guardados parciales inconsistentes.

## Procesos técnicos
Los códigos A61E, A62E, A65E, A66E y A67E deben mostrarse como checklist de procesos ejecutados dentro de una prueba.
No deben aparecer en el editor de parámetros HEX.

## Nivelación
El editor de mediciones debe separar el trabajo de campo en cuatro grupos:
- Corto / Subiendo.
- Corto / Bajando.
- Largo / Subiendo.
- Largo / Bajando.

Cada grupo debe tener un formulario compacto para agregar mediciones con piso origen, piso destino, aterrizaje mm, final mm y notas. La tabla/lista de cada grupo debe mostrar origen, destino, aterrizaje, final, si reniveló, tolerancia ±5 mm, notas y acciones.

`did_relevel` no es editable: se muestra como Sí/No calculado desde `landing_mm` y `final_mm`.

El editor guarda borradores por:
`elevator-commissioning:test-run:{testRunId}:leveling-groups-draft`.

El detalle de prueba debe mostrar un resumen técnico de nivelación con:
- Cards compactas de mediciones, cobertura, tolerancia final, renivelación, histerisis y estado general.
- Tabla por piso con valores finales por escenario, histerisis máxima y estado.
- Estados vacíos cuando todavía no hay mediciones o pares suficientes para histerisis.
- Actualización del resumen después de guardar mediciones.

El detalle de prueba debe mostrar una tabla de recomendaciones de movimiento de banderas:
- Cards compactas para pisos que requieren ajuste, pisos dentro de tolerancia, datos faltantes/parciales y movimiento máximo.
- Tabla desktop y cards apilables en mobile.
- Columnas: piso, bajada final, subida final, movimiento recomendado y estado.
- Estados: dentro de tolerancia, requiere ajuste, datos incompletos y sin datos.
- Valores positivos en azul y negativos en naranja, siguiendo la convención técnica de medidas.
- La tabla es read-only; el movimiento se calcula desde mediciones finales actuales.

El detalle de prueba debe mostrar un panel de FHM y validación final:
- Estado FHM desde el paso de workflow `FHM_RUN`.
- Warning no bloqueante si FHM no está completado.
- KPIs compactos de validación final: dentro de tolerancia, fuera de tolerancia, datos incompletos, sin datos y porcentaje dentro de tolerancia.
- Tabla por piso con bajada final, subida final y estado.
- Reutilizar el editor de mediciones con `measurementStage = final_validation`.
- Las mediciones piso a piso normales deben seguir usando `measurementStage = floor_by_floor`.

El detalle de prueba debe permitir comparar la prueba actual contra otra iteración del mismo elevador:
- Selector de baseline con candidatos disponibles.
- Cards comparativas para cobertura, tolerancia final, renivelación, histerisis y pisos críticos.
- Tabla por piso con estado anterior, estado actual, final anterior, final actual, delta y resultado.
- Tabla de parámetros modificados, con opción simple para mostrar todos.
- Estados claros cuando no hay candidatos, está cargando o no hay datos comparables.

## Autosave
Mientras el usuario edita una prueba:
- Guardar borrador local por `elevator_id + test_type_id + draft_id`.
- Mostrar indicador: "Guardado localmente".
- Al enviar exitosamente al backend, limpiar el draft local.
- Si existe draft al abrir, ofrecer restaurar.

En el Slice 3 el autosave inicial queda aplicado al editor de parámetros con la clave:
`elevator-commissioning:test-run:{testRunId}:parameters-draft`.

## Estados UI
- `draft`
- `saving`
- `saved`
- `error`
- `offline/local`

## Documentación
Los documentos Markdown se deben configurar en un registro frontend:
`src/config/technical-documents.ts`

Cada prueba debe poder enlazar a su documentación correspondiente.

## Diseño visual
- Minimalista, técnico y profesional.
- Fondos claros.
- Cards con bordes suaves.
- Tipografía legible.
- Evitar saturación visual.
- Usar color solo para estado técnico.
