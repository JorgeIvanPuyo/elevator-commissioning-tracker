# Codex Working Rules

## Antes de modificar código
1. Leer `AGENTS.md`.
2. Leer `docs/00-project-context.md`.
3. Leer `docs/06-roadmap.md`.
4. Identificar el slice exacto a trabajar.
5. No implementar funcionalidades fuera del slice salvo que sean estrictamente necesarias.

## Durante la tarea
- Mantener cambios pequeños y verificables.
- Crear o actualizar tests.
- No romper contratos existentes.
- Evitar overengineering.
- Preferir implementación clara y mantenible.
- Documentar decisiones relevantes en el roadmap o en docs.

## Al terminar
1. Ejecutar tests correspondientes.
2. Reportar comandos ejecutados.
3. Marcar el item del roadmap como completado.
4. Agregar notas si hubo decisiones técnicas.
5. Sugerir el siguiente slice inmediato.

## Calidad mínima
- Backend debe levantar con Docker.
- Frontend debe compilar.
- Tests backend deben pasar.
- No dejar imports rotos.
- No dejar variables de entorno hardcoded.
- No guardar credenciales reales.

## Estilo de respuesta esperado
Codex debe responder con:
- Resumen breve de cambios.
- Archivos modificados/creados.
- Tests/comandos ejecutados.
- Riesgos o pendientes.
- Próximo paso recomendado.
