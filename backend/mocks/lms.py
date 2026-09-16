"""Мок LMS вместо Moodle: отдаёт курсы с обучающимися и группами.

Данные согласованы с демо-стендом: те же программы и вузы, что в `app/demo_full.py`.
Запуск: `uvicorn mocks.lms:app --port 8100`.
"""

import random
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Query

from app.demo_full import CITIES, PROGRAMS_V1, SEED, UNIVERSITY_KINDS, month_starts

COURSES_PER_MONTH = 12

app = FastAPI(title="Мок LMS", docs_url="/docs")


def _courses() -> list[dict[str, Any]]:
    rng = random.Random(SEED)  # noqa: S311 — демо-данные, а не криптография
    universities = [f"{kind} ({city})" for city in CITIES[:6] for kind, _ in UNIVERSITY_KINDS]
    months = month_starts(datetime.now(UTC))
    courses: list[dict[str, Any]] = []
    for index, month in enumerate(months):
        for number in range(COURSES_PER_MONTH):
            university = universities[(index + number) % len(universities)]
            program, *_ = PROGRAMS_V1[(index + number) % len(PROGRAMS_V1)]
            courses.append(
                {
                    "id": index * COURSES_PER_MONTH + number + 1,
                    "fullname": f"{program} — {university}",
                    "university": university,
                    "program": program,
                    "month": month.strftime("%Y-%m"),
                    "students": rng.randint(12, 90),
                    "groups": rng.randint(1, 4),
                }
            )
    return courses


@app.get("/webservice/rest/server.php", summary="Moodle Web Services")
async def webservice(
    wsfunction: str = Query(default="core_course_get_courses_by_field"),
) -> dict[str, Any]:
    match wsfunction:
        case "core_course_get_courses_by_field":
            return {"courses": _courses()}
        case _:
            return {"exception": "invalid_parameter_exception", "message": wsfunction}
