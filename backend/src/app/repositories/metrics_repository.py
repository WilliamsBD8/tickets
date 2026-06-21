from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket import Ticket, TicketAnalysis


@dataclass(frozen=True)
class TopCount:
    label: str | None
    count: int


@dataclass(frozen=True)
class TicketMetricsSnapshot:
    total_tickets: int
    analyzed_tickets: int
    pending_analysis: int
    high_or_critical: int
    by_priority: dict[str, int]
    by_category: dict[str, int]
    by_sentiment: dict[str, int]
    top_products: list[TopCount]
    top_customers: list[TopCount]
    tickets_last_7_days: int


class MetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_snapshot(self) -> TicketMetricsSnapshot:
        total = int(
            (await self._session.execute(select(func.count(Ticket.id)))).scalar_one(),
        )
        analyzed = int(
            (
                await self._session.execute(select(func.count(TicketAnalysis.ticket_id)))
            ).scalar_one(),
        )

        eff_pri = func.lower(
            func.coalesce(TicketAnalysis.priority, Ticket.priority_normalized, "unknown"),
        )
        pr_rows = await self._session.execute(
            select(eff_pri, func.count()).group_by(eff_pri),
        )
        by_priority: dict[str, int] = {}
        high_or_critical = 0
        for pri, cnt in pr_rows.all():
            key = str(pri or "unknown")
            by_priority[key] = int(cnt)
            if key in ("high", "critical"):
                high_or_critical += int(cnt)

        cat_expr = func.coalesce(TicketAnalysis.category, Ticket.ticket_type, "Sin categoría")
        cat_rows = await self._session.execute(
            select(cat_expr, func.count()).group_by(cat_expr).order_by(func.count().desc()).limit(25),
        )
        by_category = {str(c or "Sin categoría"): int(n) for c, n in cat_rows.all()}

        sent_rows = await self._session.execute(
            select(TicketAnalysis.sentiment, func.count())
            .where(TicketAnalysis.sentiment.isnot(None))
            .group_by(TicketAnalysis.sentiment),
        )
        by_sentiment = {str(s or "unknown"): int(n) for s, n in sent_rows.all()}

        prod_rows = await self._session.execute(
            select(Ticket.product_purchased, func.count())
            .where(Ticket.product_purchased.isnot(None))
            .group_by(Ticket.product_purchased)
            .order_by(func.count().desc())
            .limit(5),
        )
        top_products = [TopCount(label=p, count=int(c)) for p, c in prod_rows.all()]

        cust_rows = await self._session.execute(
            select(Ticket.customer_name, func.count())
            .where(Ticket.customer_name.isnot(None))
            .group_by(Ticket.customer_name)
            .order_by(func.count().desc())
            .limit(5),
        )
        top_customers = [TopCount(label=n, count=int(c)) for n, c in cust_rows.all()]

        week_ago = date.today() - timedelta(days=7)
        recent = int(
            (
                await self._session.execute(
                    select(func.count()).select_from(Ticket).where(Ticket.purchase_date >= week_ago),
                )
            ).scalar_one(),
        )

        return TicketMetricsSnapshot(
            total_tickets=total,
            analyzed_tickets=analyzed,
            pending_analysis=max(0, total - analyzed),
            high_or_critical=high_or_critical,
            by_priority=by_priority,
            by_category=by_category,
            by_sentiment=by_sentiment,
            top_products=top_products,
            top_customers=top_customers,
            tickets_last_7_days=recent,
        )
