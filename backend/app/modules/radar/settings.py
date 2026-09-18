"""Пороги радара из настроек администратора. Пока настройку не сохраняли, действуют умолчания."""

import logging
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.admin.models import AppSetting
from app.modules.radar.rules import DEFAULT_THRESHOLDS, RadarThresholds

RADAR_THRESHOLDS_KEY = "radar_thresholds"

logger = logging.getLogger("radar.settings")


class RadarThresholdsSetting(BaseModel):
    """Пороги в днях. Пропущенное поле получает значение по умолчанию."""

    model_config = ConfigDict(extra="forbid")

    license_warn_days: int = Field(
        default=DEFAULT_THRESHOLDS.license_warn_days,
        ge=1,
        le=365,
        description="За сколько дней до конца лицензии появляется предупреждение",
    )
    license_critical_days: int = Field(
        default=DEFAULT_THRESHOLDS.license_critical_days,
        ge=0,
        le=365,
        description="С какого остатка дней предупреждение становится серьёзным",
    )
    inactivity_low_days: int = Field(
        default=DEFAULT_THRESHOLDS.inactivity_low_days,
        ge=1,
        le=365,
        description="Сколько дней без изменений до сигнала о простое",
    )
    inactivity_medium_days: int = Field(
        default=DEFAULT_THRESHOLDS.inactivity_medium_days,
        ge=1,
        le=365,
        description="Сколько дней без изменений до заметного сигнала о простое",
    )

    @model_validator(mode="after")
    def check_order(self) -> Self:
        if self.license_critical_days > self.license_warn_days:
            raise ValueError("Серьёзный порог лицензии не может быть раньше предупреждения")
        if self.inactivity_medium_days < self.inactivity_low_days:
            raise ValueError("Заметный простой не может наступать раньше обычного")
        return self

    def thresholds(self) -> RadarThresholds:
        return RadarThresholds(**self.model_dump())


async def load_thresholds(session: AsyncSession) -> RadarThresholds:
    setting = await session.get(AppSetting, RADAR_THRESHOLDS_KEY)
    if setting is None:
        return DEFAULT_THRESHOLDS
    try:
        return RadarThresholdsSetting.model_validate(setting.value).thresholds()
    except ValidationError:
        # API проверяет настройку при сохранении; сюда попадает только запись, исправленная в базе.
        logger.warning("Настройка %s испорчена, пороги по умолчанию", RADAR_THRESHOLDS_KEY)
        return DEFAULT_THRESHOLDS
