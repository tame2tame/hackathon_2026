"""Настройка эскалации зависших записей: срок без изменений и роль, которой уходит уведомление."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AppSetting

STALLED_ESCALATION_KEY = "stalled_escalation"


class EscalationSetting(BaseModel):
    """Привязка к роли, а не к человеку: сменится руководитель — уведомления пойдут новому."""

    model_config = ConfigDict(extra="forbid")

    enabled: bool = True
    days: int = Field(default=14, ge=1, le=365, description="Сколько дней без изменений терпим")
    notify_role: Literal["manager", "admin"] = Field(
        default="manager",
        description="manager — руководителю команды КАМа, admin — администраторам",
    )


async def load_escalation(session: AsyncSession) -> EscalationSetting:
    setting = await session.get(AppSetting, STALLED_ESCALATION_KEY)
    if setting is None:
        return EscalationSetting()
    try:
        return EscalationSetting.model_validate(setting.value)
    except ValidationError:
        return EscalationSetting()
