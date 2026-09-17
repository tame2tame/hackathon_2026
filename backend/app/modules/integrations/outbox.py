"""Исходящий обмен: изменения записей CRM уходят в LMS и CMS сайта пакетами JSON.

Отметка об изменении пишется в той же транзакции, что и само изменение (transactional outbox):
если запись не сохранилась, отправлять нечего, а если сохранилась — отправка не потеряется.
Воркер раз в минуту строит документы по последнему состоянию и отправляет их с повторами.
"""

import uuid
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ErrorCode
from app.modules.exchange.documents import build_documents
from app.modules.integrations.clients import (
    HttpSiteClient,
    InteractionReceiver,
    MoodleLmsClient,
    SourceUnavailableError,
)
from app.modules.integrations.models import IntegrationOutbox, IntegrationSource, SyncRun

PUSH_BATCH = 100
MAX_PUSH_ATTEMPTS = 8
BACKOFF_MINUTES = (1, 5, 15, 60)


async def mark_changed(
    session: AsyncSession, interaction_ids: Sequence[uuid.UUID], reason: str
) -> None:
    """Ставит записи в очередь каждому получателю. Уже ждущая отправка не дублируется."""
    ids = list(dict.fromkeys(interaction_ids))
    if not ids:
        return
    sources = list(
        await session.scalars(
            select(IntegrationSource.id).where(IntegrationSource.push_enabled.is_(True))
        )
    )
    if not sources:
        return
    await session.execute(
        insert(IntegrationOutbox)
        .values(
            [
                {
                    "id": uuid.uuid4(),
                    "source_id": source_id,
                    "interaction_id": interaction_id,
                    "reason": reason,
                    "status": "pending",
                }
                for source_id in sources
                for interaction_id in ids
            ]
        )
        .on_conflict_do_nothing(
            index_elements=["source_id", "interaction_id"],
            index_where=text("status = 'pending'"),
        )
    )


def receiver_for(source: IntegrationSource) -> InteractionReceiver:
    if source.kind == "lms":
        return MoodleLmsClient(source.base_url)
    return HttpSiteClient(source.base_url)


def _retry(entry: IntegrationOutbox, error: str, now: datetime) -> str:
    entry.attempts += 1
    entry.last_error = error[:300]
    if entry.attempts >= MAX_PUSH_ATTEMPTS:
        entry.status = "failed"
        return "failed"
    pause = BACKOFF_MINUTES[min(entry.attempts, len(BACKOFF_MINUTES)) - 1]
    entry.next_attempt_at = now + timedelta(minutes=pause)
    return "retried"


async def push_source(
    session: AsyncSession,
    source: IntegrationSource,
    client: InteractionReceiver | None = None,
    now: datetime | None = None,
) -> SyncRun:
    """Одна отправка очереди получателю; запись в журнале появляется и при отказе."""
    now = now or datetime.now(UTC)
    run = SyncRun(source_id=source.id, started_at=now, status="running", direction="push", stats={})
    session.add(run)
    await session.flush()

    entries = list(
        await session.scalars(
            select(IntegrationOutbox)
            .where(
                IntegrationOutbox.source_id == source.id,
                IntegrationOutbox.status == "pending",
                IntegrationOutbox.next_attempt_at <= now,
            )
            .order_by(IntegrationOutbox.created_at)
            .limit(PUSH_BATCH)
            .with_for_update(skip_locked=True)
        )
    )
    counter: Counter[str] = Counter()
    if entries:
        documents = await build_documents(session, [entry.interaction_id for entry in entries], now)
        client = client or receiver_for(source)
        try:
            result = await client.push_interactions(
                [document.model_dump(mode="json") for document in documents]
            )
        except SourceUnavailableError as error:
            for entry in entries:
                counter[_retry(entry, str(error), now)] += 1
            run.status = "failed"
            run.error_code = ErrorCode.INTEGRATION_UNAVAILABLE.value
        else:
            for entry in entries:
                key = str(entry.interaction_id)
                if key in result.accepted:
                    entry.status, entry.sent_at = "sent", now
                    counter["sent"] += 1
                elif key in result.rejected:
                    # Отказ по содержанию повтором не лечится: разбирается человеком по журналу.
                    entry.status, entry.last_error = "failed", result.rejected[key][:300]
                    counter["rejected"] += 1
                else:
                    counter[_retry(entry, "Получатель не подтвердил приём", now)] += 1
    if run.status == "running":
        run.status = "done"
        source.last_push_at = now
    run.stats = {"sent": 0, **counter}
    run.finished_at = datetime.now(UTC)
    await session.flush()
    return run


async def push_all(session: AsyncSession, now: datetime | None = None) -> list[SyncRun]:
    """Отправляет очередь всем получателям: отказ одного не мешает остальным."""
    sources = await session.scalars(
        select(IntegrationSource).where(IntegrationSource.push_enabled.is_(True))
    )
    runs = [await push_source(session, source, now=now) for source in sources]
    await session.commit()
    return runs


async def list_outbox(
    session: AsyncSession, source_id: uuid.UUID, status: str | None, limit: int = 100
) -> list[IntegrationOutbox]:
    stmt = (
        select(IntegrationOutbox)
        .where(IntegrationOutbox.source_id == source_id)
        .order_by(IntegrationOutbox.created_at.desc())
        .limit(limit)
    )
    if status:
        stmt = stmt.where(IntegrationOutbox.status == status)
    return list(await session.scalars(stmt))
