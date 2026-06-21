from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Literal

import httpx

from app.config import Settings
from app.models.ticket import Ticket


@dataclass(frozen=True)
class TicketAnalysisPayload:
    category: str
    priority: str
    summary: str
    sentiment: str
    urgency: str
    suggested_team: str


class TicketAnalyzer(ABC):
    """Analiza un ticket y devuelve campos para persistir en `TicketAnalysis`."""

    model_label: str

    @abstractmethod
    async def analyze_ticket(self, ticket: Ticket) -> TicketAnalysisPayload:
        ...


_NEGATIVE = re.compile(
    r"\b(error|fail|broken|crash|urgent|angry|terrible|worst|refund|chargeback|lawsuit|horrible)\b",
    re.I,
)
_BILLING = re.compile(r"\b(bill|invoice|payment|charge|refund|subscription|price)\b", re.I)
_SHIP = re.compile(r"\b(ship|delivery|package|tracking|lost parcel|address)\b", re.I)
_ACCESS = re.compile(r"\b(login|password|locked|access|account|2fa|mfa)\b", re.I)


class MockTicketAnalyzer(TicketAnalyzer):
    """Heurísticas deterministas: sin coste y útil para demos y tests."""

    model_label = "mock-heuristic-v1"

    async def analyze_ticket(self, ticket: Ticket) -> TicketAnalysisPayload:
        text = " ".join(
            filter(
                None,
                [
                    ticket.ticket_subject,
                    ticket.ticket_description,
                    ticket.ticket_type,
                ],
            )
        )
        text_lower = text.lower()

        if _BILLING.search(text):
            team = "Facturación"
            category = "Facturación / pagos"
        elif _SHIP.search(text):
            team = "Logística / Envíos"
            category = "Envíos y entregas"
        elif _ACCESS.search(text):
            team = "Cuentas y acceso"
            category = "Acceso y cuentas"
        elif "bug" in text_lower or "error" in text_lower or "not working" in text_lower:
            team = "Soporte Técnico"
            category = "Incidencia técnica"
        else:
            team = "Soporte Técnico"
            category = (ticket.ticket_type or "General")[:255]

        base_pri = (ticket.priority_normalized or "medium").lower()
        if _NEGATIVE.search(text) and base_pri == "low":
            priority = "high"
        else:
            priority = base_pri if base_pri in ("low", "medium", "high", "critical") else "medium"

        if _NEGATIVE.search(text):
            sentiment = "negative"
        elif any(w in text_lower for w in ("thanks", "great", "love", "excelent", "excellent")):
            sentiment = "positive"
        else:
            sentiment = "neutral"

        if priority in ("critical", "high"):
            urgency = "high"
        elif priority == "low":
            urgency = "low"
        else:
            urgency = "medium"

        desc = ticket.ticket_description or ticket.ticket_subject or "Sin descripción"
        summary = (desc[:200] + "…") if len(desc) > 200 else desc

        return TicketAnalysisPayload(
            category=category[:255],
            priority=priority,
            summary=summary,
            sentiment=sentiment,
            urgency=urgency,
            suggested_team=team[:128],
        )


class OpenAITicketAnalyzer(TicketAnalyzer):
    """Clasificación vía Chat Completions (JSON). Requiere `OPENAI_API_KEY`."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self.model_label = f"openai:{settings.openai_model}"

    async def analyze_ticket(self, ticket: Ticket) -> TicketAnalysisPayload:
        key = self._settings.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY no está definida"
            raise RuntimeError(msg)

        system = (
            "Eres un analista de soporte. Devuelve SOLO un JSON con claves: "
            "category, priority, summary, sentiment, urgency, suggested_team. "
            "priority y urgency deben ser una de: low, medium, high, critical (urgency no use critical). "
            "sentiment una de: positive, neutral, negative. "
            "summary máximo 280 caracteres en español."
        )
        user = json.dumps(
            {
                "ticket_id": ticket.id,
                "subject": ticket.ticket_subject,
                "description": ticket.ticket_description,
                "type": ticket.ticket_type,
                "status": ticket.ticket_status,
                "priority_hint": ticket.priority_normalized,
                "product": ticket.product_purchased,
            },
            ensure_ascii=False,
        )

        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self._settings.openai_model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()

        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        priority = str(parsed.get("priority", "medium")).lower()[:32]
        if priority not in ("low", "medium", "high", "critical"):
            priority = "medium"
        sentiment = str(parsed.get("sentiment", "neutral")).lower()[:32]
        if sentiment not in ("positive", "neutral", "negative"):
            sentiment = "neutral"
        urgency = str(parsed.get("urgency", "medium")).lower()[:32]
        if urgency not in ("low", "medium", "high"):
            urgency = "medium"
        return TicketAnalysisPayload(
            category=str(parsed.get("category", "General"))[:255],
            priority=priority,
            summary=str(parsed.get("summary", ""))[:2000],
            sentiment=sentiment,
            urgency=urgency,
            suggested_team=str(parsed.get("suggested_team", "Soporte Técnico"))[:128],
        )


def build_ticket_analyzer(settings: Settings) -> TicketAnalyzer:
    provider: Literal["mock", "openai"] = settings.llm_provider
    if provider == "openai":
        return OpenAITicketAnalyzer(settings)
    return MockTicketAnalyzer()
