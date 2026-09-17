"""Администрирование: сотрудники, команды, правила доступа, настройки, аудит и каталоги."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from pydantic import BaseModel, ValidationError
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.core.errors import AppError, ErrorCode, FieldError
from app.core.security import CurrentUser
from app.modules.admin.models import AppSetting, DataAccessRule
from app.modules.admin.schemas import (
    AccessRuleCreate,
    AdminUserUpdate,
    CatalogItemCreate,
    ContactCreate,
    ContactOut,
    SettingOut,
)
from app.modules.audit.models import AuditLog
from app.modules.catalogs.models import (
    AppUser,
    ContactPerson,
    Direction,
    Product,
    Program,
    Team,
    University,
    Vendor,
)
from app.modules.interactions.models import Interaction
from app.modules.radar.service import recompute_signals
from app.modules.radar.settings import RADAR_THRESHOLDS_KEY, RadarThresholdsSetting

CATALOGS: dict[str, type[University | Direction | Program | Vendor | Product]] = {
    "universities": University,
    "directions": Direction,
    "programs": Program,
    "vendors": Vendor,
    "products": Product,
}


def _audit(
    user: CurrentUser,
    action: str,
    entity_kind: str,
    entity_id: uuid.UUID | None,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> AuditLog:
    return AuditLog(
        actor_user_id=user.id,
        action=action,
        entity_kind=entity_kind,
        entity_id=entity_id,
        before=before,
        after=after,
        trace_id=trace_id,
    )


async def list_users(session: AsyncSession) -> list[AppUser]:
    users = await session.scalars(select(AppUser).order_by(AppUser.full_name))
    return list(users)


async def update_user(
    session: AsyncSession,
    admin: CurrentUser,
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    trace_id: str | None = None,
) -> AppUser:
    user = await session.get(AppUser, user_id)
    if user is None:
        raise AppError(ErrorCode.NOT_FOUND, "Сотрудник не найден.")
    before = {
        "role": user.role,
        "team_id": str(user.team_id) if user.team_id else None,
        "is_active": user.is_active,
    }
    if payload.role is not None:
        user.role = payload.role.value
    if payload.team_id is not None:
        if await session.get(Team, payload.team_id) is None:
            raise AppError(
                ErrorCode.VALIDATION_ERROR,
                "Команда не найдена.",
                errors=[FieldError(field="team_id", message="Неизвестная команда")],
            )
        user.team_id = payload.team_id
    if payload.is_active is not None:
        user.is_active = payload.is_active
    session.add(
        _audit(
            admin,
            "admin.user_changed",
            "app_user",
            user.id,
            before,
            {
                "role": user.role,
                "team_id": str(user.team_id) if user.team_id else None,
                "is_active": user.is_active,
            },
            trace_id,
        )
    )
    await session.commit()
    return user


async def list_teams(session: AsyncSession) -> list[Team]:
    teams = await session.scalars(select(Team).order_by(Team.name))
    return list(teams)


async def create_team(
    session: AsyncSession,
    admin: CurrentUser,
    name: str,
    manager_user_id: uuid.UUID | None,
    trace_id: str | None = None,
) -> Team:
    if await session.scalar(select(Team).where(Team.name == name)):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Команда с таким названием уже есть.",
            errors=[FieldError(field="name", message="Название занято")],
        )
    team = Team(name=name, manager_user_id=manager_user_id)
    session.add(team)
    await session.flush()
    session.add(
        _audit(
            admin, "admin.team_created", "team", team.id, after={"name": name}, trace_id=trace_id
        )
    )
    await session.commit()
    return team


async def list_rules(session: AsyncSession) -> list[DataAccessRule]:
    rules = await session.scalars(select(DataAccessRule).order_by(DataAccessRule.created_at.desc()))
    return list(rules)


async def create_rule(
    session: AsyncSession,
    admin: CurrentUser,
    payload: AccessRuleCreate,
    trace_id: str | None = None,
) -> DataAccessRule:
    if (payload.subject_user_id is None) == (payload.subject_role is None):
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Правило адресуется либо сотруднику, либо роли.",
            errors=[FieldError(field="subject_user_id", message="Укажите одно из двух")],
        )
    rule = DataAccessRule(
        subject_user_id=payload.subject_user_id,
        subject_role=payload.subject_role.value if payload.subject_role else None,
        effect=payload.effect,
        scope_kind=payload.scope_kind,
        scope_id=payload.scope_id,
        comment=payload.comment,
    )
    session.add(rule)
    await session.flush()
    session.add(
        _audit(
            admin,
            "admin.access_rule_created",
            "data_access_rule",
            rule.id,
            after={
                "effect": rule.effect,
                "scope_kind": rule.scope_kind,
                "scope_id": str(rule.scope_id),
            },
            trace_id=trace_id,
        )
    )
    await session.commit()
    return rule


async def delete_rule(
    session: AsyncSession, admin: CurrentUser, rule_id: uuid.UUID, trace_id: str | None = None
) -> None:
    rule = await session.get(DataAccessRule, rule_id)
    if rule is None:
        raise AppError(ErrorCode.NOT_FOUND, "Правило не найдено.")
    before = {"effect": rule.effect, "scope_kind": rule.scope_kind, "scope_id": str(rule.scope_id)}
    await session.delete(rule)
    session.add(
        _audit(
            admin,
            "admin.access_rule_deleted",
            "data_access_rule",
            rule_id,
            before,
            trace_id=trace_id,
        )
    )
    await session.commit()


@dataclass(frozen=True, slots=True)
class KnownSetting:
    schema: type[BaseModel]
    description: str


# Только эти настройки что-то меняют в системе. Неизвестный ключ — опечатка, а не новая настройка.
KNOWN_SETTINGS: dict[str, KnownSetting] = {
    RADAR_THRESHOLDS_KEY: KnownSetting(
        RadarThresholdsSetting, "Пороги радара в днях: срок лицензии и простой записи"
    ),
}


def _setting_out(key: str, stored: AppSetting | None) -> SettingOut:
    known = KNOWN_SETTINGS[key]
    value = stored.value if stored else known.schema().model_dump(mode="json")
    return SettingOut(
        key=key,
        description=known.description,
        value=value,
        is_default=stored is None,
        updated_at=stored.updated_at if stored else None,
    )


async def list_settings(session: AsyncSession) -> list[SettingOut]:
    stored = {setting.key: setting for setting in await session.scalars(select(AppSetting))}
    return [_setting_out(key, stored.get(key)) for key in sorted(KNOWN_SETTINGS)]


def _validated(key: str, value: dict[str, Any]) -> dict[str, Any]:
    known = KNOWN_SETTINGS.get(key)
    if known is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Неизвестная настройка: {key}.")
    try:
        return known.schema.model_validate(value).model_dump(mode="json")
    except ValidationError as error:
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Значение настройки не прошло проверку.",
            errors=[
                FieldError(
                    field=".".join(["value", *(str(part) for part in item["loc"])]),
                    message=item["msg"],
                )
                for item in error.errors()
            ],
        ) from error


async def set_setting(
    session: AsyncSession,
    admin: CurrentUser,
    key: str,
    value: dict[str, Any],
    trace_id: str | None = None,
) -> SettingOut:
    value = _validated(key, value)
    setting = await session.get(AppSetting, key)
    before = dict(setting.value) if setting else None
    if setting is None:
        setting = AppSetting(key=key, value=value, updated_by=admin.id)
        session.add(setting)
    else:
        setting.value = value
        setting.updated_by = admin.id
    session.add(
        _audit(admin, "admin.setting_changed", "app_setting", None, before, value, trace_id)
    )
    await session.flush()
    if key == RADAR_THRESHOLDS_KEY:
        # Новые пороги видны сразу, а не после ночного пересчёта.
        active = await session.scalars(select(Interaction.id).where(Interaction.status == "active"))
        await recompute_signals(session, list(active))
    await session.commit()
    await session.refresh(setting)
    return _setting_out(key, setting)


async def list_audit(
    session: AsyncSession,
    action: str | None = None,
    entity_kind: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    stmt: Select[Any] = select(AuditLog).order_by(AuditLog.occurred_at.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_kind:
        stmt = stmt.where(AuditLog.entity_kind == entity_kind)
    return list(await session.scalars(stmt))


def _contact_out(contact: ContactPerson) -> ContactOut:
    return ContactOut(
        id=contact.id,
        university_id=contact.university_id,
        full_name=contact.full_name,
        position=contact.position,
        email=crypto.decrypt(contact.email_enc),
        phone=crypto.decrypt(contact.phone_enc),
        archived_at=contact.archived_at,
    )


async def list_contacts(
    session: AsyncSession, user: CurrentUser, university_id: uuid.UUID, trace_id: str | None = None
) -> list[ContactOut]:
    """Просмотр контактов — обращение к персональным данным, поэтому пишется в аудит."""
    contacts = list(
        await session.scalars(
            select(ContactPerson)
            .where(ContactPerson.university_id == university_id)
            .order_by(ContactPerson.full_name)
        )
    )
    session.add(
        _audit(
            user,
            "contact.viewed",
            "university",
            university_id,
            after={"contacts": len(contacts)},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return [_contact_out(contact) for contact in contacts]


async def create_contact(
    session: AsyncSession,
    user: CurrentUser,
    university_id: uuid.UUID,
    payload: ContactCreate,
    trace_id: str | None = None,
) -> ContactOut:
    if await session.get(University, university_id) is None:
        raise AppError(ErrorCode.NOT_FOUND, "Вуз не найден.")
    if (payload.email or payload.phone) and not crypto.is_configured():
        raise AppError(
            ErrorCode.VALIDATION_ERROR,
            "Не настроен ключ шифрования: контакт с персональными данными сохранить нельзя.",
            errors=[FieldError(field="email", message="Шифрование не настроено")],
        )
    contact = ContactPerson(
        university_id=university_id,
        full_name=payload.full_name,
        position=payload.position,
        email_enc=crypto.encrypt(payload.email),
        phone_enc=crypto.encrypt(payload.phone),
    )
    session.add(contact)
    await session.flush()
    # В журнал идёт факт появления контакта, но не сами персональные данные.
    session.add(
        _audit(
            user,
            "contact.created",
            "contact_person",
            contact.id,
            after={"university_id": str(university_id), "has_email": payload.email is not None},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return _contact_out(contact)


async def archive_contact(
    session: AsyncSession, user: CurrentUser, contact_id: uuid.UUID, trace_id: str | None = None
) -> ContactOut:
    contact = await session.get(ContactPerson, contact_id)
    if contact is None:
        raise AppError(ErrorCode.NOT_FOUND, "Контакт не найден.")
    contact.archived_at = datetime.now(UTC)
    session.add(_audit(user, "contact.archived", "contact_person", contact.id, trace_id=trace_id))
    await session.commit()
    return _contact_out(contact)


def _catalog_model(kind: str) -> type[University | Direction | Program | Vendor | Product]:
    model = CATALOGS.get(kind)
    if model is None:
        raise AppError(ErrorCode.NOT_FOUND, f"Неизвестный каталог: {kind}.")
    return model


async def create_catalog_item(
    session: AsyncSession,
    admin: CurrentUser,
    kind: str,
    payload: CatalogItemCreate,
    trace_id: str | None = None,
) -> University | Direction | Program | Vendor | Product:
    model = _catalog_model(kind)
    item: University | Direction | Program | Vendor | Product
    match kind:
        case "universities":
            item = University(
                name=payload.name,
                short_name=payload.short_name or payload.name[:60],
                region=payload.region or "Не указан",
                city=payload.city,
            )
        case "directions":
            if not payload.code:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    "У направления должен быть код.",
                    errors=[FieldError(field="code", message="Обязательное поле")],
                )
            item = Direction(code=payload.code, name=payload.name)
        case "programs":
            if payload.direction_id is None:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    "У программы должно быть направление.",
                    errors=[FieldError(field="direction_id", message="Обязательное поле")],
                )
            item = Program(direction_id=payload.direction_id, name=payload.name)
        case "vendors":
            item = Vendor(name=payload.name)
        case _:
            if payload.vendor_id is None:
                raise AppError(
                    ErrorCode.VALIDATION_ERROR,
                    "У продукта должен быть вендор.",
                    errors=[FieldError(field="vendor_id", message="Обязательное поле")],
                )
            item = Product(vendor_id=payload.vendor_id, name=payload.name)

    session.add(item)
    await session.flush()
    session.add(
        _audit(
            admin,
            "admin.catalog_created",
            model.__tablename__,
            item.id,
            after={"name": payload.name},
            trace_id=trace_id,
        )
    )
    await session.commit()
    return item


async def archive_catalog_item(
    session: AsyncSession,
    admin: CurrentUser,
    kind: str,
    item_id: uuid.UUID,
    trace_id: str | None = None,
) -> University | Direction | Program | Vendor | Product:
    """Каталоги не удаляются: на них ссылаются взаимодействия и история."""
    model = _catalog_model(kind)
    # Модель выбирается по строке, поэтому тип записи уточняем сами: иначе это просто Base.
    item = cast(
        "University | Direction | Program | Vendor | Product | None",
        await session.get(model, item_id),
    )
    if item is None:
        raise AppError(ErrorCode.NOT_FOUND, "Запись каталога не найдена.")
    item.archived_at = datetime.now(UTC)
    session.add(
        _audit(admin, "admin.catalog_archived", model.__tablename__, item.id, trace_id=trace_id)
    )
    await session.commit()
    return item
