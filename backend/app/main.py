"""Сборка приложения FastAPI."""

import logging
from typing import Any, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool

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
from app.core.storage import get_storage
from app.modules.admin.router import contacts_router as admin_contacts_router
from app.modules.admin.router import router as admin_router
from app.modules.analytics.router import router as analytics_router
from app.modules.attachments.router import router as attachments_router
from app.modules.catalogs.router import router as catalogs_router
from app.modules.clients.router import router as clients_router
from app.modules.events.router import router as events_router
from app.modules.exchange.router import router as exchange_router
from app.modules.imports.router import router as imports_router
from app.modules.integrations.router import router as integrations_router
from app.modules.interactions.router import router as interactions_router
from app.modules.messages.router import router as messages_router
from app.modules.notifications.router import admin_router as notifications_admin_router
from app.modules.notifications.router import router as notifications_router
from app.modules.participants.router import router as participants_router
from app.modules.radar.router import router as radar_router
from app.modules.reports.router import router as reports_router
from app.modules.views.router import router as views_router
from app.modules.workflow.router import editor_router as workflow_editor_router
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
    storage: Literal["ok"]


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
        summary="Состояние сервиса, базы данных и хранилища файлов",
        responses=error_responses(ErrorCode.INTERNAL_ERROR),
    )
    async def health(session: SessionDep) -> HealthOut:
        await session.execute(text("SELECT 1"))
        await run_in_threadpool(get_storage().check)
        return HealthOut(status="ok", version=settings.version, database="ok", storage="ok")

    for router in (
        catalogs_router,
        clients_router,
        workflow_router,
        workflow_editor_router,
        interactions_router,
        exchange_router,
        attachments_router,
        imports_router,
        integrations_router,
        radar_router,
        reports_router,
        analytics_router,
        admin_router,
        admin_contacts_router,
        notifications_router,
        notifications_admin_router,
        messages_router,
        participants_router,
        views_router,
        events_router,
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
