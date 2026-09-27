"""Схемы интеграций: источники, запуски синхронизации и заявки с сайта."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IntegrationSourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    kind: str = Field(description="lms или site")
    name: str
    base_url: str
    is_mock: bool
    schedule_cron: str | None = Field(
        description="Справочно: входящая синхронизация идёт в воркере раз в час для всех включённых"
    )
    last_sync_at: datetime | None
    pull_enabled: bool = Field(description="Забирать ли данные из системы по расписанию")
    push_enabled: bool = Field(description="Система принимает изменения записей CRM")
    last_push_at: datetime | None


class SyncRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_id: uuid.UUID
    direction: str = Field(description="pull — забрали данные, push — отправили изменения")
    started_at: datetime
    finished_at: datetime | None
    status: str = Field(description="running, done или failed")
    stats: dict[str, Any]
    error_code: str | None


class SiteApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: str
    university_name: str
    program_name: str
    contact_name: str | None
    comment: str | None
    received_at: datetime
    match_status: str = Field(description="matched или unmatched")
    interaction_id: uuid.UUID | None


class ApplicationMatch(BaseModel):
    interaction_id: uuid.UUID = Field(description="Взаимодействие, к которому относится заявка")


class SourceUpdate(BaseModel):
    push_enabled: bool | None = Field(
        default=None, description="Отправлять ли системе изменения записей"
    )
    pull_enabled: bool | None = Field(
        default=None, description="Забирать ли из системы данные по расписанию"
    )


class OutboxEntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interaction_id: uuid.UUID
    reason: str = Field(description="Что изменилось: created, transition, owner, attachment и др.")
    status: str = Field(description="pending, sent или failed")
    attempts: int
    next_attempt_at: datetime
    last_error: str | None
    created_at: datetime
    sent_at: datetime | None
