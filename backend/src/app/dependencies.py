from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings, get_settings
from app.repositories.metrics_repository import MetricsRepository
from app.repositories.ticket_repository import TicketRepository
from app.services.ask_service import AskService
from app.services.ticket_service import TicketService


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_ticket_repository(session: SessionDep) -> TicketRepository:
    return TicketRepository(session)


TicketRepositoryDep = Annotated[TicketRepository, Depends(get_ticket_repository)]


def get_ticket_service(repo: TicketRepositoryDep) -> TicketService:
    return TicketService(repo)


TicketServiceDep = Annotated[TicketService, Depends(get_ticket_service)]


def get_settings_dep() -> Settings:
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]


def get_metrics_repository(session: SessionDep) -> MetricsRepository:
    return MetricsRepository(session)


MetricsRepositoryDep = Annotated[MetricsRepository, Depends(get_metrics_repository)]


def get_ask_service(request: Request, settings: SettingsDep) -> AskService:
    kb = getattr(request.app.state, "knowledge_base_text", "") or ""
    return AskService(settings=settings, knowledge_text=kb)


AskServiceDep = Annotated[AskService, Depends(get_ask_service)]
