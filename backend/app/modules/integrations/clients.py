"""Клиенты внешних систем за узкими интерфейсами: LMS отдаёт метрики, сайт — заявки, оба принимают
изменения записей CRM.

Настоящая LMS — Moodle Web Services, но код зависит только от интерфейса, поэтому в тестах
и на демо-стенде вместо неё работают моки из `backend/mocks/`. Контракт приёма документов
(`POST /api/crm/interactions`) — наш, пока заказчик не дал свой: меняется только адаптер.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol, runtime_checkable

import httpx

TIMEOUT_SECONDS = 10.0


class SourceUnavailableError(RuntimeError):
    """Внешняя система не ответила или ответила не тем: остальные источники это не касается."""


@dataclass(frozen=True, slots=True)
class CourseMetrics:
    """Сколько обучающихся и потоков у программы вуза за месяц."""

    university_name: str
    program_name: str
    period_month: date
    students: int
    streams: int


@dataclass(frozen=True, slots=True)
class ApplicationRecord:
    """Заявка с сайта — как её заполнил человек, без сопоставления со справочниками."""

    external_id: str
    university_name: str
    program_name: str
    contact_name: str | None
    comment: str | None
    received_at: datetime
    applications: int = 1


# runtime_checkable: синхронизация выбирает ветку по типу клиента, а не по строке вида источника.
@runtime_checkable
class LmsClient(Protocol):
    async def fetch_metrics(self) -> list[CourseMetrics]: ...


@runtime_checkable
class SiteClient(Protocol):
    async def fetch_applications(self) -> list[ApplicationRecord]: ...


@dataclass(frozen=True, slots=True)
class PushResult:
    """Что получатель принял, а что отклонил с причиной. Неупомянутое будет отправлено снова."""

    accepted: frozenset[str]
    rejected: dict[str, str]


@runtime_checkable
class InteractionReceiver(Protocol):
    async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult: ...


PUSH_PATH = "/api/crm/interactions"


def _month(value: str) -> date:
    return date.fromisoformat(f"{value}-01") if len(value) == 7 else date.fromisoformat(value)


async def _get(
    base_url: str,
    path: str,
    params: dict[str, Any] | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(
            base_url=base_url, timeout=TIMEOUT_SECONDS, transport=transport
        ) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SourceUnavailableError(str(error)) from error


async def _post(
    base_url: str,
    path: str,
    payload: dict[str, Any],
    transport: httpx.AsyncBaseTransport | None = None,
) -> Any:
    try:
        async with httpx.AsyncClient(
            base_url=base_url, timeout=TIMEOUT_SECONDS, transport=transport
        ) as client:
            response = await client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as error:
        raise SourceUnavailableError(str(error)) from error


def _push_result(answer: Any) -> PushResult:
    if not isinstance(answer, dict):
        raise SourceUnavailableError("Получатель ответил не объектом JSON")
    rejected = {
        str(item.get("id")): str(item.get("reason") or "Причина не указана")
        for item in answer.get("rejected", [])
        if isinstance(item, dict)
    }
    return PushResult(frozenset(str(key) for key in answer.get("accepted", [])), rejected)


async def push_documents(
    base_url: str,
    documents: list[dict[str, Any]],
    transport: httpx.AsyncBaseTransport | None = None,
) -> PushResult:
    """Пакет документов одним запросом: обмен по расписанию, а не по вебхуку на каждое изменение."""
    return _push_result(await _post(base_url, PUSH_PATH, {"items": documents}, transport))


class MoodleLmsClient:
    """Moodle Web Services: курсы, зачисленные и группы сводятся к метрикам месяца."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._token = token
        # Транспорт подменяют тесты, чтобы ходить в мок без сети.
        self._transport = transport

    async def fetch_metrics(self) -> list[CourseMetrics]:
        payload = await _get(
            self._base_url,
            "/webservice/rest/server.php",
            {
                "wstoken": self._token or "",
                "wsfunction": "core_course_get_courses_by_field",
                "moodlewsrestformat": "json",
            },
            transport=self._transport,
        )
        courses = payload.get("courses", []) if isinstance(payload, dict) else []
        metrics: list[CourseMetrics] = []
        for course in courses:
            try:
                metrics.append(
                    CourseMetrics(
                        university_name=course["university"],
                        program_name=course["program"],
                        period_month=_month(course["month"]),
                        students=int(course["students"]),
                        streams=int(course["groups"]),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                raise SourceUnavailableError(f"LMS вернула неожиданный курс: {error}") from error
        return metrics

    async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult:
        return await push_documents(self._base_url, documents, self._transport)


class HttpSiteClient:
    """Заявки с сайта ИТ Школы."""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url
        self._token = token
        self._transport = transport

    async def fetch_applications(self) -> list[ApplicationRecord]:
        payload = await _get(
            self._base_url,
            "/api/applications",
            {"token": self._token or ""},
            transport=self._transport,
        )
        items = payload.get("items", []) if isinstance(payload, dict) else []
        records: list[ApplicationRecord] = []
        for item in items:
            try:
                records.append(
                    ApplicationRecord(
                        external_id=str(item["id"]),
                        university_name=item["university"],
                        program_name=item["program"],
                        contact_name=item.get("contact"),
                        comment=item.get("comment"),
                        received_at=datetime.fromisoformat(item["received_at"]).astimezone(UTC),
                    )
                )
            except (KeyError, TypeError, ValueError) as error:
                raise SourceUnavailableError(f"Сайт вернул неожиданную заявку: {error}") from error
        return records

    async def push_interactions(self, documents: list[dict[str, Any]]) -> PushResult:
        return await push_documents(self._base_url, documents, self._transport)
