"""Документ обмена `radar-vuzov/interaction@1`: запись CRM для LMS, CMS сайта и выгрузки по API.

Состав — то, что жюри назвало для JSON-выгрузки: статус, ответственный, контрагент (вуз), программа
и продукт, плюс ключи связей с записями реляционной БД и файлами в S3-хранилище.
"""

import uuid
from datetime import date, datetime
from typing import Final, Literal

from pydantic import BaseModel, Field

DOCUMENT_FORMAT: Final = "radar-vuzov/interaction@1"


class DocumentRecord(BaseModel):
    """Ключ записи в базе CRM."""

    table: Literal["interaction"] = "interaction"
    id: uuid.UUID
    version: int = Field(
        description="Растёт с каждым изменением: получатель отбрасывает устаревшие документы"
    )


class DocumentGroup(BaseModel):
    id: uuid.UUID
    code: str
    name: str


class DocumentStatus(BaseModel):
    state: Literal["active", "paused", "completed", "cancelled"]
    stage_code: str
    stage_name: str
    stage_entered_at: datetime
    workflow_template_id: uuid.UUID
    workflow_version_id: uuid.UUID


class DocumentPerson(BaseModel):
    id: uuid.UUID
    full_name: str


class DocumentCounterparty(BaseModel):
    kind: Literal["university", "person", "organization"]
    id: uuid.UUID = Field(description="Ключ записи university или client")
    name: str
    short_name: str
    region: str | None
    city: str | None
    inn: str | None = Field(description="ИНН организации")


class DocumentProgram(BaseModel):
    id: uuid.UUID
    name: str
    direction_code: str
    direction_name: str
    lms_course_ref: str | None = Field(description="Курс программы в LMS, если известен")


class DocumentProduct(BaseModel):
    id: uuid.UUID
    name: str
    vendor_name: str


class DocumentContract(BaseModel):
    id: uuid.UUID
    number: str
    signed_at: date | None
    license_valid_until: date | None
    transfer_status: str | None


class DocumentFile(BaseModel):
    id: uuid.UUID = Field(description="Ключ записи attachment")
    document_type: str | None
    file_name: str
    mime_type: str
    size_bytes: int
    sha256: str = Field(description="Контрольная сумма: сверка файла без его скачивания")
    stage_code: str
    uploaded_at: datetime
    storage: dict[str, str] = Field(
        description="Где лежит файл: backend (s3 или local), bucket и key"
    )


class DocumentApplication(BaseModel):
    id: uuid.UUID = Field(description="Ключ записи site_application")
    external_id: str = Field(description="Номер заявки на сайте")
    received_at: datetime


class InteractionDocument(BaseModel):
    format: Literal["radar-vuzov/interaction@1"] = DOCUMENT_FORMAT
    record: DocumentRecord
    group: DocumentGroup
    status: DocumentStatus
    owner: DocumentPerson = Field(description="Ответственный КАМ")
    counterparty: DocumentCounterparty
    program: DocumentProgram
    product: DocumentProduct | None
    contract: DocumentContract | None
    files: list[DocumentFile]
    site_applications: list[DocumentApplication]
    created_at: datetime
    updated_at: datetime
    exported_at: datetime
