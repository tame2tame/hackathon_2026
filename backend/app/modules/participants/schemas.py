"""Схемы списков обучающихся и преподавателей."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ParticipantRole = Literal["student", "teacher"]
# Рабочая почта: проверяем форму, а не существование ящика — отдельная библиотека для этого лишняя.
EMAIL_PATTERN = r"^[^@\s]+@[^@\s.]+\.[^@\s]+$"
ROLE_NAMES = {"student": "обучающийся", "teacher": "преподаватель"}


class ParticipantOut(BaseModel):
    id: uuid.UUID
    role: ParticipantRole
    full_name: str
    email: str | None = Field(
        description="Почта скрыта: и***@вуз.рф. Целиком — в карточке участника"
    )
    has_email: bool
    source: str = Field(description="manual — завели руками, import — из файла, lms — из LMS")
    created_at: datetime


class ParticipantContactOut(BaseModel):
    """Полный контакт: показывается по запросу и пишется в аудит."""

    id: uuid.UUID
    full_name: str
    email: str | None


class ParticipantCreate(BaseModel):
    role: ParticipantRole = "student"
    full_name: str = Field(min_length=3, max_length=300)
    email: str | None = Field(default=None, max_length=254, pattern=EMAIL_PATTERN)
    external_ref: str | None = Field(
        default=None, max_length=120, description="Идентификатор в LMS"
    )


class ParticipantCountsOut(BaseModel):
    students: int
    teachers: int


class ParticipantsOut(BaseModel):
    counts: ParticipantCountsOut
    items: list[ParticipantOut]


class ParticipantRowOut(BaseModel):
    row_no: int
    key: str = Field(description="ФИО строки — по нему видно, о ком речь")
    action: Literal["created", "updated", "unchanged", "error"]
    detail: str | None


class ParticipantImportOut(BaseModel):
    dry_run: bool
    created: int
    updated: int
    unchanged: int
    errors: int
    rows: list[ParticipantRowOut]
