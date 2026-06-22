# Backend — AI Support Ticket Analyzer

## Requisitos

- Python 3.10+

## Instalación

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Ejecutar la API

Desde `backend`, con `PYTHONPATH` apuntando a `src`:

```powershell
$env:PYTHONPATH="src"
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Documentación OpenAPI: http://127.0.0.1:8000/docs

## Variables de entorno (opcional)

Copia `.env.example` a `.env` y ajusta.

- `DATABASE_URL`: por defecto SQLite en `backend/data/tickets.db`.
- `DATASET_CSV_PATH`: CSV de tickets (por defecto: `dataset/tickets.csv` si existe, si no `tickets.csv` en la raíz del repo, o `/app/data/tickets.csv` en Docker).
- `AUTO_SEED_CSV`: `true`/`false` — si la base está vacía, importa el CSV al arrancar.
- `LLM_PROVIDER`: `mock` (heurísticas, sin coste) u `openai` (requiere `OPENAI_API_KEY`).
- `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_BASE_URL`: solo si usas OpenAI.
- `KNOWLEDGE_BASE_PATH`: markdown de políticas para `/ask` (por defecto `backend/knowledge_base/support_policies.md`).
- `AUTO_ANALYZE_ON_STARTUP` / `ANALYZE_STARTUP_MAX`: análisis IA tras el seed (tope para no disparar coste con APIs de pago).
- `ASK_CONTEXT_MAX_TICKETS` / `ASK_CONTEXT_MAX_CHARS`: cuántas filas y cuántos caracteres de tickets incluye `/ask` al consultar la BD.

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/tickets` | Lista paginada + filtros; `analyzed_only=true` solo tickets con IA |
| `POST` | `/tickets/analyze` | Procesa hasta `limit` tickets pendientes de análisis |
| `POST` | `/tickets/ingest` | Sube CSV (`multipart/form-data`: `file`, `replace`, `auto_analyze`) |
| `GET` | `/metrics` | KPIs agregados (totales, prioridades, categorías, top productos/clientes, etc.) |
| `POST` | `/ask` | Pregunta en lenguaje natural (métricas + **muestra de tickets desde BD** + KB) |

Documentación interactiva: `/docs`.

**Nota:** el CSV puede traer `Ticket ID` duplicados; la carga conserva **una fila por id** (gana la última aparición).

## Docker (producción local)

Desde la **raíz del repositorio** (donde está `docker-compose.yml`):

```powershell
copy .env.example .env
# Edita POSTGRES_PASSWORD en .env

docker compose up --build -d
```

- API: http://127.0.0.1:8000/docs (puerto configurable con `API_PORT` en `.env`).
- Front (React + Nginx): http://127.0.0.1:3000 (puerto `FRONTEND_PORT`); el navegador usa `/api/...` y el proxy llega al contenedor `api`.
- Salud: `GET /health`.
- `tickets.csv` se monta en solo lectura como `/app/data/tickets.csv` dentro del contenedor.
