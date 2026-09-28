import uuid
from datetime import datetime
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.admin import catalog_io, service
from app.modules.admin.schemas import (
    AccessRuleCreate,
    AccessRuleOut,
    AdminUserOut,
    AdminUserUpdate,
    AuditEntryOut,
    CatalogImportOut,
    CatalogItemCreate,
    CatalogItemOut,
    CatalogRowOut,
    ContactCreate,
    ContactOut,
    CounterpartyGroupCreate,
    CounterpartyGroupUpdate,
    SettingOut,
    SettingUpdate,
    TeamCreate,
    TeamOut,
)
from app.modules.catalogs.schemas import CounterpartyGroupOut

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])
# Контакты вуза видят все, кому доступен вуз, поэтому они живут вне админского префикса.
contacts_router = APIRouter(prefix="/api/v1", tags=["catalogs"])

AdminDep = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]
ADMIN_ERRORS = (
    ErrorCode.AUTH_REQUIRED,
    ErrorCode.AUTH_FORBIDDEN,
    ErrorCode.NOT_FOUND,
    ErrorCode.VALIDATION_ERROR,
)


@router.get("/users", summary="Сотрудники", responses=error_responses(*ADMIN_ERRORS))
async def read_users(session: SessionDep, _admin: AdminDep) -> list[AdminUserOut]:
    return [AdminUserOut.model_validate(user) for user in await service.list_users(session)]


@router.patch(
    "/users/{user_id}",
    summary="Роль, команда и доступ сотрудника",
    responses=error_responses(*ADMIN_ERRORS),
)
async def patch_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
) -> AdminUserOut:
    user = await service.update_user(session, admin, user_id, payload, trace_id)
    return AdminUserOut.model_validate(user)


@router.get("/teams", summary="Команды", responses=error_responses(*ADMIN_ERRORS))
async def read_teams(session: SessionDep, _admin: AdminDep) -> list[TeamOut]:
    return [TeamOut.model_validate(team) for team in await service.list_teams(session)]


