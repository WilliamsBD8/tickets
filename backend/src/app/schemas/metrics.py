from __future__ import annotations

from pydantic import BaseModel, Field

from app.repositories.metrics_repository import TicketMetricsSnapshot


class TopCountItem(BaseModel):
    label: str | None = None
    count: int = Field(ge=0)


class MetricsResponse(BaseModel):
    total_tickets: int = Field(ge=0)
    analyzed_tickets: int = Field(ge=0)
    pending_analysis: int = Field(ge=0)
    high_or_critical: int = Field(ge=0)
    by_priority: dict[str, int]
    by_category: dict[str, int]
    by_sentiment: dict[str, int]
    top_products: list[TopCountItem]
    top_customers: list[TopCountItem]
    tickets_last_7_days: int = Field(ge=0)

    @classmethod
    def from_snapshot(cls, snap: TicketMetricsSnapshot) -> MetricsResponse:
        return cls(
            total_tickets=snap.total_tickets,
            analyzed_tickets=snap.analyzed_tickets,
            pending_analysis=snap.pending_analysis,
            high_or_critical=snap.high_or_critical,
            by_priority=snap.by_priority,
            by_category=snap.by_category,
            by_sentiment=snap.by_sentiment,
            top_products=[TopCountItem(label=x.label, count=x.count) for x in snap.top_products],
            top_customers=[TopCountItem(label=x.label, count=x.count) for x in snap.top_customers],
            tickets_last_7_days=snap.tickets_last_7_days,
        )
