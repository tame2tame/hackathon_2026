"""Роли пользователей (ARCHITECTURE.md, раздел 4)."""

from enum import StrEnum


class Role(StrEnum):
    KAM = "kam"
    MANAGER = "manager"
    ADMIN = "admin"
