"""Схемы вложений."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttachmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    mime_type: str
    size_bytes: int
    document_type: str | None = Field(description="Тип документа этапа, если указан при загрузке")
    sha256: str = Field(description="Контрольная сумма: видно повторную загрузку того же файла")
    stage_id: uuid.UUID = Field(description="Этап, на котором файл загружен")
    uploaded_by: uuid.UUID
    uploaded_at: datetime
