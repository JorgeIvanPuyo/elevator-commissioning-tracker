# Technical Documents Registry

Este archivo define cómo organizar los manuales Markdown de cada prueba.

## Carpeta sugerida
`apps/web/src/content/technical-documents/`

## Archivos sugeridos
- `load-test.md`
- `fine-leveling-overview.md`
- `a65e-auto-leveling-empty.md`
- `a66e-auto-leveling-full-load.md`
- `a67e-load-compensation.md`
- `manual-parameter-adjustment.md`
- `floor-by-floor-measurement.md`

## Registro frontend sugerido
```ts
export const technicalDocuments = [
  {
    slug: "load-test",
    title: "Prueba de carga",
    category: "Carga",
    file: "load-test.md",
    relatedTestTypeCode: "LOAD_TEST",
  },
  {
    slug: "fine-leveling-overview",
    title: "Nivelación fina",
    category: "Nivelación",
    file: "fine-leveling-overview.md",
    relatedTestTypeCode: "FINE_LEVELING",
  },
];
```

## Regla
Cada pantalla de prueba debe tener un enlace visible:
"Ver procedimiento técnico".
