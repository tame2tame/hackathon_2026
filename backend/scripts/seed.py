"""Workflow и демо-данные: python -m scripts.seed [--workflow-only | --full]."""

import argparse
import asyncio
from datetime import UTC, datetime

from app.core.db import get_sessionmaker
from app.demo import seed_demo
from app.demo_full import seed_full
from app.modules.workflow.defaults import ensure_default_workflow


async def run(workflow_only: bool, full: bool) -> str:
    async with get_sessionmaker()() as session:
        if workflow_only:
            await ensure_default_workflow(session)
            await session.commit()
            return "Базовый workflow готов."
        if full:
            created = await seed_full(session, datetime.now(UTC))
            await session.commit()
            return "Демо-стенд v1 загружен." if created else "Демо-стенд v1 уже был загружен."
        created = await seed_demo(session, datetime.now(UTC))
        await session.commit()
        return "Демо-данные загружены." if created else "Демо-данные уже были загружены."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow-only", action="store_true", help="Создать только базовый workflow"
    )
    parser.add_argument(
        "--full", action="store_true", help="Полный стенд: 96 вузов, ~350 взаимодействий, метрики"
    )
    args = parser.parse_args()
    print(asyncio.run(run(args.workflow_only, args.full)))


if __name__ == "__main__":
    main()
