# AGENTS — Guía para recrear o extender el proyecto

Este documento orienta a **cualquier agente o persona** que deba reconstruir el *AI Support Ticket Analyzer* desde cero o mantenerlo. Complementa `README.md` y `prueba-tecnica.md`.

---

## 1. Qué es el producto

- **Backend:** FastAPI, SQLAlchemy 2 async, SQLite (dev) o PostgreSQL (Docker), ingestión CSV, análisis IA por ticket (mock u OpenAI), métricas, `/ask` con KB + muestra de filas de BD.
- **Frontend:** React 18 + Vite + TypeScript, dashboard (KPIs, filtros, tabla, Recharts, subida CSV, `/ask`).
- **Datos:** `dataset/tickets.csv` + `dataset/diccionario-de-datos.md`.
- **Deploy:** `docker-compose.yml` (db + api + nginx front).

---

## 2. Orden recomendado para **recrear** desde cero

Usa los perfiles en **`.cursor/agents/`** (o equivalente en tu IDE) en este orden:

| Fase | Agente | Objetivo |
|------|--------|----------|
| 0 | `solution-architect` | Leer `prueba-tecnica.md`; proponer arquitectura, carpetas, contratos API, estrategia IA y riesgos **sin** escribir código hasta que se apruebe. |
| 1 | `backend-engineer` | Implementar API: `controllers/`, `services/`, `repositories/`, `schemas/`, `models/`, lifespan, CSV, métricas, `/ask`, ingest multipart. |
| 2 | `frontend-engineer` | Implementar Vite+React: `api/`, componentes, proxy `/api`, dashboard. |
| 3 | `devops-engineer` | Dockerfiles multi-stage, `docker-compose`, Nginx `client_max_body_size`, healthchecks, variables `.env.example`. |
| 4 | `qa-integracion` | Checklist manual + sugerencias de pruebas; verificar métricas no duplicadas por cartesian join en SQL. |

Si el alcance es solo **una capa**, invoca solo el agente correspondiente y pasa contexto: rutas abajo.

---

## 3. Árbol mínimo esperado

```
Alejandro/
├── AGENTS.md                 ← este archivo
├── README.md
├── IA-DESARROLLO.md
├── prueba-tecnica.md
├── docker-compose.yml
├── .env.example
├── dataset/
│   ├── tickets.csv
│   └── diccionario-de-datos.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── knowledge_base/support_policies.md
│   └── src/app/
│       ├── main.py
│       ├── config.py
│       ├── controllers/
│       ├── services/
│       ├── repositories/
│       ├── schemas/
│       ├── models/
│       └── loaders/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── vite.config.ts
    └── src/
```

---

## 4. Comandos de verificación (post-recreación)

**Backend (local):**

```powershell
cd backend
$env:PYTHONPATH="src"
.\.venv\Scripts\uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Comprobar: `GET http://127.0.0.1:8000/health`, `GET /docs`.

**Frontend:**

```powershell
cd frontend
npm install && npm run dev
```

**Docker (raíz):**

```powershell
docker compose up --build -d
```

UI `http://127.0.0.1:3000`, API `http://127.0.0.1:8000/docs`.

---

## 5. Reglas de implementación (todos los agentes)

- **Backend:** inyección de dependencias, capas separadas, endpoints async, OpenAPI claro; no secretos en código; `DATABASE_URL` y CSV vía env.
- **Consultas métricas** que unan `Ticket` + `TicketAnalysis`: siempre `select_from(Ticket).outerjoin(TicketAnalysis, …)` y `count(Ticket.id)` — **nunca** mezclar columnas de ambas tablas en un `GROUP BY` sin `FROM` explícito (evita producto cartesiano).
- **Frontend:** `apiUrl()` usa `/api` en dev y detrás de Nginx en prod; no hardcodear `localhost:8000` en build salvo `VITE_API_URL`.
- **CSV:** columna obligatoria `Ticket ID`; UTF-8; duplicados por ID: gana la última fila (comportamiento actual del loader).

---

## 6. Mapa de agentes → archivos `.cursor/agents/`

| Archivo | Cuándo usarlo |
|---------|----------------|
| `solution-architect.md` | Diseño inicial o refactor grande. |
| `backend-engineer.md` | Todo cambio en `backend/src/**/*.py`. |
| `frontend-engineer.md` | Todo cambio en `frontend/src/**`. |
| `devops-engineer.md` | Docker, Compose, Nginx, variables de despliegue. |
| `qa-integracion.md` | Validación end-to-end y calidad de datos. |

---

## 7. Entrega alineada con la prueba técnica

- README raíz con instalación, ejecución, pruebas, endpoints, env, decisiones y limitaciones.
- `IA-DESARROLLO.md` con uso de IA en el desarrollo.
- Dataset en `dataset/` según enunciado.

Si falta algo de lo anterior, el agente **qa-integracion** debe marcarlo antes de dar por cerrada la recreación.
