"""Схемы workflow: этапы, правила переходов, версия шаблона."""

import uuid

from pydantic import BaseModel, ConfigDict


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
