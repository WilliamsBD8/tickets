from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy import func, select
from starlette.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.controllers.ask import router as ask_router
from app.controllers.metrics import router as metrics_router
from app.controllers.tickets import router as tickets_router
from app.db.base import Base
from app.db.session import create_engine, create_session_factory
from app.loaders.csv_loader import load_tickets_from_csv
from app.models.ticket import Ticket
from app.services.analysis_runner import run_startup_analysis
from app.services.ticket_llm import build_ticket_analyzer


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    backend_dir = Path(__file__).resolve().parents[2]
    (backend_dir / "data").mkdir(parents=True, exist_ok=True)

    engine = create_engine(settings)
    session_factory = create_session_factory(engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if settings.auto_seed_csv and settings.dataset_csv_path.is_file():
        async with session_factory() as session:
            count_stmt = select(func.count(Ticket.id))
            existing = await session.scalar(count_stmt)
            if existing == 0:
                tickets = load_tickets_from_csv(settings.dataset_csv_path)
                session.add_all(tickets)
                await session.commit()

    kb_path = settings.knowledge_base_path
    app.state.knowledge_base_text = (
        kb_path.read_text(encoding="utf-8") if kb_path.is_file() else ""
    )

    analyzer = build_ticket_analyzer(settings)
    await run_startup_analysis(session_factory, settings, analyzer)

    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Support Ticket Analyzer",
        version="0.2.0",
        lifespan=lifespan,
        description="API del analizador de tickets de soporte.",
    )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(tickets_router, prefix="/tickets")
    app.include_router(metrics_router, prefix="/metrics")
    app.include_router(ask_router, prefix="/ask")

    return app


app = create_app()
