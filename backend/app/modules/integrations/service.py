"""Синхронизация с LMS и сайтом: метрики, заявки и журнал запусков.

Каждый источник синхронизируется отдельно: падение одного не мешает остальным, а его причина
остаётся в журнале запусков с кодом ошибки.
"""

import uuid
from collections import Counter, defaultdict
from datetime import UTC, date, datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.core import cache
from app.core.config import Settings, get_settings
from app.core.errors import AppError, ErrorCode
from app.core.roles import Role
from app.core.scope import apply_interaction_scope, visible_interaction
from app.core.security import CurrentUser
from app.modules.catalogs.models import AppUser, Program, ProgramProduct, Team, University
from app.modules.imports.mapping import normalize
from app.modules.integrations.clients import (
    ApplicationRecord,
    CourseMetrics,
    HttpSiteClient,
    LmsClient,
    MoodleLmsClient,
    SiteClient,
    SourceUnavailableError,
    source_token,
)
from app.modules.integrations.models import IntegrationSource, SiteApplication, SyncRun
from app.modules.integrations.outbox import mark_changed
from app.modules.interactions.models import Interaction, Transition
from app.modules.metrics.models import ProgramMetric
from app.modules.radar.service import recompute_signals
from app.modules.workflow.defaults import universities_group
from app.modules.workflow.service import GroupProcess, group_process

LMS_NAME = "LMS ИТ Школы"
SITE_NAME = "Сайт ИТ Школы"
HOURLY_CRON = "0 * * * *"
SOURCE_NOT_FOUND = "Источник не найден."


async def ensure_sources(
    session: AsyncSession, settings: Settings | None = None
) -> list[IntegrationSource]:
    """Заводит источники LMS и сайта, если их ещё нет. Идемпотентна."""
    settings = settings or get_settings()
    wanted = (
        (LMS_NAME, "lms", settings.lms_base_url, "LMS_TOKEN"),
        (SITE_NAME, "site", settings.site_base_url, "SITE_TOKEN"),
    )
    existing = {source.name: source for source in await session.scalars(select(IntegrationSource))}
    for name, kind, base_url, secret_ref in wanted:
        if name in existing:
            continue
        source = IntegrationSource(
            kind=kind,
            name=name,
            base_url=base_url,
            secret_ref=secret_ref,
            is_mock=True,
            schedule_cron=HOURLY_CRON,
        )
        session.add(source)
        existing[name] = source
    await session.flush()
    return list(existing.values())


async def list_sources(session: AsyncSession) -> list[IntegrationSource]:
    sources = await session.scalars(select(IntegrationSource).order_by(IntegrationSource.name))
    return list(sources)


async def get_source(session: AsyncSession, source_id: uuid.UUID) -> IntegrationSource:
    source = await session.get(IntegrationSource, source_id)
    if source is None:
        raise AppError(ErrorCode.NOT_FOUND, SOURCE_NOT_FOUND)
    return source


async def list_runs(session: AsyncSession, source_id: uuid.UUID) -> list[SyncRun]:
    await get_source(session, source_id)
    runs = await session.scalars(
        select(SyncRun)
        .where(SyncRun.source_id == source_id)
        .order_by(SyncRun.started_at.desc())
        .limit(50)
    )
    return list(runs)


def _client_for(source: IntegrationSource) -> LmsClient | SiteClient:
    token = source_token(source.secret_ref)
    if source.kind == "lms":
        return MoodleLmsClient(source.base_url, token)
    return HttpSiteClient(source.base_url, token)


async def _catalog_ids(session: AsyncSession) -> tuple[dict[str, University], dict[str, Program]]:
    universities: dict[str, University] = {}
    for university in await session.scalars(select(University)):
        universities[normalize(university.name)] = university
        universities.setdefault(normalize(university.short_name), university)
    programs = {
        normalize(program.name): program for program in await session.scalars(select(Program))
    }
    return universities, programs


