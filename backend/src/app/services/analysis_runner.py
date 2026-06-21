from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.models.ticket import TicketAnalysis
from app.repositories.ticket_repository import TicketRepository
from app.services.ticket_llm import TicketAnalyzer, TicketAnalysisPayload


def _to_row(ticket_id: int, payload: TicketAnalysisPayload, model_label: str) -> TicketAnalysis:
    return TicketAnalysis(
        ticket_id=ticket_id,
        category=payload.category,
        priority=payload.priority,
        summary=payload.summary,
        sentiment=payload.sentiment,
        urgency=payload.urgency,
        suggested_team=payload.suggested_team,
        model_name=model_label,
        analyzed_at=datetime.now(timezone.utc),
    )


async def process_missing_analyses(
    session: AsyncSession,
    analyzer: TicketAnalyzer,
    *,
    max_tickets: int,
    batch_size: int = 40,
) -> int:
    """Analiza tickets sin fila en `ticket_analyses` hasta `max_tickets`."""
    repo = TicketRepository(session)
    processed = 0
    while processed < max_tickets:
        take = min(batch_size, max_tickets - processed)
        tickets = await repo.fetch_tickets_missing_analysis(limit=take)
        if not tickets:
            break
        for ticket in tickets:
            payload = await analyzer.analyze_ticket(ticket)
            session.add(_to_row(ticket.id, payload, analyzer.model_label))
        await session.commit()
        processed += len(tickets)
        if len(tickets) < take:
            break
    return processed


async def run_startup_analysis(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    analyzer: TicketAnalyzer,
) -> None:
    if not settings.auto_analyze_on_startup:
        return
    cap = settings.analyze_startup_max
    async with session_factory() as session:
        await process_missing_analyses(session, analyzer, max_tickets=cap)
