"""Регистрация всех моделей в метаданных — для Alembic и тестов."""

from app.core.db import Base
from app.modules.analytics.models import RatingWeightSet
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
from app.modules.imports.models import ImportBatch, ImportProfile, ImportRow
from app.modules.integrations.models import IntegrationSource, SiteApplication, SyncRun
from app.modules.interactions.models import (
    AssignmentChange,
    Attachment,
    Contract,
    Interaction,
    InteractionContact,
    InteractionNote,
    Transition,
)
from app.modules.metrics.models import ProgramMetric
from app.modules.radar.models import RadarSignal
from app.modules.reports.models import ReportJob
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
    "ImportBatch",
    "ImportProfile",
    "ImportRow",
    "IntegrationSource",
    "Interaction",
    "InteractionContact",
    "InteractionNote",
    "Product",
    "Program",
    "ProgramMetric",
    "ProgramProduct",
    "RadarSignal",
    "RatingWeightSet",
    "ReportJob",
    "SiteApplication",
    "Stage",
    "StageNorm",
    "StageTransitionRule",
    "SyncRun",
    "Team",
    "Transition",
    "University",
    "Vendor",
    "WorkflowTemplate",
    "WorkflowVersion",
    "product_direction",
]