async def _save_metrics(
    session: AsyncSession, source: IntegrationSource, metrics: list[CourseMetrics]
) -> Counter[str]:
    """Обновляет метрики по ключу «вуз, программа, месяц, метрика, источник»."""
    universities, programs = await _catalog_ids(session)
    stored = {
        (metric.university_id, metric.program_id, metric.period_month, metric.metric): metric
        for metric in await session.scalars(
            select(ProgramMetric).where(ProgramMetric.source == source.kind)
        )
    }
    counter: Counter[str] = Counter()
    for item in metrics:
        university = universities.get(normalize(item.university_name))
        program = programs.get(normalize(item.program_name))
        if university is None or program is None:
            counter["skipped"] += 1
            continue
        for metric_kind, value in (("students", item.students), ("streams", item.streams)):
            key = (university.id, program.id, item.period_month, metric_kind)
            existing = stored.get(key)
            if existing is None:
                session.add(
                    ProgramMetric(
                        university_id=university.id,
                        program_id=program.id,
                        period_month=item.period_month,
                        metric=metric_kind,
                        value=value,
                        source=source.kind,
                    )
                )
                counter["created"] += 1
            else:
                existing.value = value
                counter["updated"] += 1
    await session.flush()
    return counter


async def _owner_for(
    session: AsyncSession, university_id: uuid.UUID, group_id: uuid.UUID
) -> AppUser | None:
    """КАМ, который последним работал с этим вузом; если такого нет — руководитель команды,
    которая больше всех ведёт записи этой группы. Иначе заявку разберёт человек.

    Раньше при отсутствии КАМа бралась первая попавшаяся строка — это мог оказаться
    руководитель частных лиц, а порядок без ORDER BY менялся от запроса к запросу.
    """
    owner: AppUser | None = await session.scalar(
        select(AppUser)
        .join(Interaction, Interaction.owner_user_id == AppUser.id)
        .where(Interaction.university_id == university_id, AppUser.is_active.is_(True))
        .order_by(Interaction.updated_at.desc(), AppUser.id)
        .limit(1)
    )
    if owner is not None:
        return owner
    member = aliased(AppUser)
    manager: AppUser | None = await session.scalar(
        select(AppUser)
        .join(Team, Team.manager_user_id == AppUser.id)
        .join(member, member.team_id == Team.id)
        .join(Interaction, Interaction.owner_user_id == member.id)
        .where(
            Interaction.group_id == group_id,
            AppUser.role == Role.MANAGER.value,
            AppUser.is_active.is_(True),
        )
        .group_by(AppUser.id)
        .order_by(func.count(Interaction.id).desc(), AppUser.id)
        .limit(1)
    )
    return manager


async def _match_application(
    session: AsyncSession,
    record: ApplicationRecord,
    universities: dict[str, University],
    programs: dict[str, Program],
    group_id: uuid.UUID,
    process: GroupProcess,
) -> tuple[SiteApplication, uuid.UUID | None]:
    """Привязывает заявку к взаимодействию, создавая его при необходимости."""
    application = await session.scalar(
        select(SiteApplication).where(SiteApplication.external_id == record.external_id)
    )
    if application is None:
        application = SiteApplication(
            external_id=record.external_id,
            university_name=record.university_name,
            program_name=record.program_name,
            contact_name=record.contact_name,
            comment=record.comment,
            received_at=record.received_at,
            match_status="unmatched",
        )
        session.add(application)
    if application.match_status == "matched":
        return application, None

    university = universities.get(normalize(record.university_name))
    program = programs.get(normalize(record.program_name))
    if university is None or program is None:
        # Названия из формы сайта не нашлись в справочниках: заявку разберёт человек.
        return application, None

    application.university_id = university.id
    application.program_id = program.id
    links = (
        (
            await session.execute(
                select(ProgramProduct.product_id, ProgramProduct.is_default).where(
                    ProgramProduct.program_id == program.id
                )
            )
        )
        .tuples()
        .all()
    )
    # Продукт программы: основная пара, а если продукт у программы один — он.
    product_id = next((linked for linked, is_default in links if is_default), None)
    if product_id is None and len(links) == 1:
        product_id = links[0][0]
    if links and product_id is None:
        # У программы несколько продуктов и основной не выбран: решит человек.
        return application, None

    interaction = await session.scalar(
        select(Interaction).where(
            Interaction.university_id == university.id,
            Interaction.program_id == program.id,
            Interaction.product_id.is_not_distinct_from(product_id),
            Interaction.status != "cancelled",
        )
    )
    created_id: uuid.UUID | None = None
    if interaction is None:
        interaction = await _interaction_from_application(
            session, record, university.id, program.id, product_id, group_id, process
        )
        if interaction is None:
            # Некому вести вуз: заявка остаётся в очереди, а не висит без ответственного.
            return application, None
        created_id = interaction.id

    application.interaction_id = interaction.id
    application.match_status = "matched"
    return application, created_id


