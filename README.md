# AI Support Ticket Analyzer

Prueba técnica: API **FastAPI** + dashboard **React (Vite)** para ingerir tickets, analizarlos con IA (mock u OpenAI), consultar métricas y hacer preguntas en lenguaje natural usando la base de datos y una base de conocimiento en markdown.

## Estructura del repositorio

| Ruta | Contenido |
|------|-----------|
| `backend/` | API FastAPI, SQLAlchemy async, Docker |
| `frontend/` | Dashboard React + TypeScript |
| `dataset/` | `tickets.csv` (dataset) y `diccionario-de-datos.md` |
| `docker-compose.yml` | Postgres + API + Nginx (front) |
| `prueba-tecnica.md` | Enunciado original |

---

## Requisitos previos

- **Docker + Docker Compose** (recomendado para levantar todo), o  
- **Python 3.10+** y **Node.js 20+** para desarrollo local sin contenedores.

---

## Opción A — Todo con Docker (recomendado)

Desde la **raíz del repo**:

```powershell
copy .env.example .env
# Edita POSTGRES_PASSWORD y, si quieres, API_PORT / FRONTEND_PORT / opciones de la API (LLM, CORS, límites — ver .env.example)

docker compose up --build -d
```

- **Dashboard:** http://127.0.0.1:3000  
- **API / Swagger:** http://127.0.0.1:8000/docs  
- El front llama al API vía `/api/...` (Nginx → contenedor `api`).

Necesitas el **`.env` de la raíz** (plantilla: `.env.example`). Compose inyecta puertos, Postgres y las mismas variables de API que `backend/.env.example` (LLM, CORS, límites, rutas en contenedor, etc.). **No** monta `backend/.env` dentro del contenedor: para cambiar la API en Docker, edita el `.env` de la raíz. **`frontend/.env`** sigue siendo solo para `npm run dev` / build local de Vite.

---

## Opción B — Desarrollo local (sin Docker)

### 1. Backend

```powershell
cd backend
copy .env.example .env
# Opcional: edita .env (LLM_PROVIDER, OPENAI_API_KEY, CORS_ORIGINS, …)

py -3 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:PYTHONPATH="src"
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Por defecto usa **SQLite** en `backend/data/tickets.db` y busca el CSV en `dataset/tickets.csv`, luego `tickets.csv` en la raíz.  
La API carga **`backend/.env`** (no el de la raíz).

### 2. Frontend

```powershell
cd frontend
copy .env.example .env
# Opcional: solo si cambias el host del API en dev (VITE_API_PROXY_TARGET)

