from typing import Literal

from pydantic import BaseModel, Field


class PaymentRowOut(BaseModel):
    row_no: int = Field(description="Номер записи в файле, с 1")
    key: str = Field(description="Номер заявки")
    action: Literal["created", "updated", "unchanged", "error"]
    detail: str | None


class PaymentImportOut(BaseModel):
    dry_run: bool
    created: int = Field(description="Новые записи B2C")
    updated: int = Field(description="Известные записи, к которым добавилась оплата")
    unchanged: int = Field(description="Оплата уже была загружена раньше")
    errors: int
    rows: list[PaymentRowOut]
