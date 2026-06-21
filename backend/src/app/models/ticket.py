from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    pass


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)

    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    customer_gender: Mapped[str | None] = mapped_column(String(32), nullable=True)

    product_purchased: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_purchase_raw: Mapped[str | None] = mapped_column(String(128), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    ticket_type: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    ticket_subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    ticket_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    ticket_status: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    ticket_priority_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    priority_normalized: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    ticket_channel: Mapped[str | None] = mapped_column(String(64), nullable=True)

    first_response_time_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    time_to_resolution_raw: Mapped[str | None] = mapped_column(String(64), nullable=True)
    customer_satisfaction_rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    analysis: Mapped[TicketAnalysis | None] = relationship(
        "TicketAnalysis",
        back_populates="ticket",
        uselist=False,
        cascade="all, delete-orphan",
    )


class TicketAnalysis(Base):
    __tablename__ = "ticket_analyses"

    ticket_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tickets.id", ondelete="CASCADE"),
        primary_key=True,
    )

    category: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    priority: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_team: Mapped[str | None] = mapped_column(String(128), nullable=True)

    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="analysis")
