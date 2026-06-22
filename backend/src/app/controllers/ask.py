from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import AskServiceDep, SessionDep
from app.schemas.ask import AskRequest, AskResponse

router = APIRouter()


@router.post(
    "",
    response_model=AskResponse,
    summary="Preguntar en lenguaje natural",
    description=(
        "Combina métricas agregadas, una **muestra de tickets leída de la base** (búsqueda por palabras "
        "de la pregunta o los más recientes) y la base de conocimiento (markdown). "
        "Modo `mock` por defecto; con OpenAI, el modelo responde solo con ese contexto."
    ),
)
async def ask_endpoint(
    body: AskRequest,
    session: SessionDep,
    ask: AskServiceDep,
) -> AskResponse:
    answer, model = await ask.ask(session, body.question.strip())
    return AskResponse(answer=answer, model=model)
