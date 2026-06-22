from __future__ import annotations

from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import delete

from app.dependencies import SettingsDep, TicketServiceDep
from app.loaders.csv_loader import load_tickets_from_bytes
from app.models.ticket import Ticket, TicketAnalysis
from app.repositories.ticket_repository import TicketListFilters
from app.schemas.ticket import (
    AnalyzeTicketsRequest,
    AnalyzeTicketsResponse,
    IngestCsvResponse,
    TicketListResponse,
)
from app.services.analysis_runner import process_missing_analyses
from app.services.ticket_llm import build_ticket_analyzer

router = APIRouter()


@router.get(
    "",
    response_model=TicketListResponse,
    summary="Listar tickets",
    description=(
        "Devuelve tickets persistidos con sus campos del dataset y, si existe, "
        "el análisis generado por IA. Filtros opcionales y paginación."
    ),
    responses={
        200: {
            "description": "Lista paginada de tickets",
        },
    },
)
async def list_tickets(
    service: TicketServiceDep,
    category: str | None = Query(
        default=None,
        description="Texto parcial (sin distinguir mayúsculas) sobre categoría efectiva: IA o tipo de ticket",
    ),
    priority: str | None = Query(
        default=None,
        description="Prioridad efectiva: low, medium, high o critical",
    ),
    status: str | None = Query(
        default=None,
        description="Estado del ticket (coincidencia parcial, sin distinguir mayúsculas)",
    ),
    sentiment: str | None = Query(
        default=None,
        description="Sentimiento del análisis IA: positive, neutral o negative (solo tickets analizados)",
    ),
    search: str | None = Query(
        default=None,
        description="Busca en asunto, descripción, producto y nombre de cliente",
    ),
    date_from: date | None = Query(
        default=None,
        description="Fecha mínima de compra (campo parseado `purchase_date`)",
    ),
    date_to: date | None = Query(
        default=None,
        description="Fecha máxima de compra (campo parseado `purchase_date`)",
    ),
    page: int = Query(default=1, ge=1, description="Página (base 1)"),
    page_size: int = Query(default=50, ge=1, le=200, description="Tamaño de página"),
    analyzed_only: bool = Query(
        default=False,
        description="Si es true, solo tickets que ya tienen análisis IA persistido",
    ),
) -> TicketListResponse:
    filters = TicketListFilters(
        category=category,
        priority=priority.lower().strip() if priority else None,
        status=status,
        sentiment=sentiment.lower().strip() if sentiment else None,
        search=search,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
        analyzed_only=analyzed_only,
    )
    return await service.list_tickets(filters)


@router.post(
    "/analyze",
    response_model=AnalyzeTicketsResponse,
    summary="Analizar tickets pendientes",
    description=(
        "Ejecuta el pipeline de IA (mock o OpenAI) para tickets sin `ticket_analyses`. "
        "Útil si desactivaste el análisis al arrancar o añadiste datos nuevos."
    ),
)
async def analyze_pending(
    request: Request,
    settings: SettingsDep,
    body: AnalyzeTicketsRequest,
) -> AnalyzeTicketsResponse:
    analyzer = build_ticket_analyzer(settings)
    factory = request.app.state.session_factory
    cap = min(body.limit, settings.analyze_startup_max)
    async with factory() as session:
        processed = await process_missing_analyses(session, analyzer, max_tickets=cap)
    return AnalyzeTicketsResponse(processed=processed, provider=settings.llm_provider)


@router.post(
    "/ingest",
    response_model=IngestCsvResponse,
    summary="Subir CSV de tickets",
    description=(
        "Importa un archivo CSV UTF-8 con las mismas columnas que el dataset oficial. "
        "**replace=true** (por defecto): borra todos los tickets y análisis IA, luego inserta el archivo. "
        "**replace=false**: actualiza o crea por `Ticket ID` y elimina solo el análisis IA de esos ids "
        "para poder volver a analizarlos."
    ),
)
async def ingest_csv(
    request: Request,
    settings: SettingsDep,
    file: UploadFile = File(..., description="Archivo .csv (UTF-8)"),
    replace: bool = Form(True, description="Vaciar la base antes de importar"),
    auto_analyze: bool = Form(
        False,
        description="Tras importar, ejecutar análisis IA hasta ANALYZE_STARTUP_MAX",
    ),
) -> IngestCsvResponse:
    fname = file.filename or ""
    if not fname.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .csv")

    raw = await file.read()
    if len(raw) > settings.csv_upload_max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande (máximo {settings.csv_upload_max_bytes} bytes).",
        )

    try:
        tickets = load_tickets_from_bytes(raw)
    except (ValueError, KeyError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not tickets:
        raise HTTPException(status_code=400, detail="El CSV no contiene filas válidas.")

    factory = request.app.state.session_factory
    async with factory() as session:
        if replace:
            await session.execute(delete(Ticket))
            session.add_all(tickets)
        else:
            ids = [t.id for t in tickets]
            if ids:
                await session.execute(delete(TicketAnalysis).where(TicketAnalysis.ticket_id.in_(ids)))
            for t in tickets:
                await session.merge(t)
        await session.commit()

    analyzed = 0
    if auto_analyze:
        analyzer = build_ticket_analyzer(settings)
        async with factory() as session:
            analyzed = await process_missing_analyses(
                session,
                analyzer,
                max_tickets=settings.analyze_startup_max,
            )

    return IngestCsvResponse(imported=len(tickets), replace=replace, analyzed=analyzed)
