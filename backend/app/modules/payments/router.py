import uuid
from typing import Annotated, Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, CurrentUserDep, require_roles
from app.modules.payments import lms
from app.modules.payments.schemas import PaymentImportOut, PaymentRowOut
from app.modules.payments.service import import_payments

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


@router.post(
    "/import",
    summary="Загрузить оплаты из платёжной системы",
    description=(
        "JSON платёжной системы (массив записей с полями «Номер заявки», «Курс», «Фамилия», "
        "«Имя», «Отчество», «Телефон», «Email», «Номер потока»), а также CSV, XLSX или XLS "
        "с теми же колонками. Человек находится по почте или заводится карточкой клиента, "
        "его запись B2C по курсу находится или заводится и переходит на «Зачисление в LMS». "
        "Номер заявки уникален: повторная загрузка ничего не дублирует. По умолчанию — "
        "предпросмотр (`dry_run=true`)."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.IMPORT_MAPPING_INVALID,
        ErrorCode.FILE_TOO_LARGE,
    ),
)
async def post_payments_import(
    trace_id: TraceIdDep,
    session: SessionDep,
    user: ManagerDep,
    file: Annotated[UploadFile, File(description="Выгрузка оплат")],
    dry_run: Annotated[bool, Form(description="Только показать, что будет")] = True,
    encoding: Annotated[
        Literal["utf-8", "windows-1251", "koi8-r", "cp866", "utf-16"] | None,
        Form(description="Кодировка CSV, если определилась неверно"),
    ] = None,
) -> PaymentImportOut:
    outcome = await import_payments(session, user, file, dry_run, encoding, trace_id)
    return PaymentImportOut(
        dry_run=outcome.dry_run,
        created=outcome.count("created"),
        updated=outcome.count("updated"),
        unchanged=outcome.count("unchanged"),
        errors=outcome.count("error"),
        rows=[
            PaymentRowOut(row_no=row.row_no, key=row.key, action=row.action, detail=row.detail)
            for row in outcome.rows
        ],
    )


@router.get(
    "/lms-users",
    summary="Файл «Загрузка пользователей» для LMS",
    description=(
        "XLSX по шаблону LMS: частные лица на этапе «Зачисление в LMS» в области видимости, "
        "по курсу и потоку. Заполнены ФИО, телефон и почта; паспорт, СНИЛС и диплом CRM не "
        "хранит. В файле персональные данные — выгрузка пишется в журнал аудита."
    ),
    response_class=Response,
    responses={
        200: {"content": {lms.MEDIA_TYPE: {}}, "description": "Файл для загрузки в LMS"},
        **error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.VALIDATION_ERROR),
    },
)
async def read_lms_users(
    trace_id: TraceIdDep,
    session: SessionDep,
    user: CurrentUserDep,
    stage_code: Annotated[str, Query(max_length=60, description="Этап записей")] = "enrollment",
    program_id: Annotated[uuid.UUID | None, Query(description="Курс")] = None,
    stream: Annotated[int | None, Query(ge=1, description="Номер потока из оплаты")] = None,
) -> Response:
    content, file_name = await lms.export_lms_users(
        session, user, stage_code, program_id, stream, trace_id
    )
    return Response(
        content,
        media_type=lms.MEDIA_TYPE,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(file_name)}"},
    )
