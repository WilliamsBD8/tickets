from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models.ticket import Ticket, TicketAnalysis


@dataclass(frozen=True)
class TicketListFilters:
    category: str | None = None
    priority: str | None = None
    status: str | None = None
    sentiment: str | None = None
    search: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    page: int = 1
    page_size: int = 50
    analyzed_only: bool = False


class TicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _filter_clauses(self, filters: TicketListFilters):
        effective_category = func.coalesce(TicketAnalysis.category, Ticket.ticket_type)
        effective_priority = func.coalesce(TicketAnalysis.priority, Ticket.priority_normalized)

        clauses: list = []

        if filters.category:
            pattern = f"%{filters.category.strip()}%"
            clauses.append(effective_category.ilike(pattern))

        if filters.priority:
            p = filters.priority.strip().lower()
            clauses.append(func.lower(effective_priority) == p)

        if filters.status:
            pattern = f"%{filters.status.strip()}%"
            clauses.append(Ticket.ticket_status.ilike(pattern))

        if filters.sentiment:
            s = filters.sentiment.strip().lower()
            clauses.append(TicketAnalysis.sentiment.isnot(None))
            clauses.append(func.lower(TicketAnalysis.sentiment) == s)

        if filters.search:
            q = f"%{filters.search.strip()}%"
            clauses.append(
                or_(
                    Ticket.ticket_subject.ilike(q),
                    Ticket.ticket_description.ilike(q),
                    Ticket.product_purchased.ilike(q),
                    Ticket.customer_name.ilike(q),
                )
            )

        if filters.date_from is not None:
            clauses.append(Ticket.purchase_date.isnot(None))
            clauses.append(Ticket.purchase_date >= filters.date_from)

        if filters.date_to is not None:
            clauses.append(Ticket.purchase_date.isnot(None))
            clauses.append(Ticket.purchase_date <= filters.date_to)

        return clauses

    async def fetch_tickets_missing_analysis(self, limit: int) -> list[Ticket]:
        subq = select(TicketAnalysis.ticket_id)
        stmt = (
            select(Ticket)
            .where(~Ticket.id.in_(subq))
            .order_by(Ticket.id.asc())
            .limit(limit)
        )
        rows = await self._session.execute(stmt)
        return list(rows.scalars().all())

    async def list_with_filters(self, filters: TicketListFilters) -> tuple[list[Ticket], int]:
        page = max(1, filters.page)
        page_size = min(max(1, filters.page_size), 200)
        offset = (page - 1) * page_size

        clauses = self._filter_clauses(filters)

        if filters.analyzed_only:
            base = (
                select(Ticket)
                .join(Ticket.analysis)
                .options(contains_eager(Ticket.analysis))
            )
            count_stmt = select(func.count(Ticket.id)).select_from(Ticket).join(TicketAnalysis)
        else:
            base = (
                select(Ticket)
                .outerjoin(Ticket.analysis)
                .options(contains_eager(Ticket.analysis))
            )
            count_stmt = select(func.count(Ticket.id)).select_from(Ticket).outerjoin(Ticket.analysis)
        if clauses:
            base = base.where(*clauses)
            count_stmt = count_stmt.where(*clauses)

        total_result = await self._session.execute(count_stmt)
        total = int(total_result.scalar_one())

        list_stmt = base.order_by(Ticket.id.desc()).offset(offset).limit(page_size)
        rows = await self._session.execute(list_stmt)
        items = list(rows.scalars().unique().all())
        return items, total
