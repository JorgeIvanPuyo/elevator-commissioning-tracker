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
- Warning si el valor viola min/max.

Ejemplo:
`273 = 60 (96)`

## Nivelación
Cada fila debe incluir:
- Piso origen.
- Piso destino.
- Dirección.
- Tipo de viaje.
- Aterrizaje mm.
- Final mm.
- Estado.
- Notas.

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
