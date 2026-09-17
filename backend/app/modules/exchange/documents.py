"""Сборка документов обмена одним набором запросов на любое число записей."""

import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.storage import get_storage
from app.modules.catalogs.models import Product, Program
from app.modules.exchange.schemas import (
    DocumentApplication,
    DocumentContract,
    DocumentCounterparty,
    DocumentFile,
    DocumentGroup,
    DocumentPerson,
    DocumentProduct,
    DocumentProgram,
    DocumentRecord,
    DocumentStatus,
    InteractionDocument,
)
from app.modules.integrations.models import SiteApplication
from app.modules.interactions.models import Attachment, Interaction
from app.modules.workflow.models import Stage, WorkflowVersion


def _counterparty(interaction: Interaction) -> DocumentCounterparty:
    if interaction.university is not None:
        university = interaction.university
        return DocumentCounterparty(
            kind="university",
            id=university.id,
            name=university.name,
            short_name=university.short_name,
            region=university.region,
            city=university.city,
            inn=None,
        )
    client = interaction.client
    if client is None:
        raise ValueError("У взаимодействия нет контрагента")
    return DocumentCounterparty(
        kind="person" if client.kind == "person" else "organization",
        id=client.id,
        name=client.name,
        short_name=client.name,
        region=None,
        city=client.city,
        inn=client.inn,
    )


async def build_documents(
    session: AsyncSession, interaction_ids: Sequence[uuid.UUID], now: datetime | None = None
) -> list[InteractionDocument]:
    """Документы в порядке переданных id; несуществующие записи пропускаются."""
    now = now or datetime.now(UTC)
    ids = list(dict.fromkeys(interaction_ids))
    if not ids:
        return []
    interactions = {
        interaction.id: interaction
        for interaction in (
            await session.scalars(
                select(Interaction)
                .where(Interaction.id.in_(ids))
                .options(
                    joinedload(Interaction.group),
                    joinedload(Interaction.university),
                    joinedload(Interaction.client),
                    joinedload(Interaction.program).joinedload(Program.direction),
                    joinedload(Interaction.product).joinedload(Product.vendor),
                    joinedload(Interaction.owner),
                    joinedload(Interaction.current_stage),
                    joinedload(Interaction.contract),
                    joinedload(Interaction.workflow_version),
                )
            )
        ).unique()
    }
    files: dict[uuid.UUID, list[DocumentFile]] = defaultdict(list)
    storage = get_storage()
    for attachment, stage_code in (
        await session.execute(
            select(Attachment, Stage.code)
            .join(Stage, Stage.id == Attachment.stage_id)
            .where(Attachment.interaction_id.in_(ids))
            .order_by(Attachment.uploaded_at, Attachment.id)
        )
    ).tuples():
        files[attachment.interaction_id].append(
            DocumentFile(
                id=attachment.id,
                document_type=attachment.document_type,
                file_name=attachment.file_name,
                mime_type=attachment.mime_type,
                size_bytes=attachment.size_bytes,
                sha256=attachment.sha256,
                stage_code=stage_code,
                uploaded_at=attachment.uploaded_at,
                storage=storage.locate(attachment.storage_key),
            )
        )
    applications: dict[uuid.UUID, list[DocumentApplication]] = defaultdict(list)
    for application in await session.scalars(
        select(SiteApplication)
        .where(SiteApplication.interaction_id.in_(ids))
        .order_by(SiteApplication.received_at)
    ):
        if application.interaction_id is not None:
            applications[application.interaction_id].append(
                DocumentApplication(
                    id=application.id,
                    external_id=application.external_id,
                    received_at=application.received_at,
                )
            )

    documents: list[InteractionDocument] = []
    for interaction_id in ids:
        interaction = interactions.get(interaction_id)
        if interaction is None:
            continue
        version: WorkflowVersion = interaction.workflow_version
        program = interaction.program
        product = interaction.product
        contract = interaction.contract
        documents.append(
            InteractionDocument(
                record=DocumentRecord(id=interaction.id, version=interaction.version),
                group=DocumentGroup(
                    id=interaction.group.id,
                    code=interaction.group.code,
                    name=interaction.group.name,
                ),
                status=DocumentStatus(
                    state=interaction.status,
                    stage_code=interaction.current_stage.code,
                    stage_name=interaction.current_stage.name,
                    stage_entered_at=interaction.stage_entered_at,
                    workflow_template_id=version.template_id,
                    workflow_version_id=version.id,
                ),
                owner=DocumentPerson(
                    id=interaction.owner.id, full_name=interaction.owner.full_name
                ),
                counterparty=_counterparty(interaction),
                program=DocumentProgram(
                    id=program.id,
                    name=program.name,
                    direction_code=program.direction.code,
                    direction_name=program.direction.name,
                    lms_course_ref=program.lms_course_ref,
                ),
                product=DocumentProduct(
                    id=product.id, name=product.name, vendor_name=product.vendor.name
                )
                if product is not None
                else None,
                contract=DocumentContract(
                    id=contract.id,
                    number=contract.number,
                    signed_at=contract.signed_at,
                    license_valid_until=contract.license_valid_until,
                    transfer_status=contract.transfer_status,
                )
                if contract is not None
                else None,
                files=files[interaction.id],
                site_applications=applications[interaction.id],
                created_at=interaction.created_at,
                updated_at=interaction.updated_at,
                exported_at=now,
            )
        )
    return documents
