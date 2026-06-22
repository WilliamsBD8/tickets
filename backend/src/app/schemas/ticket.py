from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketRawFields(BaseModel):
    """Campos tal como provienen del CSV (normalizados mínimamente para transporte)."""

    model_config = ConfigDict(from_attributes=True)

    ticket_id: int
    customer_name: str | None = None
    customer_email: str | None = None
    customer_age: int | None = None
    customer_gender: str | None = None
    product_purchased: str | None = None
    date_of_purchase: str | None = None
    purchase_date: date | None = None
    ticket_type: str | None = None
    ticket_subject: str | None = None
    ticket_description: str | None = None
    ticket_status: str | None = None
    ticket_priority: str | None = None
    ticket_channel: str | None = None
    first_response_time: str | None = None
    time_to_resolution: str | None = None
    customer_satisfaction_rating: float | None = None


class TicketAIFields(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str | None = None
    priority: str | None = Field(
        default=None,
        description="Prioridad sugerida por IA: low | medium | high | critical",
    )
    summary: str | None = None
    sentiment: str | None = Field(
        default=None,
        description="Sentimiento estimado: positive | neutral | negative",
    )
    urgency: str | None = Field(default=None, description="Urgencia: low | medium | high")
    suggested_team: str | None = None
    model: str | None = None
    analyzed_at: datetime | None = None


class TicketEnriched(BaseModel):
    """Ticket con datos crudos y enriquecimiento opcional por IA."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Identificador del ticket (Ticket ID)")
    raw: TicketRawFields
    ai: TicketAIFields | None = Field(
        default=None,
        description="Campos generados por el modelo; null si aún no se analizó",
    )


class TicketListResponse(BaseModel):
    items: list[TicketEnriched]
    total: int = Field(ge=0, description="Total de registros que coinciden con los filtros")


class AnalyzeTicketsRequest(BaseModel):
    """Dispara análisis IA para tickets que aún no tienen fila en `ticket_analyses`."""

    limit: int = Field(
        default=500,
        ge=1,
        le=50_000,
        description="Máximo de tickets a procesar en esta petición",
    )


class AnalyzeTicketsResponse(BaseModel):
    processed: int = Field(ge=0, description="Tickets analizados en esta ejecución")
    provider: str = Field(description="Proveedor LLM configurado (mock u openai)")


class IngestCsvResponse(BaseModel):
    imported: int = Field(ge=0, description="Filas de ticket importadas (ids únicos)")
    replace: bool = Field(description="Si se vació la tabla antes de importar")
    analyzed: int = Field(
        default=0,
        ge=0,
        description="Tickets analizados por IA en esta petición (solo si auto_analyze=true)",
    )
