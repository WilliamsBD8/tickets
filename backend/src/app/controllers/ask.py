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
        "Usa métricas agregadas de la base de datos y la base de conocimiento (markdown) "
        "para responder sobre tickets. Modo `mock` por defecto; con OpenAI, razona sobre el mismo contexto."
    ),
)
async def ask_endpoint(
    body: AskRequest,
    session: SessionDep,
    ask: AskServiceDep,
) -> AskResponse:
    answer, model = await ask.ask(session, body.question.strip())
    return AskResponse(answer=answer, model=model)
