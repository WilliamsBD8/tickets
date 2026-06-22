from __future__ import annotations

import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.ticket import Ticket
from app.repositories.ask_context_repository import AskContextRepository
from app.repositories.metrics_repository import MetricsRepository, TicketMetricsSnapshot

logger = logging.getLogger(__name__)


class AskService:
    """Responde en lenguaje natural usando métricas, muestra de tickets en BD y base de conocimiento."""

    def __init__(self, settings: Settings, knowledge_text: str) -> None:
        self._settings = settings
        self._knowledge_text = knowledge_text.strip() or "(No hay texto de base de conocimiento cargado.)"

    @staticmethod
    def _format_snapshot(snap: TicketMetricsSnapshot) -> str:
        lines = [
            "## Métricas actuales (base de datos)",
            f"- Total tickets: {snap.total_tickets}",
            f"- Con análisis IA: {snap.analyzed_tickets}",
            f"- Pendientes de análisis: {snap.pending_analysis}",
            f"- Alta + crítica (prioridad efectiva): {snap.high_or_critical}",
            f"- Tickets con compra en últimos 7 días: {snap.tickets_last_7_days}",
            f"- Por prioridad: {snap.by_priority}",
            f"- Por categoría (top hasta 25 en servidor): {snap.by_category}",
            f"- Por sentimiento (solo analizados): {snap.by_sentiment}",
            "- Top productos: "
            + ", ".join(f"{x.label} ({x.count})" for x in snap.top_products if x.label)
            + (" (sin datos)" if not snap.top_products else ""),
            "- Top clientes por volumen: "
            + ", ".join(f"{x.label} ({x.count})" for x in snap.top_customers if x.label)
            + (" (sin datos)" if not snap.top_customers else ""),
        ]
        return "\n".join(lines)

    @staticmethod
    def _format_ticket_compact(t: Ticket) -> str:
        lines = [
            f"ID: {t.id}",
            f"Asunto: {(t.ticket_subject or '')[:220]}",
            f"Estado: {t.ticket_status}",
            f"Producto: {t.product_purchased}",
            f"Tipo (CSV): {t.ticket_type}",
            f"Prioridad normalizada: {t.priority_normalized}",
        ]
        desc = (t.ticket_description or "").strip()
        if desc:
            lines.append(f"Descripción (recorte): {desc[:450]}")

        ai = t.analysis  # type: ignore[assignment]
        if ai is not None:
            lines.extend(
                [
                    f"IA categoría: {ai.category}",
                    f"IA prioridad: {ai.priority}",
                    f"IA sentimiento: {ai.sentiment}",
                    f"IA urgencia: {ai.urgency}",
                    f"IA equipo: {ai.suggested_team}",
                    f"IA resumen: {(ai.summary or '')[:320]}",
                ],
            )
        return "\n".join(lines)

    def _format_tickets_block(self, tickets: list[Ticket]) -> str:
        if not tickets:
            return "(No hay tickets en la base de datos.)"
        max_chars = self._settings.ask_context_max_chars
        parts: list[str] = []
        used = 0
        for t in tickets:
            chunk = self._format_ticket_compact(t)
            sep = 10
            if used + len(chunk) + sep > max_chars:
                remaining = len(tickets) - len(parts)
                if remaining > 0:
                    parts.append(f"... ({remaining} ticket(s) omitidos por límite de contexto)")
                break
            parts.append(chunk)
            used += len(chunk) + sep
        return "\n---\n".join(parts)

    def _mock_answer(self, question: str, snap: TicketMetricsSnapshot, tickets: list[Ticket]) -> str:
        q = question.lower()
        chunks: list[str] = []

        if tickets:
            preview = "\n".join(
                f"- **#{t.id}** — {(t.ticket_subject or 'sin asunto')[:100]}"
                for t in tickets[:10]
            )
            chunks.append(
                "### Tickets leídos de la base de datos\n"
                f"Se cargaron **{len(tickets)}** filas (coincidencia con palabras de tu pregunta o las más recientes).\n"
                f"{preview}",
            )

        if any(w in q for w in ("crític", "critical", "grave", "urgente", "urgent")):
            chunks.append(
                f"Hay **{snap.high_or_critical}** tickets con prioridad alta o crítica "
                "(combinando prioridad sugerida por IA o la prioridad normalizada del CSV).",
            )
        if "producto" in q or "product" in q or "queja" in q or "complaint" in q:
            top = ", ".join(f"**{x.label}** ({x.count})" for x in snap.top_products[:5] if x.label)
            chunks.append(f"Los productos con más tickets registrados: {top or 'no hay datos suficientes.'}")
        if "cliente" in q or "customer" in q or "afect" in q:
            top = ", ".join(f"**{x.label}** ({x.count})" for x in snap.top_customers[:5] if x.label)
            chunks.append(f"Clientes con más tickets: {top or 'no hay datos suficientes.'}")
        if "categor" in q or "tema" in q:
            top_cats = sorted(snap.by_category.items(), key=lambda x: x[1], reverse=True)[:5]
            cats = ", ".join(f"**{k}** ({v})" for k, v in top_cats)
            chunks.append(f"Categorías más frecuentes: {cats or 'sin desglose.'}")
        if "sentimiento" in q or "satisfaction" in q or "satisfacc" in q:
            chunks.append(f"Distribución por sentimiento (IA): {snap.by_sentiment or 'sin análisis aún.'}")
        if "sla" in q or "equipo" in q or "escal" in q or "triage" in q:
            chunks.append(
                "Según la base de conocimiento interna: revisa equipos (Soporte Técnico, "
                "Facturación, Logística, Cuentas) y prioridades sugeridas en el markdown de políticas.",
            )

        chunks.append(
            f"**Resumen agregado (BD):** {snap.total_tickets} tickets · {snap.analyzed_tickets} con IA · "
            f"{snap.pending_analysis} pendientes de IA · {snap.tickets_last_7_days} con compra en últimos 7 días.",
        )
        chunks.append(
            "Modo **mock**: respuesta basada en métricas + muestra de tickets leídos de la base. "
            "Con `LLM_PROVIDER=openai` y `OPENAI_API_KEY`, el modelo razona sobre el mismo contexto.",
        )
        return "\n\n".join(chunks)

    async def _openai_answer(self, question: str, metrics_and_tickets: str) -> str:
        key = self._settings.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY requerida para modo openai en /ask"
            raise RuntimeError(msg)

        room = max(2500, 48_000 - len(metrics_and_tickets) - len(question))
        kb = self._knowledge_text[: min(14_000, room)]

        system = (
            "Eres un analista de soporte. Responde en español, de forma breve y accionable. "
            "Usa SOLO: (1) las métricas agregadas, (2) el bloque de tickets con ID real extraído de la base de datos, "
            "(3) la base de conocimiento. Puedes citar IDs de ticket que aparezcan en el bloque. "
            "No inventes tickets ni cifras que no estén en el contexto."
        )
        user = (
            f"{metrics_and_tickets}\n\n### Base de conocimiento\n{kb}\n\n### Pregunta\n{question}"
        )

        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self._settings.openai_model,
            "temperature": 0.3,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=90.0) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        return str(data["choices"][0]["message"]["content"]).strip()

    async def ask(self, session: AsyncSession, question: str) -> tuple[str, str]:
        snap = await MetricsRepository(session).get_snapshot()
        metrics_block = self._format_snapshot(snap)

        ctx_repo = AskContextRepository(session)
        tickets = await ctx_repo.fetch_tickets_for_context(
            question,
            self._settings.ask_context_max_tickets,
        )
        tickets_block = self._format_tickets_block(tickets)
        metrics_and_tickets = metrics_block + "\n\n### Tickets (registros en base de datos)\n" + tickets_block

        if self._settings.llm_provider == "openai" and self._settings.openai_api_key:
            try:
                text = await self._openai_answer(question, metrics_and_tickets)
                return text, f"openai:{self._settings.openai_model}"
            except (httpx.HTTPError, KeyError, RuntimeError) as e:
                logger.warning("Fallo OpenAI en /ask, usando mock: %s", e)
                return self._mock_answer(question, snap, tickets), "mock-ask-fallback"

        return self._mock_answer(question, snap, tickets), "mock-ask-v1"