npm install
npm run dev
```

Abre **http://127.0.0.1:5173**. El proxy de Vite envía `/api/*` al backend en el puerto 8000.  
Vite lee **`frontend/.env`** (no el de la raíz).

---

## Cómo probarlo

1. **Dashboard:** tabla, filtros, KPIs, gráficos (barras + pastel), subida de CSV, botón de análisis IA, panel `/ask`.  
2. **Swagger:** `GET /docs` en el puerto del API.  
3. **Salud:** `GET /health`  
4. **Ejemplos rápidos (con API en 8000):**

```powershell
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/tickets?page=1&page_size=5"
curl http://127.0.0.1:8000/metrics
curl -X POST http://127.0.0.1:8000/ask -H "Content-Type: application/json" -d "{\"question\":\"¿Qué producto tiene más tickets?\"}"
```

**Subir CSV:** en el dashboard (sección “Subir dataset”) o `POST /tickets/ingest` (`multipart/form-data`: `file`, `replace`, `auto_analyze`). Ver `backend/README.md`.

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/health` | Estado del servicio |
| `GET` | `/tickets` | Lista paginada + filtros (`analyzed_only`, etc.) |
| `POST` | `/tickets/analyze` | Analiza tickets pendientes con IA |
| `POST` | `/tickets/ingest` | Importa un CSV (reemplazo o fusión por ID) |
| `GET` | `/metrics` | KPIs agregados |
| `POST` | `/ask` | Pregunta en lenguaje natural (métricas + muestra de BD + KB) |

Detalle y variables: **`backend/README.md`**. Front: **`frontend/README.md`**.

---

## Variables de entorno — tres `.env` distintos

**Copiar `.env.example` → `.env` en la raíz no configura solo el backend ni el front.** Cada herramienta lee su propio archivo (o ninguno, y usa valores por defecto).

| Ubicación | Quién lo usa | Plantilla | Para qué sirve |
|-----------|----------------|-----------|----------------|
| **Raíz** (`./.env`) | **Docker Compose** al ejecutar `docker compose` desde la raíz | `.env.example` | Puertos, Postgres y **opciones de la API** (mismas claves que `backend/.env.example`: `LLM_PROVIDER`, OpenAI, `CORS_ORIGINS`, límites de CSV/`/ask`, rutas de dataset/KB dentro del contenedor, etc.). **No** lo lee FastAPI ni Vite al desarrollar fuera de Docker. |
| **`backend/.env`** | **FastAPI** (pydantic-settings) al arrancar `uvicorn` desde `backend/` | `backend/.env.example` | `DATABASE_URL`, `LLM_PROVIDER`, `OPENAI_API_KEY`, `CORS_ORIGINS`, límites de CSV/`/ask`, rutas al dataset/KB, etc. |
| **`frontend/.env`** | **Vite** al hacer `npm run dev` / `npm run build` desde `frontend/` | `frontend/.env.example` | `VITE_API_PROXY_TARGET` (dev), `VITE_API_URL` (build producción). Muchas veces no hace falta crear `.env` si usas los valores por defecto. |

**Resumen práctico**

- **Solo Docker Compose:** basta con `copy .env.example .env` en la **raíz**.  
- **Solo backend local:** `copy .env.example .env` dentro de **`backend/`**.  
- **Solo front local:** opcional `copy .env.example .env` dentro de **`frontend/`**.  
- **Todo a la vez en local:** puedes tener **tres** `.env` independientes; cambiar uno no actualiza los otros.

No subas **API keys** al repositorio; usa `.env` local o secretos del orquestador.

---

## Decisiones técnicas (breve)

- **FastAPI + SQLAlchemy 2 async:** encaje natural con CSV → modelo relacional, filtros y métricas en SQL.  
- **Mock de IA por defecto:** cumple el enunciado sin coste; **OpenAI** opcional vía `LLM_PROVIDER=openai` y `OPENAI_API_KEY`.  
- **React + Vite:** dashboard rápido de montar; **Recharts** para gráficos.  
- **Docker Compose:** Postgres para un entorno cercano a producción; front servido con **Nginx** y proxy `/api`.  
- **`/ask`:** métricas agregadas + **muestra de tickets leída de la BD** (palabras clave de la pregunta o recientes) + markdown de **base de conocimiento** — no es RAG vectorial completo, pero sí contexto real de filas.

---

## Limitaciones y mejoras con más tiempo

- **RAG / embeddings** para `/ask` sobre todo el histórico sin depender solo de `ILIKE` y un tope de filas.  
- **Normalización de categorías** en el dataset (muchos nombres distintos para el mismo concepto).  
- **Alembic** para migraciones en lugar de solo `create_all`.  
- **Tests** (pytest + pruebas de contrato del front) y **CI** en GitHub Actions.  
- **Autenticación** en `/tickets/ingest` y `/ask` en entornos expuestos a Internet.

---

## Uso de IA durante el desarrollo

Ver **[`IA-DESARROLLO.md`](./IA-DESARROLLO.md)** (herramientas, para qué se usaron y qué se validó a mano).

## Agentes y recreación del proyecto

Ver **[`AGENTS.md`](./AGENTS.md)** y los perfiles en **`.cursor/agents/`** para reconstruir o extender el sistema con roles claros (arquitectura, backend, front, DevOps, QA).

---

## Licencia / entrega

Código generado para la prueba técnica. Entrega: **repositorio Git** con acceso según indique la empresa.
