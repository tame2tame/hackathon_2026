"""Схемы взаимодействий: элемент списка, карточка, переход."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.modules.catalogs.schemas import ProductRef, ProgramRef, UniversityRef, UserRef
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
    university: UniversityRef
    program: ProgramRef
    product: ProductRef
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


class TransitionCreate(BaseModel):
    to_stage_id: uuid.UUID
    comment: str = Field(default="", max_length=4000)
    expected_version: int = Field(ge=1, description="Версия записи, которую видел пользователь")
    attachment_ids: list[uuid.UUID] = Field(default_factory=list, max_length=20)


class TransitionResult(BaseModel):
    transition: TransitionOut
    interaction: InteractionDetail
