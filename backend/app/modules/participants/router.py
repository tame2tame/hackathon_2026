import uuid
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Query, Response, UploadFile, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.security import CurrentUserDep
from app.modules.participants.schemas import (
    ParticipantContactOut,
    ParticipantCreate,
    ParticipantImportOut,
    ParticipantOut,
    ParticipantRole,
    ParticipantRowOut,
    ParticipantsOut,
)
from app.modules.participants.service import (
    add_participant,
    export_participants,
    get_contact,
    import_participants,
    list_participants,
    remove_participant,
)

router = APIRouter(prefix="/api/v1", tags=["participants"])
COMMON = error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND)


@router.get(
    "/interactions/{interaction_id}/participants",
    summary="Обучающиеся и преподаватели по записи",
    description=(
        "ФИО и роль видит тот, кто видит запись. Почта показана сокращённо (и***@вуз.рф): "
        "адрес целиком отдаёт отдельный метод, и его запрос пишется в аудит."
    ),
    responses=COMMON,
)
async def read_participants(
    interaction_id: uuid.UUID,
    session: SessionDep,
    user: CurrentUserDep,
    role: Annotated[ParticipantRole | None, Query(description="Только одна роль")] = None,
) -> ParticipantsOut:
    return await list_participants(session, user, interaction_id, role)


@router.post(
    "/interactions/{interaction_id}/participants",
    status_code=status.HTTP_201_CREATED,
    summary="Добавить обучающегося или преподавателя",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND, ErrorCode.VALIDATION_ERROR
    ),
)
async def post_participant(
    interaction_id: uuid.UUID,
    payload: ParticipantCreate,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
) -> ParticipantOut:
    return await add_participant(session, user, interaction_id, payload, trace_id)


@router.get(
    "/participants/{participant_id}/contact",
    summary="Почта участника целиком",
    description="Персональные данные: каждый просмотр пишется в журнал аудита.",
    responses=COMMON,
)
async def read_participant_contact(
    participant_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> ParticipantContactOut:
    return await get_contact(session, user, participant_id, trace_id)


@router.delete(
    "/participants/{participant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Убрать участника из списка",
    description="Строка уходит из списка, а почта стирается: хранить её больше незачем.",
    responses=COMMON,
)
async def delete_participant(
    participant_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: CurrentUserDep
) -> None:
    await remove_participant(session, user, participant_id, trace_id)


@router.post(
    "/interactions/{interaction_id}/participants/import",
    summary="Загрузить список файлом",
    description=(
        "JSON, CSV, XLSX или XLS с колонками «ФИО», «Email», «Роль» и «Идентификатор в LMS». "
        "Человек находится по почте, а без почты — по ФИО и роли: повторная загрузка того же "
        "файла не создаёт дублей. По умолчанию — предпросмотр (`dry_run=true`)."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.IMPORT_MAPPING_INVALID,
        ErrorCode.FILE_TOO_LARGE,
    ),
)
async def post_participants_import(
    interaction_id: uuid.UUID,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
    file: Annotated[UploadFile, File(description="Файл списка")],
    dry_run: Annotated[bool, Form(description="Только показать, что будет")] = True,
    role: Annotated[ParticipantRole, Form(description="Роль строк без колонки «Роль»")] = "student",
    encoding: Annotated[
        Literal["utf-8", "windows-1251", "koi8-r", "cp866", "utf-16"] | None,
        Form(description="Кодировка CSV, если определилась неверно"),
    ] = None,
) -> ParticipantImportOut:
    outcome = await import_participants(
        session, user, interaction_id, file, dry_run, role, encoding, trace_id
    )
    return ParticipantImportOut(
        dry_run=outcome.dry_run,
        created=outcome.count("created"),
        updated=outcome.count("updated"),
        unchanged=outcome.count("unchanged"),
        errors=outcome.count("error"),
        rows=[
            ParticipantRowOut(row_no=row.row_no, key=row.key, action=row.action, detail=row.detail)
            for row in outcome.rows
        ],
    )


@router.get(
    "/interactions/{interaction_id}/participants/export",
    summary="Выгрузить список файлом",
    description=(
        "Те же колонки, что принимает загрузка. В файле почта целиком — выгрузка пишется в аудит."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/json": {}, "text/csv": {}, "application/octet-stream": {}},
            "description": "Файл списка",
        },
        **COMMON,
    },
)
async def read_participants_export(
    interaction_id: uuid.UUID,
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
    file_format: Annotated[
        Literal["json", "csv", "xlsx"], Query(alias="format", description="Формат файла")
    ] = "xlsx",
    encoding: Annotated[
        Literal["utf-8", "windows-1251"], Query(description="Кодировка CSV")
    ] = "utf-8",
) -> Response:
    content, media_type, file_name = await export_participants(
        session, user, interaction_id, file_format, encoding, trace_id
    )
    return Response(
        content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"},
    )
