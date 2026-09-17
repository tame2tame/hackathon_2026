"""Отправка уведомлений во внешние каналы за общим интерфейсом: Telegram, Max и почта (SMTP).

Настоящие Bot API и почтовый сервер подключаются адресом и секретом в настройках канала; на стенде
вместо мессенджеров отвечает заглушка из `backend/mocks/messengers.py`, а почту принимает Mailpit.
"""

import os
import re
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Protocol

import httpx
from starlette.concurrency import run_in_threadpool

from app.modules.notifications.models import NotificationChannel

TIMEOUT_SECONDS = 10.0
# Токены читаются только из переменных NOTIFY_*: иначе через настройку канала можно было бы
# отправить наружу любой секрет окружения, например адрес базы с паролем.
SECRET_REF_PATTERN = re.compile(r"^NOTIFY_[A-Z0-9_]{1,60}$")
# Заглушке мессенджеров токен не нужен, но путь Bot API без него не собрать.
MOCK_TOKEN = "mock-token"  # noqa: S105 — не секрет, а подстановка для заглушки

# Тесты подменяют транспорт HTTP, чтобы ходить в заглушку без сети.
http_transport: httpx.AsyncBaseTransport | None = None


class DeliveryError(RuntimeError):
    """Канал не принял сообщение: отправка повторится позже."""


@dataclass(frozen=True, slots=True)
class OutgoingMessage:
    address: str
    title: str
    body: str
    link: str | None = None

    def text(self) -> str:
        parts = [self.title, self.body]
        if self.link:
            parts.append(self.link)
        return "\n\n".join(parts)


class Sender(Protocol):
    async def send(self, message: OutgoingMessage) -> None: ...


def secret(channel: NotificationChannel) -> str | None:
    if not channel.secret_ref or not SECRET_REF_PATTERN.match(channel.secret_ref):
        return None
    return os.environ.get(channel.secret_ref)


async def _post(url: str, *, params: dict[str, str] | None, payload: dict[str, Any]) -> Any:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS, transport=http_transport) as client:
            response = await client.post(url, params=params, json=payload)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise DeliveryError(type(error).__name__) from error


class TelegramSender:
    """Telegram Bot API: `sendMessage` в чат сотрудника."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def send(self, message: OutgoingMessage) -> None:
        answer = await _post(
            f"{self._base_url}/bot{self._token}/sendMessage",
            params=None,
            payload={"chat_id": message.address, "text": message.text()},
        )
        if not isinstance(answer, dict) or answer.get("ok") is not True:
            raise DeliveryError("Telegram не подтвердил отправку")


class MaxSender:
    """Bot API мессенджера Max: сообщение пользователю по его идентификатору."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token

    async def send(self, message: OutgoingMessage) -> None:
        answer = await _post(
            f"{self._base_url}/messages",
            params={"access_token": self._token, "user_id": message.address},
            payload={"text": message.text()},
        )
        if not isinstance(answer, dict) or "message" not in answer:
            raise DeliveryError("Max не подтвердил отправку")


class EmailSender:
    """Почта через SMTP: подходит и Exchange, и любой другой сервер с SMTP."""

    def __init__(
        self,
        host: str,
        port: int,
        sender: str,
        username: str | None = None,
        password: str | None = None,
        starttls: bool = False,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._username = username
        self._password = password
        self._starttls = starttls

    def _send_sync(self, message: OutgoingMessage) -> None:
        email = EmailMessage()
        email["From"] = self._sender
        email["To"] = message.address
        email["Subject"] = message.title
        email.set_content(message.text())
        with smtplib.SMTP(self._host, self._port, timeout=TIMEOUT_SECONDS) as smtp:
            if self._starttls:
                smtp.starttls()
            if self._username and self._password:
                smtp.login(self._username, self._password)
            smtp.send_message(email)

    async def send(self, message: OutgoingMessage) -> None:
        try:
            await run_in_threadpool(self._send_sync, message)
        except (OSError, smtplib.SMTPException) as error:
            raise DeliveryError(type(error).__name__) from error


def sender_for(channel: NotificationChannel) -> Sender:
    settings = channel.settings or {}
    base_url = str(settings.get("base_url", ""))
    match channel.kind:
        case "telegram":
            return TelegramSender(base_url, secret(channel) or MOCK_TOKEN)
        case "max":
            return MaxSender(base_url, secret(channel) or MOCK_TOKEN)
        case _:
            return EmailSender(
                host=str(settings.get("host", "127.0.0.1")),
                port=int(settings.get("port", 25)),
                sender=str(settings.get("sender", "radar@example.com")),
                username=settings.get("username"),
                password=secret(channel),
                starttls=bool(settings.get("starttls", False)),
            )
