"""Собирает `docs/USER_GUIDE.md` из встроенной справки: один источник для интерфейса и документа.

Запуск: `python -m scripts.export_help` (или `make help`). CI сверяет результат с файлом
в репозитории — так документ не расходится с тем, что видит пользователь на экране.
"""

import argparse
import sys
from pathlib import Path

from app.modules.help.service import topics

# В продукте картинка приходит по адресу API, в документе — лежит файлом рядом с кодом.
API_IMAGES = "/api/v1/help/images/"
REPO_IMAGES = "../backend/app/help/images/"

GUIDE_PATH = Path(__file__).resolve().parents[2] / "docs" / "USER_GUIDE.md"
HEADER = """# Руководство пользователя

Этот файл собирается из встроенной справки командой `make help`: те же разделы пользователь
видит в самом продукте (значок «Справка», методы `GET /api/v1/help`). Править нужно исходники
в [`backend/app/help/`](../backend/app/help), а не этот файл.

Эксплуатация стенда — в [руководстве администратора](ADMIN_GUIDE.md); как считаются радар,
нормы и рейтинг — в [методах обработки данных](DATA_PROCESSING.md).
"""


def render() -> str:
    parts = [HEADER, "\n## Содержание\n"]
    for topic in topics():
        parts.append(f"- [{topic.title}](#{topic.slug}) — {topic.summary}\n")
    for topic in topics():
        roles = ", ".join(sorted(topic.roles))
        parts.append(f'\n<a id="{topic.slug}"></a>\n\n## {topic.title}\n\n')
        parts.append(f"*Кому показывается: {roles}.*\n\n")
        parts.append(f"{topic.body.replace(API_IMAGES, REPO_IMAGES)}\n")
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description="Сборка руководства пользователя")
    parser.add_argument("--check", action="store_true", help="Сравнить без записи")
    args = parser.parse_args()

    content = render()
    if args.check:
        current = GUIDE_PATH.read_text(encoding="utf-8") if GUIDE_PATH.exists() else ""
        if current != content:
            print(
                "docs/USER_GUIDE.md не совпадает со встроенной справкой. "
                "Выполните make help и закоммитьте файл.",
                file=sys.stderr,
            )
            return 1
        print("Руководство совпадает со встроенной справкой.")
        return 0

    GUIDE_PATH.write_text(content, encoding="utf-8")
    print(f"Руководство собрано: {GUIDE_PATH} ({len(topics())} разделов)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
