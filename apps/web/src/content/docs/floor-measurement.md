# Medición piso a piso

## Campos de captura

- Origen: piso desde donde inicia el viaje.
- Destino: piso donde aterriza la cabina.
- Tipo de viaje: corto o largo.
- Dirección: subiendo o bajando.
- Landing mm: medida al aterrizar.
- Final mm: medida final luego de renivelar, si aplica.

## Convención

Valor positivo significa cabina alta respecto al pasillo. Valor negativo significa cabina baja.

## Renivelación automática

La renivelación no se marca manualmente. Se calcula cuando `final_mm` existe y es diferente de `landing_mm`.
