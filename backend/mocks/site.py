"""Мок сайта ИТ Школы: отдаёт заявки вузов.

Часть заявок указывает вуз и программу, которые есть в справочниках, часть — нет:
на них проверяется очередь несопоставленных. Запуск: `uvicorn mocks.site:app --port 8101`.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import FastAPI

from app.demo import PROGRAMS, UNIVERSITIES

app = FastAPI(title="Мок сайта", docs_url="/docs")

# Заявки от вузов, которых нет в справочнике: они и попадут в очередь несопоставленных.
UNKNOWN = (
    ("Университет без справочника", "Квантовые вычисления"),
    ("Институт из будущего", "Робототехника"),
)


def _applications() -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    items: list[dict[str, Any]] = []
    for index, (_, short_name, _, _) in enumerate(UNIVERSITIES[:4]):
        program_name, *_ = PROGRAMS[index % len(PROGRAMS)]
        items.append(
            {
                "id": f"site-{index + 1}",
                "university": short_name,
                "program": program_name,
                "contact": "Приёмная комиссия",
                "comment": "Заявка с сайта на программу",
                "received_at": (now - timedelta(days=index)).isoformat(),
            }
        )
    for index, (university, program) in enumerate(UNKNOWN, start=len(items) + 1):
        items.append(
            {
                "id": f"site-{index}",
                "university": university,
                "program": program,
                "contact": None,
                "comment": "Вуза нет в справочнике",
                "received_at": (now - timedelta(days=index)).isoformat(),
            }
        )
    return items


@app.get("/api/applications", summary="Заявки с сайта")
async def applications() -> dict[str, Any]:
    return {"items": _applications()}
