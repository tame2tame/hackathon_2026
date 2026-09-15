"""Сборка приложения FastAPI."""

import logging
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdMiddleware, error_responses, install_error_handlers
from app.core.security import DEV_USER_HEADER
from app.modules.catalogs.router import router as catalogs_router
from app.modules.interactions.router import router as interactions_router
from app.modules.radar.router import router as radar_router
from app.modules.workflow.router import router as workflow_router

DESCRIPTION = """
CRM контроля взаимодействия ИТ Школы Ростелекома с вузами.

Все методы `/api/v1` требуют `Authorization: Bearer <access_token>` из Keycloak.
Ошибки возвращаются в формате `application/problem+json` с полем `code`
из каталога в ARCHITECTURE.md.
"""


class HealthOut(BaseModel):
    status: Literal["ok"]
    version: str
    database: Literal["ok"]


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(
        title="Радар вузов API",
        version=settings.version,
        description=DESCRIPTION,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    install_error_handlers(app)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_methods=["GET", "POST", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type", DEV_USER_HEADER],
            expose_headers=["X-Trace-Id"],
        )
    # Добавлен последним, поэтому внешний: trace_id есть и у ответов CORS.
    app.add_middleware(TraceIdMiddleware)

    @app.get(
        "/api/health",
        tags=["system"],
        summary="Состояние сервиса и базы данных",
        responses=error_responses(ErrorCode.INTERNAL_ERROR),
    )
    async def health(session: SessionDep) -> HealthOut:
        await session.execute(text("SELECT 1"))
        return HealthOut(status="ok", version=settings.version, database="ok")

    for router in (catalogs_router, workflow_router, interactions_router, radar_router):
        app.include_router(router)
    return app


app = create_app()
