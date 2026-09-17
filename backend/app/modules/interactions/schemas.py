"""Схемы взаимодействий: элемент списка, карточка, переход."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.errors import ErrorCode
from app.modules.catalogs.schemas import (
    CounterpartyRef,
    GroupRef,
    ProductRef,
    ProgramRef,
    UniversityRef,
    UserRef,
)
from app.modules.clients.schemas import ClientRef
from app.modules.radar.rules import Severity, SignalKind
from app.modules.radar.schemas import SignalOut
from app.modules.workflow.schemas import AllowedTransitionOut, StageRef


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: str
    signed_at: date | None
    license_signed_at: date | None
    license_valid_until: date | None
    license_term_years: int | None
    transfer_status: str | None


class SignalBrief(BaseModel):
    kind: SignalKind
    severity: Severity


class InteractionListItem(BaseModel):
    id: uuid.UUID
    group: GroupRef = Field(description="Группа контрагентов: от неё зависит процесс")
    counterparty: CounterpartyRef = Field(description="Вуз или клиент — одной ссылкой")
    university: UniversityRef | None = Field(description="Вуз, если контрагент — вуз")
    client: ClientRef | None = Field(description="Клиент, если контрагент — не вуз")
    program: ProgramRef
    product: ProductRef | None = Field(description="Пусто у продуктонезависимой программы")
    owner: UserRef
    stage: StageRef
    stage_entered_at: datetime
    days_on_stage: int
    norm_days: int | None
    status: str
    version: int = Field(description="Передаётся в expected_version при переходе")
    last_activity_at: datetime
    open_signals: list[SignalBrief]


class TransitionOut(BaseModel):
    id: uuid.UUID
    from_stage: StageRef | None
    to_stage: StageRef
    occurred_at: datetime
    actor: UserRef | None
    comment: str | None
    source: str


class InteractionDetail(InteractionListItem):
    workflow_version_id: uuid.UUID
    contract: ContractOut | None
    history: list[TransitionOut]
    allowed_transitions: list[AllowedTransitionOut]
    signals: list[SignalOut]


class InteractionCreate(BaseModel):
    """Новая запись вручную. Контрагент — ровно один: вуз или клиент."""

    group_id: uuid.UUID
    university_id: uuid.UUID | None = None
    client_id: uuid.UUID | None = None
    program_id: uuid.UUID
    product_id: uuid.UUID | None = Field(
        default=None, description="Продукт из программы; у продуктонезависимой программы пусто"
    )
    owner_id: uuid.UUID | None = Field(
        default=None, description="Ответственный; по умолчанию — тот, кто создаёт запись"
    )
    comment: str = Field(default="", max_length=4000, description="Попадёт в первую запись истории")


class TransitionCreate(BaseModel):
    to_stage_id: uuid.UUID
    comment: str = Field(default="", max_length=4000)
    expected_version: int = Field(ge=1, description="Версия записи, которую видел пользователь")
    attachment_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)


class TransitionResult(BaseModel):
    transition: TransitionOut
    interaction: InteractionDetail


class NoteCreate(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


class NoteOut(BaseModel):
    id: uuid.UUID
    text: str
    author: UserRef
    created_at: datetime


class BulkTransitionRequest(BaseModel):
    interaction_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    to_stage_code: str = Field(
        max_length=60, description="Код этапа назначения в версии процесса взаимодействия"
    )
    comment: str = Field(default="", max_length=4000)


class OwnerChange(BaseModel):
    owner_id: uuid.UUID
    reason: str = Field(default="", max_length=4000)
    expected_version: int = Field(ge=1, description="Версия записи, которую видел пользователь")


class BulkOwnerRequest(BaseModel):
    interaction_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    owner_id: uuid.UUID
    reason: str = Field(default="", max_length=4000)


class BulkItemResult(BaseModel):
    interaction_id: uuid.UUID
    ok: bool
    version: int | None = Field(default=None, description="Новая версия записи при успехе")
    code: ErrorCode | None = Field(default=None, description="Код ошибки из каталога при отказе")
    detail: str | None = None


class BulkResult(BaseModel):
    """Частичный успех — обычный ответ: у каждой записи свой итог."""

    results: list[BulkItemResult]
    succeeded: int
    failed: int
