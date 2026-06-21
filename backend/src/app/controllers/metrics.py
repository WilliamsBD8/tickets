from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import MetricsRepositoryDep
from app.schemas.metrics import MetricsResponse

router = APIRouter()


@router.get(
    "",
    response_model=MetricsResponse,
    summary="Métricas agregadas",
    description=(
        "KPIs y conteos agregados para dashboard: totales, prioridades, categorías, "
        "sentimiento, top productos y clientes, tickets recientes."
    ),
)
async def get_metrics(repo: MetricsRepositoryDep) -> MetricsResponse:
    snap = await repo.get_snapshot()
    return MetricsResponse.from_snapshot(snap)
