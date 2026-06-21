from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Query, Request

from app.dependencies import SettingsDep, TicketServiceDep
from app.repositories.ticket_repository import TicketListFilters
from app.schemas.ticket import (
    AnalyzeTicketsRequest,
    AnalyzeTicketsResponse,
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