async def _interaction_from_application(
    session: AsyncSession,
    record: ApplicationRecord,
    university_id: uuid.UUID,
    program_id: uuid.UUID,
    product_id: uuid.UUID | None,
    group_id: uuid.UUID,
    process: GroupProcess,
) -> Interaction | None:
    """Заводит взаимодействие по заявке. Даты берутся из заявки: она и есть начало работы."""
    owner = await _owner_for(session, university_id, group_id)
    if owner is None:
        return None

    stage = process.start
    version_id = process.version.id
    interaction = Interaction(
        group_id=group_id,
        university_id=university_id,
        program_id=program_id,
        product_id=product_id,
        workflow_version_id=version_id,
        current_stage_id=stage.id,
        stage_entered_at=record.received_at,
        owner_user_id=owner.id,
        source="site",
        last_activity_at=record.received_at,
        created_at=record.received_at,
    )
    session.add(interaction)
    await session.flush()
    session.add(
        Transition(
            interaction_id=interaction.id,
            from_stage_id=None,
            to_stage_id=stage.id,
            occurred_at=record.received_at,
            actor_user_id=owner.id,
            comment="Заявка с сайта",
            source="integration",
        )
    )
    return interaction


async def _save_applications(
    session: AsyncSession,
    source: IntegrationSource,
    records: list[ApplicationRecord],
    now: datetime,
) -> Counter[str]:
    universities, programs = await _catalog_ids(session)
    # Заявки с сайта — от вузов, поэтому записи заводятся в группе вузов по её процессу.
    group = await universities_group(session)
    process = await group_process(session, group)
    counter: Counter[str] = Counter()
    created: list[uuid.UUID] = []
    matched: list[uuid.UUID] = []
    monthly: dict[tuple[uuid.UUID, uuid.UUID, date], int] = defaultdict(int)

    for record in records:
        was_matched = await session.scalar(
            select(SiteApplication.interaction_id).where(
                SiteApplication.external_id == record.external_id,
                SiteApplication.match_status == "matched",
            )
        )
        application, created_id = await _match_application(
            session, record, universities, programs, group.id, process
        )
        counter[application.match_status] += 1
        if created_id is not None:
            created.append(created_id)
        if was_matched is None and application.interaction_id is not None:
            # Сайт узнаёт, в какую запись CRM попала его заявка.
            matched.append(application.interaction_id)
        if application.university_id and application.program_id:
            month = record.received_at.date().replace(day=1)
            monthly[(application.university_id, application.program_id, month)] += 1
    await session.flush()

    stored = {
        (metric.university_id, metric.program_id, metric.period_month): metric
        for metric in await session.scalars(
            select(ProgramMetric).where(
                ProgramMetric.source == source.kind, ProgramMetric.metric == "applications"
            )
        )
    }
    for (university_id, program_id, month), value in monthly.items():
        existing = stored.get((university_id, program_id, month))
        if existing is None:
            session.add(
                ProgramMetric(
                    university_id=university_id,
                    program_id=program_id,
                    period_month=month,
                    metric="applications",
                    value=value,
                    source=source.kind,
                )
            )
        else:
            existing.value = value
    await session.flush()
    if created:
        await recompute_signals(session, created, now)
    await mark_changed(session, matched, "site_application")
    counter["interactions_created"] = len(created)
    return counter


