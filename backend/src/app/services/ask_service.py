from __future__ import annotations

import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.repositories.metrics_repository import MetricsRepository, TicketMetricsSnapshot

logger = logging.getLogger(__name__)


class AskService:
    """Responde preguntas en lenguaje natural usando métricas agregadas + base de conocimiento."""

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

    def _mock_answer(self, question: str, snap: TicketMetricsSnapshot) -> str:
        q = question.lower()
        chunks: list[str] = []

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

        if not chunks:
            chunks.append(
                f"Resumen rápido: **{snap.total_tickets}** tickets en total, "
                f"**{snap.analyzed_tickets}** ya tienen análisis IA y **{snap.pending_analysis}** pendientes. "
                f"En los últimos 7 días hay **{snap.tickets_last_7_days}** tickets con fecha de compra reciente.",
            )
        chunks.append(
            "Esta respuesta usa el **modo mock** (reglas + métricas). "
            "Con `LLM_PROVIDER=openai` y `OPENAI_API_KEY`, se usaría el modelo para razonar sobre el mismo contexto.",
        )
        return "\n\n".join(chunks)

    async def _openai_answer(self, question: str, metrics_block: str) -> str:
        key = self._settings.openai_api_key
        if not key:
            msg = "OPENAI_API_KEY requerida para modo openai en /ask"
            raise RuntimeError(msg)

        system = (
            "Eres un analista de soporte. Responde en español, de forma breve y accionable, "
            "usando SOLO la información de métricas y la base de conocimiento proporcionadas. "
            "Si no hay datos sufícientes, dilo explícitamente. No inventes cifras."
        )
        user = f"{metrics_block}\n\n### Base de conocimiento\n{self._knowledge_text[:14000]}\n\n### Pregunta\n{question}"

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

        if self._settings.llm_provider == "openai" and self._settings.openai_api_key:
            try:
                text = await self._openai_answer(question, metrics_block)
                return text, f"openai:{self._settings.openai_model}"
            except (httpx.HTTPError, KeyError, RuntimeError) as e:
                logger.warning("Fallo OpenAI en /ask, usando mock: %s", e)
                return self._mock_answer(question, snap), "mock-ask-fallback"

        return self._mock_answer(question, snap), "mock-ask-v1"