@router.post(
    "/teams",
    status_code=status.HTTP_201_CREATED,
    summary="Создать команду",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_team(
    payload: TeamCreate, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> TeamOut:
    team = await service.create_team(
        session, admin, payload.name, payload.manager_user_id, trace_id
    )
    return TeamOut.model_validate(team)


@router.get(
    "/access-rules",
    summary="Правила доступа к данным",
    description="Запрет сильнее разрешения; правила применяются поверх ролей во всех списках.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def read_rules(session: SessionDep, _admin: AdminDep) -> list[AccessRuleOut]:
    return [AccessRuleOut.model_validate(rule) for rule in await service.list_rules(session)]


@router.post(
    "/access-rules",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить правило доступа",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_rule(
    payload: AccessRuleCreate, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> AccessRuleOut:
    rule = await service.create_rule(session, admin, payload, trace_id)
    return AccessRuleOut.model_validate(rule)


@router.delete(
    "/access-rules/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Убрать правило доступа",
    responses=error_responses(*ADMIN_ERRORS),
)
async def delete_rule(
    rule_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> None:
    await service.delete_rule(session, admin, rule_id, trace_id)


@router.get("/settings", summary="Настройки приложения", responses=error_responses(*ADMIN_ERRORS))
async def read_settings(session: SessionDep, _admin: AdminDep) -> list[SettingOut]:
    return await service.list_settings(session)


@router.put(
    "/settings/{key}",
    summary="Изменить настройку",
    description=(
        "Значение проверяется схемой настройки; пропущенные поля получают значения по умолчанию. "
        "Неизвестный ключ — `NOT_FOUND`. Изменение пишется в аудит, новые пороги радара "
        "применяются сразу."
    ),
    responses=error_responses(*ADMIN_ERRORS),
)
async def put_setting(
    key: str, payload: SettingUpdate, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> SettingOut:
    return await service.set_setting(session, admin, key, payload.value, trace_id)


@router.get(
    "/audit",
    summary="Журнал аудита",
    description=(
        "Значения до и после изменения; просмотр персональных данных тоже записывается. "
        "Новые сверху, пачками: `limit` записей со сдвигом `offset`. Фильтры по действию, "
        "виду и id объекта, сотруднику и периоду `[occurred_from, occurred_to)`."
    ),
    responses=error_responses(*ADMIN_ERRORS),
)
async def read_audit(
    session: SessionDep,
    _admin: AdminDep,
    action: Annotated[str | None, Query(max_length=60)] = None,
    entity_kind: Annotated[str | None, Query(max_length=60)] = None,
    entity_id: Annotated[uuid.UUID | None, Query(description="Объект")] = None,
    actor_user_id: Annotated[uuid.UUID | None, Query(description="Кто сделал")] = None,
    occurred_from: Annotated[datetime | None, Query(description="Не раньше, ISO 8601")] = None,
    occurred_to: Annotated[datetime | None, Query(description="Раньше, ISO 8601")] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0, description="Сколько записей пропустить")] = 0,
) -> list[AuditEntryOut]:
    filters = service.AuditFilter(
        action=action,
        entity_kind=entity_kind,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        occurred_from=occurred_from,
        occurred_to=occurred_to,
    )
    return await service.list_audit(session, filters, limit, offset)


@router.post(
    "/catalogs/{kind}",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить запись каталога",
    description="Каталоги: universities, directions, programs, vendors, products.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_catalog_item(
    kind: str,
    payload: CatalogItemCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
) -> CatalogItemOut:
    item = await service.create_catalog_item(session, admin, kind, payload, trace_id)
    return CatalogItemOut(id=item.id, name=item.name, archived_at=item.archived_at)


@router.post(
    "/catalogs/{kind}/import",
    summary="Загрузить справочник файлом",
    description=(
        "JSON (массив объектов или `{items}`), CSV, XLSX или XLS. Справочники: "
        f"{', '.join(catalog_io.SPECS)}. Колонки называются как в выгрузке или по именам полей. "
        "Записи находятся по естественному ключу: повторная загрузка не создаёт дублей, пустая "
        "ячейка не стирает поле, архивная запись возвращается. По умолчанию — предпросмотр "
        "(`dry_run=true`): итог по каждой строке без изменений в базе."
    ),
    responses=error_responses(
        *ADMIN_ERRORS,
        ErrorCode.IMPORT_MAPPING_INVALID,
        ErrorCode.FILE_TOO_LARGE,
    ),
)
async def post_catalog_import(
    kind: str,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
    file: Annotated[UploadFile, File(description="Файл справочника")],
    dry_run: Annotated[bool, Form(description="Только показать, что будет")] = True,
    encoding: Annotated[
        Literal["utf-8", "windows-1251", "koi8-r", "cp866", "utf-16"] | None,
        Form(description="Кодировка CSV, если определилась неверно"),
    ] = None,
) -> CatalogImportOut:
    outcome = await catalog_io.import_catalog(
        session, admin, kind, file, dry_run, encoding, trace_id
    )
    return CatalogImportOut(
        kind=outcome.kind,
        dry_run=outcome.dry_run,
        created=outcome.count("created"),
        updated=outcome.count("updated"),
        unchanged=outcome.count("unchanged"),
        errors=outcome.count("error"),
        rows=[
            CatalogRowOut(row_no=row.row_no, key=row.key, action=row.action, detail=row.detail)
            for row in outcome.rows
        ],
    )


@router.get(
    "/catalogs/{kind}/export",
    summary="Выгрузить справочник файлом",
    description=(
        "Те же колонки, что принимает загрузка: выгрузил, поправил, загрузил обратно. "
        "CSV — через точку с запятой, UTF-8 с BOM или windows-1251."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/json": {}, "text/csv": {}, "application/octet-stream": {}},
            "description": "Файл справочника",
        },
        **error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN, ErrorCode.NOT_FOUND),
    },
)
async def read_catalog_export(
    kind: str,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
    file_format: Annotated[
        Literal["json", "csv", "xlsx"], Query(alias="format", description="Формат файла")
    ] = "xlsx",
    encoding: Annotated[
        Literal["utf-8", "windows-1251"], Query(description="Кодировка CSV")
    ] = "utf-8",
    include_archived: Annotated[bool, Query(description="Вместе с архивными записями")] = False,
) -> Response:
    content, media_type, file_name = await catalog_io.export_catalog(
        session, kind, file_format, encoding, include_archived, user, trace_id
    )
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"},
    )


@router.post(
    "/catalogs/{kind}/{item_id}/archive",
    summary="Архивировать запись каталога",
    description="Удаления нет: на записи ссылаются взаимодействия и история.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_catalog_archive(
    kind: str, item_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> CatalogItemOut:
    item = await service.archive_catalog_item(session, admin, kind, item_id, trace_id)
    return CatalogItemOut(id=item.id, name=item.name, archived_at=item.archived_at)


@router.post(
    "/counterparty-groups",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить группу контрагентов",
    description="Новая группа работает по уже опубликованному процессу.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_group(
    payload: CounterpartyGroupCreate, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> CounterpartyGroupOut:
    group = await service.create_group(session, admin, payload, trace_id)
    return CounterpartyGroupOut.model_validate(group)


@router.patch(
    "/counterparty-groups/{group_id}",
    summary="Изменить группу контрагентов",
    description=(
        "Название, описание, порядок и процесс. Процесс группы с открытыми записями не "
        "заменяется: его меняют в редакторе, и записи переходят на новую схему."
    ),
    responses=error_responses(*ADMIN_ERRORS),
)
async def patch_group(
    group_id: uuid.UUID,
    payload: CounterpartyGroupUpdate,
    trace_id: TraceIdDep,
    session: SessionDep,
    admin: AdminDep,
) -> CounterpartyGroupOut:
    group = await service.update_group(session, admin, group_id, payload, trace_id)
    return CounterpartyGroupOut.model_validate(group)


@router.post(
    "/counterparty-groups/{group_id}/archive",
    summary="Архивировать группу контрагентов",
    description="Только без открытых записей: история закрытых остаётся.",
    responses=error_responses(*ADMIN_ERRORS),
)
async def post_group_archive(
    group_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, admin: AdminDep
) -> CounterpartyGroupOut:
    group = await service.archive_group(session, admin, group_id, trace_id)
    return CounterpartyGroupOut.model_validate(group)


@contacts_router.get(
    "/universities/{university_id}/contacts",
    summary="Контакты вуза",
    description="Просмотр записывается в аудит: это обращение к персональным данным.",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_contacts(
    university_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> list[ContactOut]:
    return await service.list_contacts(session, user, university_id, trace_id)


@contacts_router.post(
    "/universities/{university_id}/contacts",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить контакт вуза",
    description="Email и телефон шифруются перед записью в базу.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
    ),
)
async def post_contact(
    university_id: uuid.UUID,
    payload: ContactCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> ContactOut:
    return await service.create_contact(session, user, university_id, payload, trace_id)


@contacts_router.post(
    "/contacts/{contact_id}/archive",
    summary="Архивировать контакт",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def post_contact_archive(
    contact_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> ContactOut:
    return await service.archive_contact(session, user, contact_id, trace_id)
