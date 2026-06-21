from __future__ import annotations

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(
        min_length=3,
        max_length=4000,
        description="Pregunta en lenguaje natural sobre los tickets (y políticas de la KB).",
    )


class AskResponse(BaseModel):
    answer: str
    model: str = Field(description="Identificador del modo usado para responder")
