"""Шифрование персональных данных контактов: email и телефон хранятся в БД зашифрованными.

Ключ задаётся переменной `PD_ENCRYPTION_KEY` (Fernet, 44 символа base64). Без ключа приложение
работает, но сохранить контакт с персональными данными не даст: лучше явный отказ, чем тихое
хранение открытым текстом.
"""

import hashlib
import hmac
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


class EncryptionNotConfiguredError(RuntimeError):
    """Ключ шифрования не задан, а без него персональные данные хранить нельзя."""


def generate_key() -> str:
    """Готовый ключ для .env: `python -c "from app.core.crypto import generate_key; ..."`."""
    return Fernet.generate_key().decode()


@lru_cache
def _fernet() -> Fernet:
    key = get_settings().pd_encryption_key
    if not key:
        raise EncryptionNotConfiguredError(
            "Не задан PD_ENCRYPTION_KEY: контакты с персональными данными сохранять нельзя."
        )
    return Fernet(key.encode())


def is_configured() -> bool:
    return bool(get_settings().pd_encryption_key)


def encrypt(value: str | None) -> bytes | None:
    if value is None or not value.strip():
        return None
    return _fernet().encrypt(value.strip().encode())


def decrypt(value: bytes | None) -> str | None:
    if value is None:
        return None
    try:
        return _fernet().decrypt(value).decode()
    except (InvalidToken, EncryptionNotConfiguredError):
        # Ключ сменился или данные испорчены: показываем пустоту, но не роняем список.
        return None


def fingerprint(value: str | None) -> str | None:
    """Отпечаток адреса: по нему находится дубль, но сам адрес из него не восстановить.

    Шифрование Fernet каждый раз даёт разный результат, поэтому искать по `email_enc` нельзя.
    Отпечаток — HMAC на том же ключе: без ключа он бесполезен даже вместе с копией базы.
    """
    if value is None or not value.strip():
        return None
    key = get_settings().pd_encryption_key
    if not key:
        raise EncryptionNotConfiguredError(
            "Не задан PD_ENCRYPTION_KEY: персональные данные сохранять нельзя."
        )
    return hmac.new(key.encode(), value.strip().casefold().encode(), hashlib.sha256).hexdigest()


def mask_email(value: str | None) -> str | None:
    """Почта для списка: видно, чья она, но адрес целиком нужно запрашивать отдельно.

    Список карточки не должен падать из-за одной странной строки, поэтому непохожее на адрес
    просто скрывается целиком.
    """
    if not value:
        return None
    name, separator, domain = value.partition("@")
    if not separator or not name or not domain:
        return None
    return f"{name[0]}***@{domain}"
