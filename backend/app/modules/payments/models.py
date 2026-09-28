"""Оплаты частных лиц из платёжной системы: номер заявки, курс и поток.

Персональных данных здесь нет — человек лежит в `client` зашифрованным, а оплата лишь ссылается
на него и на запись. Номер заявки уникален: повторная загрузка той же выгрузки ничего не дублирует.
"""

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, Timestamps, UUIDPrimaryKey


class Payment(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "payment"

    order_no: Mapped[str] = mapped_column(String(80), unique=True)
    interaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interaction.id", ondelete="RESTRICT"), index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("client.id", ondelete="RESTRICT"), index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("program.id", ondelete="RESTRICT"))
    # Номер потока в LMS: по нему выгрузка для зачисления собирается на один поток.
    stream_no: Mapped[int | None]
    imported_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL")
    )