async def sync_source(
    session: AsyncSession,
    source: IntegrationSource,
    client: LmsClient | SiteClient | None = None,
    now: datetime | None = None,
) -> SyncRun:
    """Одна синхронизация: запись в журнале появляется даже при отказе источника."""
    now = now or datetime.now(UTC)
    run = SyncRun(source_id=source.id, started_at=now, status="running", stats={})
    session.add(run)
    await session.flush()

    client = client or _client_for(source)
    try:
        if isinstance(client, LmsClient):
            stats = await _save_metrics(session, source, await client.fetch_metrics())
        else:
            stats = await _save_applications(
                session, source, await client.fetch_applications(), now
            )
    except SourceUnavailableError:
        run.status = "failed"
        run.error_code = ErrorCode.INTEGRATION_UNAVAILABLE.value
    else:
        run.status = "done"
        run.stats = dict(stats)
        source.last_sync_at = now
    run.finished_at = datetime.now(UTC)
    await session.flush()
    return run


async def sync_all(session: AsyncSession, now: datetime | None = None) -> list[SyncRun]:
    """Синхронизирует все включённые источники: отказ одного не мешает остальным."""
    runs = [
        await sync_source(session, source, now=now)
        for source in await list_sources(session)
        if source.pull_enabled
    ]
    await session.commit()
    # Витрина метрик обновилась: сбрасываем кэш рейтинга уже после фиксации, иначе параллельный
    # запрос успел бы посчитать рейтинг по старым данным и положить его в новое поколение.
    await cache.invalidate(cache.RATING)
    return runs


def _visible_applications(user: CurrentUser) -> Select[tuple[SiteApplication]]:
    """Очередь несопоставленных видна всем руководителям — её кто-то должен разобрать.
    Сопоставленная заявка с ФИО заявителя видна тем, кто видит её взаимодействие.
    """
    visible_interactions = apply_interaction_scope(select(Interaction.id), user)
    return select(SiteApplication).where(
        or_(
            SiteApplication.match_status == "unmatched",
            SiteApplication.interaction_id.in_(visible_interactions),
        )
    )


async def list_applications(
    session: AsyncSession, user: CurrentUser, match_status: str | None = None
) -> list[SiteApplication]:
    stmt = _visible_applications(user).order_by(SiteApplication.received_at.desc()).limit(200)
    if match_status:
        stmt = stmt.where(SiteApplication.match_status == match_status)
    return list(await session.scalars(stmt))


async def match_application(
    session: AsyncSession, user: CurrentUser, application_id: uuid.UUID, interaction_id: uuid.UUID
) -> SiteApplication:
    """Ручное сопоставление: и заявка, и взаимодействие должны быть доступны тому, кто
    сопоставляет. Уже сопоставленную заявку перепривязать может только тот, кто видит её
    нынешнее взаимодействие, — иначе чужую заявку можно было бы увести к себе.
    """
    application = await session.scalar(
        _visible_applications(user).where(SiteApplication.id == application_id)
    )
    if application is None:
        raise AppError(ErrorCode.NOT_FOUND, "Заявка не найдена.")
    interaction = await visible_interaction(session, user, interaction_id)

    application.interaction_id = interaction.id
    application.university_id = interaction.university_id
    application.program_id = interaction.program_id
    application.match_status = "matched"
    await mark_changed(session, [interaction.id], "site_application")
    await session.commit()
    return application
