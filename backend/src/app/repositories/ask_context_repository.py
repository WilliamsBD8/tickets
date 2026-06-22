from __future__ import annotations

import re

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager

from app.models.ticket import Ticket, TicketAnalysis


class AskContextRepository:
    """Recupera filas de `tickets` (+ análisis) para enriquecer el contexto de `/ask`."""

    _WORD = re.compile(r"[\wáéíóúñü]{4,}", re.IGNORECASE)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _keywords(self, question: str) -> list[str]:
        raw = self._WORD.findall(question.lower())
        return list(dict.fromkeys(raw))[:15]

    def _base_select(self):
        return (
            select(Ticket)
            .outerjoin(Ticket.analysis)
            .options(contains_eager(Ticket.analysis))
        )

    async def fetch_tickets_for_context(self, question: str, limit: int) -> list[Ticket]:
        words = self._keywords(question)
        base = self._base_select()

        if words:
            word_clauses: list = []
            for w in words:
                pat = f"%{w}%"
                word_clauses.append(
                    or_(
                        Ticket.ticket_subject.ilike(pat),
                        Ticket.ticket_description.ilike(pat),
                        Ticket.product_purchased.ilike(pat),
                        Ticket.ticket_type.ilike(pat),
                        Ticket.customer_name.ilike(pat),
                        TicketAnalysis.category.ilike(pat),
                        TicketAnalysis.summary.ilike(pat),
                        TicketAnalysis.sentiment.ilike(pat),
                    ),
                )
            stmt = base.where(or_(*word_clauses)).order_by(Ticket.id.desc()).limit(limit)
            res = await self._session.execute(stmt)
            items = list(res.scalars().unique().all())
            if items:
                return items

        stmt = base.order_by(Ticket.id.desc()).limit(limit)
        res = await self._session.execute(stmt)
        return list(res.scalars().unique().all())
