"""Схемы workflow: этапы, правила переходов, версия шаблона."""

import uuid

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
