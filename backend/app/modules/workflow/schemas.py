"""Схемы workflow: этапы, правила переходов, версия шаблона."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StageRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    position: int


class StageOut(StageRef):
    kind: str
    bulk_allowed: bool
    required_document_types: list[str]
    norm_days: int | None


class TransitionRuleOut(BaseModel):
    from_stage_id: uuid.UUID
    to_stage_id: uuid.UUID
    requires_comment: bool
    requires_attachment: bool


class AllowedTransitionOut(BaseModel):
    to_stage: StageRef
    requires_comment: bool
    requires_attachment: bool


class WorkflowOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    name: str
    version_no: int
    stages: list[StageOut]
    transitions: list[TransitionRuleOut]


class StageNormOut(BaseModel):
    stage_code: str
    stage_name: str
    norm_days: int
    source: str = Field(description="manual — задана вручную, suggested — принята подсказка")
    suggested_median_days: int | None = Field(
        description="Типичный срок этапа по завершённым переходам"
    )
    suggested_percentile_days: int | None = Field(
        description="80-й перцентиль: срок, в который укладывается большинство"
    )
    sample_size: int | None = Field(description="Сколько завершённых этапов легло в подсказку")


class NormUpdate(BaseModel):
    norm_days: int = Field(ge=1, le=365, description="Новая норма этапа в днях")


class WorkflowTemplateCreate(BaseModel):
    name: str = Field(max_length=200, min_length=3)


class WorkflowTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_default: bool


class StageDraft(BaseModel):
    """Этап черновика: код неизменяем и связывает норму с этапом между версиями."""

    code: str = Field(max_length=60, pattern=r"^[a-z][a-z0-9_]*$")
    name: str = Field(max_length=200)
    position: int = Field(ge=1)
    kind: Literal["start", "normal", "final"] = "normal"
    bulk_allowed: bool = False
    required_document_types: list[str] = Field(default_factory=list)
    norm_days: int | None = Field(default=None, ge=1, le=365)


class TransitionDraft(BaseModel):
    from_code: str = Field(max_length=60)
    to_code: str = Field(max_length=60)
    requires_comment: bool = True
    requires_attachment: bool = False


class VersionPatch(BaseModel):
    """Что меняем в черновике. Пропущенное поле остаётся как было."""

    stages: list[StageDraft] | None = Field(default=None, min_length=2)
    transitions: list[TransitionDraft] | None = None


class StageRename(BaseModel):
    name: str = Field(max_length=200, min_length=2)


class PublishRequest(BaseModel):
    migration_map: dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Код этапа прежней схемы → код новой. Необязательна: записи с удалённого этапа "
            "сами переходят на ближайший предыдущий этап, а если его нет — на следующий"
        ),
    )


class StageRenameOut(BaseModel):
    code: str
    old_name: str
    new_name: str


class StageMoveOut(BaseModel):
    """Куда переедут открытые записи этапа прежней схемы."""

    from_code: str
    from_name: str
    stage_removed: bool = Field(description="Этапа нет в новой схеме")
    open_interactions: int
    to_code: str
    to_name: str
    automatic: bool = Field(description="Этап выбран автоматически, а не картой переноса")


class PublishPreview(BaseModel):
    """Что изменит публикация: данные для окна подтверждения."""

    renamed: list[StageRenameOut]
    moves: list[StageMoveOut] = Field(
        description="Удалённые этапы и этапы, записи с которых карта переносит на другой"
    )
    added: list[StageRef]
    moved_interactions: int = Field(description="Сколько открытых записей перейдёт на новую схему")
    requires_admin: bool = Field(
        description="Черновик переименовывает этапы: опубликовать его может только администратор"
    )


class VersionOut(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID
    version_no: int
    status: str = Field(description="draft, published или retired")
    published_at: datetime | None
    stages: list[StageOut]
    transitions: list[TransitionRuleOut]
