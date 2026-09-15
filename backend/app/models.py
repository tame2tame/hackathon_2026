"""Регистрация всех моделей в метаданных — для Alembic и тестов."""

from app.core.db import Base
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import (
    AppUser,
    ContactPerson,
    Direction,
    Product,
    Program,
    ProgramProduct,
    Team,
    University,
    Vendor,
    product_direction,
)
from app.modules.interactions.models import (
    AssignmentChange,
    Attachment,
    Contract,
    Interaction,
    InteractionContact,
    InteractionNote,
    Transition,
)
from app.modules.radar.models import RadarSignal
from app.modules.workflow.models import (
    Stage,
    StageNorm,
    StageTransitionRule,
    WorkflowTemplate,
    WorkflowVersion,
)

__all__ = [
    "AppUser",
    "AssignmentChange",
    "Attachment",
    "AuditLog",
    "Base",
    "ContactPerson",
    "Contract",
    "Direction",
    "Interaction",
    "InteractionContact",
    "InteractionNote",
    "Product",
    "Program",
    "ProgramProduct",
    "RadarSignal",
    "Stage",
    "StageNorm",
    "StageTransitionRule",
    "Team",
    "Transition",
    "University",
    "Vendor",
    "WorkflowTemplate",
    "WorkflowVersion",
    "product_direction",
]
