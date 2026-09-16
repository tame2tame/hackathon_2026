import uuid
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Request, UploadFile, status
from fastapi.responses import StreamingResponse

from app.core.db import SessionDep
from app.core.errors import ErrorCode, error_responses
from app.core.security import CurrentUserDep
from app.modules.attachments.schemas import AttachmentOut
from app.modules.attachments.service import (
    list_attachments,
    open_attachment,
    read_chunks,
    upload_attachment,
)

router = APIRouter(prefix="/api/v1", tags=["attachments"])


@router.post(
    "/interactions/{interaction_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    summary="Загрузить документ к взаимодействию",
    description=(
        "Файл проверяется по расширению и сигнатуре, лимит задаёт `MAX_UPLOAD_MB`. "
        "Документ привязывается к текущему этапу и закрывает сигнал «нет документа»."
    ),
    responses=error_responses(
        ErrorCode.AUTH_REQUIRED,
        ErrorCode.NOT_FOUND,
        ErrorCode.VALIDATION_ERROR,
        ErrorCode.FILE_TYPE_NOT_ALLOWED,
        ErrorCode.FILE_TOO_LARGE,
    ),
)
async def post_attachment(
    interaction_id: uuid.UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
    file: Annotated[UploadFile, File(description="Файл документа")],
    document_type: Annotated[
        str | None, Form(description="Тип документа этапа, например signed_contract")
    ] = None,
) -> AttachmentOut:
    trace_id = getattr(request.state, "trace_id", None)
    attachment = await upload_attachment(
        session, user, interaction_id, file, document_type, trace_id=trace_id
    )
    return AttachmentOut.model_validate(attachment)


@router.get(
    "/interactions/{interaction_id}/attachments",
    summary="Документы взаимодействия",
    responses=error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
)
async def read_attachments(
    interaction_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> list[AttachmentOut]:
    attachments = await list_attachments(session, user, interaction_id)
    return [AttachmentOut.model_validate(attachment) for attachment in attachments]


@router.get(
    "/attachments/{attachment_id}/file",
    summary="Скачать файл вложения",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"application/octet-stream": {}},
            "description": "Файл вложения с исходным именем",
        },
        **error_responses(ErrorCode.AUTH_REQUIRED, ErrorCode.NOT_FOUND),
    },
)
async def read_attachment_file(
    attachment_id: uuid.UUID, session: SessionDep, user: CurrentUserDep
) -> StreamingResponse:
    attachment, stream = await open_attachment(session, user, attachment_id)
    # filename* — чтобы кириллические имена доходили без искажений.
    disposition = f"attachment; filename*=UTF-8''{quote(attachment.file_name)}"
    return StreamingResponse(
        read_chunks(stream),
        media_type=attachment.mime_type,
        headers={"Content-Disposition": disposition},
    )
