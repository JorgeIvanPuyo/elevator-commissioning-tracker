# Elevator Load & Fine Leveling App — Project Context

## Objetivo
Construir una aplicación web para gestionar pruebas de carga, nivelación fina, ajustes de parámetros, evidencias y trazabilidad técnica de elevadores de un proyecto de 62 pisos.

## Alcance inicial
- Proyecto con 16 elevadores.
- Primera fase operativa: elevadores #9, #10, #11, #12 y #13.
- Luego extender a los 11 elevadores restantes.
- Backend: FastAPI + PostgreSQL/Supabase + SQLAlchemy + Alembic + pytest.
- Frontend: Next.js + TypeScript + Tailwind + Vercel.
- Storage: Google Cloud Storage para fotos/videos/evidencias.
- Deploy backend: Google Cloud Run.
- Monorepo: `apps/api` y `apps/web`.

## Problema operativo
Actualmente la información se dispersa entre Excel, notas de celular, fotos y mediciones manuales. La aplicación debe permitir:
- Registrar cada ejecución de prueba.
- Comparar pruebas anteriores vs prueba actual.
- Ver si los ajustes mejoraron o empeoraron.
- Evitar repetir pruebas o perder trazabilidad.
- Generar métricas técnicas por elevador, piso, prueba y parámetro.
- Preparar una base sólida para informes por elevador.

## Principio de producto
Primero trazabilidad útil en campo. Luego automatización, informes avanzados y analítica fina.

## Entidades críticas
- Proyecto
- Elevador
- Piso
- Prueba / ejecución de prueba
- Tipo de prueba
- Parámetros de control
- Medición de nivelación por piso
- Evidencias
- Documentación técnica
- Métricas calculadas
