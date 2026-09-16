"""Сборка приложения FastAPI."""

import logging
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import SessionDep
from app.core.errors import (
    PROBLEM_MEDIA_TYPE,
    ErrorCode,
    TraceIdMiddleware,
    error_responses,
    install_error_handlers,
)
from app.core.security import DEV_USER_HEADER
from app.modules.attachments.router import router as attachments_router
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


def declare_problem_responses(schema: dict[str, Any]) -> dict[str, Any]:
    """Все ошибки отдаются как application/problem+json, поэтому контракт объявляет тот же тип."""
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            for status, response in operation.get("responses", {}).items():
                if status.startswith(("4", "5")):
                    response["content"] = {
                        PROBLEM_MEDIA_TYPE: {"schema": {"$ref": "#/components/schemas/Problem"}}
                    }
    return schema


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

    for router in (
        catalogs_router,
        workflow_router,
        interactions_router,
        attachments_router,
        radar_router,
    ):
        app.include_router(router)

    def openapi() -> dict[str, Any]:
        if not app.openapi_schema:
            app.openapi_schema = declare_problem_responses(
                get_openapi(
                    title=app.title,
                    version=app.version,
                    description=app.description,
                    routes=app.routes,
                )
            )
        return app.openapi_schema

    app.openapi = openapi  # type: ignore[method-assign]
    return app


app = create_app()
