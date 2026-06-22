# Uso de IA en el desarrollo (resumen)

## Herramientas

| Herramienta | Uso principal |
|-------------|----------------|
| **Cursor** (agente / chat) | Generación y refactor de código (FastAPI, React, Docker), búsqueda en el repo, corrección de bugs (p. ej. métricas con producto cartesiano), alineación con el enunciado. |
| **Modelo en el IDE** | Explicación de errores, borradores de README y textos, revisión de consistencia entre API y tipos del front. |

## Para qué se usó

- **Backend:** estructura por capas (controllers / services / repositories), endpoints `/metrics`, `/ask`, `/tickets/ingest`, CORS, ajustes de consultas SQL y carga de CSV.  
- **Frontend:** componentes del dashboard (tabla, filtros, KPIs, Recharts, subida de archivos).  
- **DevOps:** `Dockerfile`, `docker-compose`, Nginx para el front y proxy al API.  
- **Documentación:** borradores de README; este archivo como plantilla honesta — **revísalo y personalízalo** con tu experiencia real.

## Qué se validó manualmente

- Arranque local del **backend** y comprobación en **`/docs`** y **`/health`**.  
- Arranque del **front** con `npm run dev` y flujo en el **dashboard** (filtros, paginación, gráficos, `/ask`, subida CSV).  
- **`docker compose up`** y acceso a UI en puerto **3000** y API en **8000**.  
- Coherencia de **métricas** (totales que cuadran con la cantidad de tickets) tras corregir joins.  
- Que el CSV de **`dataset/tickets.csv`** (y columnas como `Ticket ID`) sea aceptado por ingest y por el seed.

## Agentes / reglas / prompts reutilizables

- Reglas de usuario en **Cursor** (commits, estilo de respuestas, español).  
- Regla de proyecto **`.cursor/rules/project-context.mdc`** (`alwaysApply`) que apunta a **`AGENTS.md`** y al árbol del monorepo.  
- Perfiles en **`.cursor/agents/`**: `solution-architect`, `backend-engineer`, `frontend-engineer`, `devops-engineer`, `qa-integracion` — ver **`AGENTS.md`** en la raíz para el orden de recreación.
