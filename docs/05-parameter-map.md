# Parameter Map

## Load Test Process Steps
| Code | Purpose |
|---|---|
| A61E | Configura 0% de carga |
| A62E | Configura 100% de carga |

## Auto Process Commands
| Code | Purpose |
|---|---|
| A65E | Ajuste automático de nivelación sin carga |
| A66E | Ajuste automático de nivelación con 100% de carga |
| A67E | Ajuste automático de compensación de carga |

## Auto Leveling Parameters A65E/A66E

| Bound | Zone | Bias | Parameter | Example HEX | Decimal |
|---|---|---|---|---:|---:|
| MIN | low zone | up bias | 026D | 5D | 93 |
| MIN | low zone | down bias | 026E | 5B | 91 |
| MIN | mid zone | up bias | 026F | 5B | 91 |
| MIN | mid zone | down bias | 270 | 5C | 92 |
| MIN | high zone | up bias | 271 | 83 | 131 |
| MIN | high zone | down bias | 272 | 72 | 114 |
| MAX | low zone | up bias | 273 | 60 | 96 |
| MAX | low zone | down bias | 274 | 5E | 94 |
| MAX | mid zone | up bias | 275 | 61 | 97 |
| MAX | mid zone | down bias | 276 | 5E | 94 |
| MAX | high zone | up bias | 277 | 68 | 104 |
| MAX | high zone | down bias | 278 | 5E | 94 |

## Min/Max Validation Pairs

| Min | Max | Field |
|---|---|---|
| 026D | 273 | low zone / up bias |
| 026E | 274 | low zone / down bias |
| 026F | 275 | mid zone / up bias |
| 270 | 276 | mid zone / down bias |
| 271 | 277 | high zone / up bias |
| 272 | 278 | high zone / down bias |

## Load Compensation A67E
| Code |
|---|
| 266 |
| 240 |
| 241 |
| 242 |
| 243 |
| 244 |
| 245 |

## Manual Fine Tuning Parameters
| Code | Notes |
|---|---|
| 212 | Ajuste manual de nivelación |
| 214 | Ajuste manual de nivelación |
| 022F | Ajuste de histerisis/general según comportamiento observado |
| 229 | Ajuste manual relacionado con nivelación |

## Storage Rules
- `hex_value` se guarda en mayúsculas y sin prefijo `0x`.
- `decimal_value` se calcula en backend.
- Los pares min/max se evalúan con `bound_type` y `pair_code` desde `parameter_definitions`.
- Si MAX < MIN, se guarda el valor y se retorna warning.
- A61E, A62E, A65E, A66E y A67E viven en `test_run_process_steps`, no en `parameter_definitions`.
