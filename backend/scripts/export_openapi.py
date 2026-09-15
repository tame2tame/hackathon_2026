"""Экспорт схемы API в contracts/openapi.yaml (ADR-004).

python -m scripts.export_openapi          — записать файл
python -m scripts.export_openapi --check  — только сравнить (для CI)
"""

import argparse
import sys
from pathlib import Path

import yaml

from app.main import create_app

CONTRACT_PATH = Path(__file__).resolve().parents[2] / "contracts" / "openapi.yaml"


def render() -> str:
    schema = create_app().openapi()
    return yaml.safe_dump(schema, allow_unicode=True, sort_keys=False, width=100)


def main() -> int:
    parser = argparse.ArgumentParser(description="Экспорт схемы OpenAPI")
    parser.add_argument("--check", action="store_true", help="Сравнить без записи")
    args = parser.parse_args()

    content = render()
    if args.check:
        current = CONTRACT_PATH.read_text(encoding="utf-8") if CONTRACT_PATH.exists() else ""
        if current != content:
            print(
                "contracts/openapi.yaml не совпадает со схемой приложения. "
                "Выполните make openapi и закоммитьте файл.",
                file=sys.stderr,
            )
            return 1
        print("Контракт совпадает со схемой приложения.")
        return 0

    CONTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONTRACT_PATH.write_text(content, encoding="utf-8")
    print(f"Схема записана в {CONTRACT_PATH.relative_to(CONTRACT_PATH.parents[1])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
