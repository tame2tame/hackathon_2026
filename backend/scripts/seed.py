"""Базовый workflow и демо-данные v0: python -m scripts.seed [--workflow-only]."""

import argparse
import asyncio
from datetime import UTC, datetime

from app.core.db import get_sessionmaker
from app.demo import seed_demo
from app.modules.workflow.defaults import ensure_default_workflow


async def run(workflow_only: bool) -> str:
    async with get_sessionmaker()() as session:
        if workflow_only:
            await ensure_default_workflow(session)
            await session.commit()
            return "Базовый workflow готов."
        created = await seed_demo(session, datetime.now(UTC))
        await session.commit()
        return "Демо-данные загружены." if created else "Демо-данные уже были загружены."


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workflow-only", action="store_true", help="Создать только базовый workflow"
    )
    args = parser.parse_args()
    print(asyncio.run(run(args.workflow_only)))


if __name__ == "__main__":
    main()
