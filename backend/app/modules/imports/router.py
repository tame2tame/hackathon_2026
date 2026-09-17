import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.core.db import SessionDep
from app.core.errors import ErrorCode, TraceIdDep, error_responses
from app.core.roles import Role
from app.core.security import CurrentUser, require_roles
from app.modules.imports.mapping import REQUIRED_FIELDS, ImportField, suggest
from app.modules.imports.models import ImportBatch, ImportRow
from app.modules.imports.schemas import (
    ApplyResult,
    ImportBatchOut,
    ImportProfileOut,
    MappingUpdate,
    RowPreview,
)
from app.modules.imports.service import (
    PREVIEW_ROWS,
    apply_batch,
    batch_rows,
    create_batch,
    list_profiles,
    row_values,
    set_mapping,
)

router = APIRouter(prefix="/api/v1", tags=["imports"])
ManagerDep = Annotated[CurrentUser, Depends(require_roles(Role.MANAGER, Role.ADMIN))]


def _preview(batch: ImportBatch, rows: list[ImportRow]) -> ImportBatchOut:
    previews: list[RowPreview] = []
    for row in rows[:PREVIEW_ROWS]:
        values = row_values(row.raw, batch.column_map)
        previews.append(
            RowPreview(
                row_no=row.row_no,
                resolution=row.resolution,
                detail=row.detail,
                university=values.university,
                product=values.product,
                contract_number=values.contract_number,
            )
        )
    return ImportBatchOut(
        id=batch.id,
        file_name=batch.file_name,
        file_kind=batch.file_kind,
        encoding=batch.encoding,
        delimiter=batch.delimiter,
        status=batch.status,
        headers=batch.headers,
        column_map=batch.column_map,
        suggested_map=suggest(batch.headers),
        fields=[field.value for field in ImportField],
        required_fields=[field.value for field in REQUIRED_FIELDS],
        total_rows=int(batch.stats.get("total", 0)),
        stats={key: int(value) for key, value in batch.stats.items()},
        rows=previews,
    )


@router.post(
    "/imports",
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить выгрузку xls, xlsx или csv",
    description=(
        "Возвращает колонки файла, подсказку соответствия по заголовкам ТЗ и параметры чтения. "
        "Кодировку CSV система определяет сама (BOM, UTF-8, иначе cp1251, KOI8-R или cp866 по "
        "содержимому), разделитель — по образцу строк. Если в предпросмотре «кракозябры», "
        "загрузите файл снова, указав `encoding`; для старых xls без кодовой страницы она тоже "
        "учитывается."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.FILE_TYPE_NOT_ALLOWED,
        ErrorCode.FILE_TOO_LARGE,
    ),
)
async def post_import(
    session: SessionDep,
    user: ManagerDep,
    file: Annotated[UploadFile, File(description="Книга Excel или CSV с выгрузкой")],
    encoding: Annotated[
        Literal["utf-8", "windows-1251", "koi8-r", "cp866", "utf-16"] | None,
        Form(description="Кодировка файла, если определилась неверно"),
    ] = None,
) -> ImportBatchOut:
    batch = await create_batch(session, user, file, encoding)
    return _preview(batch, await batch_rows(session, batch.id))


@router.put(
    "/imports/{batch_id}/mapping",
    summary="Задать соответствие колонок и увидеть предпросмотр",
    description="Каждая строка получает решение: new, update, conflict, skip или needs_program.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.IMPORT_MAPPING_INVALID,
    ),
)
async def put_mapping(
    batch_id: uuid.UUID, payload: MappingUpdate, session: SessionDep, user: ManagerDep
) -> ImportBatchOut:
    batch = await set_mapping(session, user, batch_id, payload.column_map, payload.save_as_profile)
    return _preview(batch, await batch_rows(session, batch.id))


@router.post(
    "/imports/{batch_id}/apply",
    summary="Применить загрузку",
    description="Создаёт и обновляет записи по строкам new и update, затем пересчитывает радар.",
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.AUTH_FORBIDDEN,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
    ),
)
async def post_apply(
    batch_id: uuid.UUID, trace_id: TraceIdDep, session: SessionDep, user: ManagerDep
) -> ApplyResult:
    return await apply_batch(session, user, batch_id, trace_id=trace_id)


@router.get(
    "/import-profiles",
    summary="Сохранённые соответствия колонок",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.AUTH_FORBIDDEN),
)
async def read_import_profiles(session: SessionDep, user: ManagerDep) -> list[ImportProfileOut]:
    return [ImportProfileOut.model_validate(profile) for profile in await list_profiles(session)]
