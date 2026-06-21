# Frontend — React (Vite + TypeScript)

Dashboard: **KPIs** (`GET /metrics`), **gráficos** (prioridad, categorías, sentimiento con Recharts), **tabla** con filtros y paginación (`GET /tickets`), **preguntas en lenguaje natural** (`POST /ask`) y acción **Analizar pendientes** (`POST /tickets/analyze`).

## Requisitos

- Node.js **20+** (recomendado LTS)
- Backend FastAPI en `http://127.0.0.1:8000` (o ajusta el proxy)

## Instalación

```powershell
cd frontend
npm install
```

## Desarrollo

En una terminal, levanta el API (desde `backend`, ver su README). En otra:

```powershell
cd frontend
npm run dev
```

Abre **http://127.0.0.1:5173**. Las peticiones a `/api/*` las reenvía Vite al backend sin problemas de CORS.

## Variables de entorno

Copia `.env.example` a `.env` si quieres cambiar el host del API en desarrollo:

- `VITE_API_PROXY_TARGET` — destino del proxy (por defecto `http://127.0.0.1:8000`).

Para el build de producción:

- `VITE_API_URL` — URL base del API (sin barra final). Si no se define, el cliente usa rutas relativas `/api/...` (p. ej. detrás del Nginx de Docker Compose).

## Build

```powershell
npm run build
npm run preview
```

## CORS

El backend permite por defecto orígenes `http://127.0.0.1:5173` y `http://localhost:5173`. Si usas otro puerto, añádelo en el backend con `CORS_ORIGINS` (separados por coma).

## Docker (junto al backend)

Desde la raíz del repositorio (donde está `docker-compose.yml`):

```powershell
docker compose up --build -d
```

- UI: **http://127.0.0.1:3000** (puerto `FRONTEND_PORT` en `.env`).
- El navegador llama a `/api/...`; Nginx reenvía al servicio `api`. No hace falta `VITE_API_URL` en la imagen.
- La API sigue publicada en `API_PORT` (8000 por defecto) si quieres usar Swagger o herramientas directas.
