"""Исходящий обмен: изменения записей CRM уходят в LMS и CMS сайта пакетами JSON.

Отметка об изменении пишется в той же транзакции, что и само изменение (transactional outbox):
если запись не сохранилась, отправлять нечего, а если сохранилась — отправка не потеряется.

Воркер захватывает строки очереди арендой и сразу фиксирует захват, а сеть вызывает уже без
блокировок: переход КАМа не ждёт медленного получателя. Каждое новое изменение ждущей записи
увеличивает `change_seq`; отправка засчитывается, только если счётчик тот же, что при захвате,
иначе документ устарел и запись уйдёт ещё раз.
"""

import uuid
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, select, text, update
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
from app.modules.interactions.models import Interaction

PUSH_BATCH = 100
MAX_PUSH_ATTEMPTS = 8
BACKOFF_MINUTES = (1, 5, 15, 60)
LEASE = timedelta(minutes=5)


async def mark_changed(
    session: AsyncSession,
    interaction_ids: Sequence[uuid.UUID],
    reason: str,
    *,
    touch: bool = False,
) -> None:
    """Ставит записи в очередь каждому получателю. Ждущая отправка не дублируется.

    `touch` сдвигает `updated_at` записи, когда само изменение её строку не трогает
    (например, заявка сайта привязалась к записи): иначе выгрузка по `updated_since` его не увидит.
    """
    ids = list(dict.fromkeys(interaction_ids))
    if not ids:
        return
    if touch:
        await session.execute(
            update(Interaction).where(Interaction.id.in_(ids)).values(updated_at=func.now())
        )
    sources = list(
        await session.scalars(
            select(IntegrationSource.id).where(IntegrationSource.push_enabled.is_(True))
        )
    )
    if not sources:
        return
    statement = insert(IntegrationOutbox).values(
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
    await session.execute(
        statement.on_conflict_do_update(
            index_elements=["source_id", "interaction_id"],
            index_where=text("status = 'pending'"),
            set_={
                "change_seq": IntegrationOutbox.change_seq + 1,
                "reason": statement.excluded.reason,
            },
        )
    )


def receiver_for(source: IntegrationSource) -> InteractionReceiver:
    if source.kind == "lms":
        return MoodleLmsClient(source.base_url)
    return HttpSiteClient(source.base_url)


@dataclass(frozen=True, slots=True)
class _Claim:
    id: uuid.UUID
    interaction_id: uuid.UUID
    change_seq: int
    attempts: int


async def _claim(session: AsyncSession, source_id: uuid.UUID, now: datetime) -> list[_Claim]:
    due = (
        select(IntegrationOutbox.id)
        .where(
            IntegrationOutbox.source_id == source_id,
            IntegrationOutbox.status == "pending",
            IntegrationOutbox.next_attempt_at <= now,
            or_(IntegrationOutbox.locked_until.is_(None), IntegrationOutbox.locked_until < now),
        )
        .order_by(IntegrationOutbox.created_at)
        .limit(PUSH_BATCH)
        .with_for_update(skip_locked=True)
    )
    rows = await session.execute(
        update(IntegrationOutbox)
        .where(IntegrationOutbox.id.in_(due.scalar_subquery()))
        .values(locked_until=now + LEASE)
        .returning(
            IntegrationOutbox.id,
            IntegrationOutbox.interaction_id,
            IntegrationOutbox.change_seq,
            IntegrationOutbox.attempts,
        )
    )
    return [_Claim(*row) for row in rows.tuples()]


async def _settle(session: AsyncSession, claim: _Claim, values: dict[str, Any]) -> bool:
    """Итог отправки — только если запись не менялась после захвата. Иначе захват просто снят."""
    settled = await session.scalar(
        update(IntegrationOutbox)
        .where(IntegrationOutbox.id == claim.id, IntegrationOutbox.change_seq == claim.change_seq)
        .values(locked_until=None, **values)
        .returning(IntegrationOutbox.id)
    )
    if settled is not None:
        return True
    await session.execute(
        update(IntegrationOutbox).where(IntegrationOutbox.id == claim.id).values(locked_until=None)
    )
    return False


async def _retry(session: AsyncSession, claim: _Claim, error: str, now: datetime) -> str:
    attempts = claim.attempts + 1
    give_up = attempts >= MAX_PUSH_ATTEMPTS
    pause = BACKOFF_MINUTES[min(attempts, len(BACKOFF_MINUTES)) - 1]
    await session.execute(
        update(IntegrationOutbox)
        .where(IntegrationOutbox.id == claim.id)
        .values(
            attempts=attempts,
            last_error=error[:300],
            locked_until=None,
            next_attempt_at=now + timedelta(minutes=pause),
            status="failed" if give_up else "pending",
        )
    )
    return "failed" if give_up else "retried"


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
    claims = await _claim(session, source.id, now)
    # Захват фиксируется до сети: иначе строки очереди были бы заблокированы на время вызова.
    await session.commit()

    counter: Counter[str] = Counter()
    if claims:
        documents = await build_documents(session, [claim.interaction_id for claim in claims], now)
        client = client or receiver_for(source)
        try:
            result = await client.push_interactions(
                [document.model_dump(mode="json") for document in documents]
            )
        except SourceUnavailableError as error:
            for claim in claims:
                counter[await _retry(session, claim, str(error), now)] += 1
            run.status = "failed"
            run.error_code = ErrorCode.INTEGRATION_UNAVAILABLE.value
        else:
            for claim in claims:
                key = str(claim.interaction_id)
                if key in result.accepted:
                    sent = {"status": "sent", "sent_at": now, "last_error": None}
                    counter["sent" if await _settle(session, claim, sent) else "changed"] += 1
                elif key in result.rejected:
                    # Отказ по содержанию повтором не лечится: разбирается человеком по журналу.
                    rejected = {"status": "failed", "last_error": result.rejected[key][:300]}
                    ok = await _settle(session, claim, rejected)
                    counter["rejected" if ok else "changed"] += 1
                else:
                    counter[
                        await _retry(session, claim, "Получатель не подтвердил приём", now)
                    ] += 1
    if run.status == "running":
        run.status = "done"
        source.last_push_at = now
    run.stats = {"sent": 0, **counter}
    run.finished_at = datetime.now(UTC)
    await session.flush()
    return run


async def push_all(session: AsyncSession, now: datetime | None = None) -> list[SyncRun]:
    """Отправляет очередь всем получателям: отказ одного не мешает остальным."""
    sources = list(
        await session.scalars(
            select(IntegrationSource).where(IntegrationSource.push_enabled.is_(True))
        )
    )
    runs: list[SyncRun] = []
    for source in sources:
        runs.append(await push_source(session, source, now=now))
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
