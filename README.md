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
# Edita POSTGRES_PASSWORD (y opcionalmente API_PORT / FRONTEND_PORT)

docker compose up --build -d
```

- **Dashboard:** http://127.0.0.1:3000  
- **API / Swagger:** http://127.0.0.1:8000/docs  
- El front llama al API vía `/api/...` (Nginx → contenedor `api`).

Variables útiles: ver `.env.example` en la raíz y `backend/.env.example` para el API.

---

## Opción B — Desarrollo local (sin Docker)

### 1. Backend

```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
$env:PYTHONPATH="src"
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Por defecto usa **SQLite** en `backend/data/tickets.db` y busca el CSV en `dataset/tickets.csv`, luego `tickets.csv` en la raíz.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abre **http://127.0.0.1:5173**. El proxy de Vite envía `/api/*` al backend en el puerto 8000.

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

## Variables de entorno (resumen)

| Área | Archivo / notas |
|------|------------------|
| Docker Compose | `.env.example` en la raíz (`POSTGRES_PASSWORD`, `API_PORT`, `FRONTEND_PORT`, …) |
| API (SQLite/Postgres, IA, CORS, límites CSV y `/ask`) | `backend/.env.example` |
| Front (proxy / URL del API en build) | `frontend/.env.example` |

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

---

## Licencia / entrega

Código generado para la prueba técnica. Entrega: **repositorio Git** con acceso según indique la empresa.
