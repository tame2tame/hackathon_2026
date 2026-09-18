"""Эскалация зависших записей: запись без изменений дольше срока — уведомление вышестоящей роли.

Срок и роль — настройка `stalled_escalation`. Руководитель узнаёт о записи своей команды; если
у команды нет руководителя или запись ведёт он сам, уведомление уходит администраторам.
"""

import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.roles import Role
from app.core.scope import apply_interaction_scope
from app.core.security import current_user_for
from app.modules.catalogs.models import AppUser, Team
from app.modules.interactions.models import Interaction
from app.modules.notifications.service import notify
from app.modules.notifications.settings import load_escalation
from app.modules.radar.messages import plural_days


async def _people(
    session: AsyncSession,
) -> tuple[dict[uuid.UUID, set[uuid.UUID]], set[uuid.UUID], dict[uuid.UUID, AppUser]]:
    """Руководители каждой команды и администраторы — только действующие."""
    managers: dict[uuid.UUID, set[uuid.UUID]] = defaultdict(set)
    admins: set[uuid.UUID] = set()
    people: dict[uuid.UUID, AppUser] = {}
    for user in await session.scalars(select(AppUser).where(AppUser.is_active.is_(True))):
        people[user.id] = user
        if user.role == Role.ADMIN.value:
            admins.add(user.id)
        elif user.role == Role.MANAGER.value and user.team_id is not None:
            managers[user.team_id].add(user.id)
    active = {user_id for team in managers.values() for user_id in team} | admins
    for team in await session.scalars(select(Team).where(Team.manager_user_id.is_not(None))):
        head = team.manager_user_id
        if head is not None:
            is_active = await session.scalar(select(AppUser.is_active).where(AppUser.id == head))
            if is_active:
                managers[team.id].add(head)
                active.add(head)
    return managers, admins, people


def recipients_for(
    role: str,
    owner: AppUser,
    managers: dict[uuid.UUID, set[uuid.UUID]],
    admins: set[uuid.UUID],
) -> list[uuid.UUID]:
    chosen: set[uuid.UUID] = set()
    if role == Role.MANAGER.value and owner.team_id is not None:
        chosen = managers.get(owner.team_id, set()) - {owner.id}
    if not chosen:
        chosen = admins - {owner.id}
    return sorted(chosen)


async def _visible_per_person(
    session: AsyncSession, people: dict[uuid.UUID, AppUser], interaction_ids: list[uuid.UUID]
) -> dict[uuid.UUID, set[uuid.UUID]]:
    visible: dict[uuid.UUID, set[uuid.UUID]] = {}
    for user_id, person in people.items():
        rows = await session.scalars(
            apply_interaction_scope(
                select(Interaction.id).where(Interaction.id.in_(interaction_ids)),
                await current_user_for(session, person),
            )
        )
        visible[user_id] = set(rows)
    return visible


async def escalate_stalled(session: AsyncSession, now: datetime | None = None) -> int:
    """Создаёт уведомления о записях без изменений. Возвращает число новых уведомлений."""
    now = now or datetime.now(UTC)
    setting = await load_escalation(session)
    if not setting.enabled:
        return 0
    stalled = (
        (
            await session.execute(
                select(Interaction, AppUser)
                .join(AppUser, AppUser.id == Interaction.owner_user_id)
                .where(
                    Interaction.status == "active",
                    Interaction.last_activity_at <= now - timedelta(days=setting.days),
                )
                .options(
                    joinedload(Interaction.university),
                    joinedload(Interaction.client),
                    joinedload(Interaction.program),
                    joinedload(Interaction.current_stage),
                )
                .order_by(Interaction.last_activity_at)
            )
        )
        .unique()
        .tuples()
        .all()
    )
    if not stalled:
        return 0
    managers, admins, people = await _people(session)
    # Получатель не должен узнать о записи, которой он не видит: правила доступа сильнее роли.
    visible = await _visible_per_person(session, people, [record.id for record, _ in stalled])

    created = 0
    for interaction, owner in stalled:
        days = (now - interaction.last_activity_at).days
        label = f"{interaction.counterparty.short_name} — {interaction.program.name}"
        stamp = interaction.last_activity_at.strftime("%Y%m%dT%H%M%S")
        recipients = [
            user_id
            for user_id in recipients_for(setting.notify_role, owner, managers, admins)
            if interaction.id in visible.get(user_id, set())
        ]
        if not recipients:
            # Руководителю запись закрыта правилом доступа: сообщаем тем, кто её видит.
            recipients = [
                user_id
                for user_id in sorted(admins - {owner.id})
                if interaction.id in visible.get(user_id, set())
            ]
        created += len(
            await notify(
                session,
                recipients,
                "stalled_interaction",
                f"Запись без изменений {days} {plural_days(days)}",
                f"«{label}» стоит на этапе «{interaction.current_stage.name}», "
                f"ответственный — {owner.full_name}. Задача долго стоит — уточните причину.",
                interaction_id=interaction.id,
                payload={
                    "days": days,
                    "threshold_days": setting.days,
                    "owner_user_id": str(owner.id),
                    "stage_code": interaction.current_stage.code,
                },
                # Один эпизод простоя — одно уведомление; новая активность начинает новый эпизод.
                dedupe_key=f"stalled:{interaction.id}:{stamp}",
            )
        )
    await session.commit()
    return created
