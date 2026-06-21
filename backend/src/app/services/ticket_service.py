from __future__ import annotations

from app.models.ticket import Ticket, TicketAnalysis
from app.repositories.ticket_repository import TicketListFilters, TicketRepository
from app.schemas.ticket import TicketAIFields, TicketEnriched, TicketListResponse, TicketRawFields


class TicketService:
    def __init__(self, repo: TicketRepository) -> None:
        self._repo = repo

    @staticmethod
    def _to_enriched(ticket: Ticket) -> TicketEnriched:
        raw = TicketRawFields(
            ticket_id=ticket.id,
            customer_name=ticket.customer_name,
            customer_email=ticket.customer_email,
            customer_age=ticket.customer_age,
            customer_gender=ticket.customer_gender,
            product_purchased=ticket.product_purchased,
            date_of_purchase=ticket.date_of_purchase_raw,
            purchase_date=ticket.purchase_date,
            ticket_type=ticket.ticket_type,
            ticket_subject=ticket.ticket_subject,
            ticket_description=ticket.ticket_description,
            ticket_status=ticket.ticket_status,
            ticket_priority=ticket.ticket_priority_raw,
            ticket_channel=ticket.ticket_channel,
            first_response_time=ticket.first_response_time_raw,
            time_to_resolution=ticket.time_to_resolution_raw,
            customer_satisfaction_rating=ticket.customer_satisfaction_rating,
        )
        analysis: TicketAnalysis | None = ticket.analysis  # type: ignore[assignment]
        ai: TicketAIFields | None = None
        if analysis is not None:
            ai = TicketAIFields(
                category=analysis.category,
                priority=analysis.priority,
                summary=analysis.summary,
                sentiment=analysis.sentiment,
                urgency=analysis.urgency,
                suggested_team=analysis.suggested_team,
                model=analysis.model_name,
                analyzed_at=analysis.analyzed_at,
            )

        return TicketEnriched(id=ticket.id, raw=raw, ai=ai)

    async def list_tickets(self, filters: TicketListFilters) -> TicketListResponse:
        rows, total = await self._repo.list_with_filters(filters)
        items = [self._to_enriched(t) for t in rows]
        return TicketListResponse(items=items, total=total)
