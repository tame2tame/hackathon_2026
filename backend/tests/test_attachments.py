"""Вложения: белый список типов, лимит размера, область видимости и закрытие сигнала."""

import pytest
from httpx import AsyncClient

from app.core.config import Settings
from app.modules.attachments import files, service
from tests.api import PDF_BYTES, find, upload_pdf
from tests.users import ANNA_KAM, MIKHAIL_KAM, as_user

EXE = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 64
ZIP_FILE = files.ZIP + b"\x14\x00\x00\x00" + b"\x00" * 32
OLE2_FILE = files.OLE2 + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32


async def attachments_of(client: AsyncClient, email: str, interaction_id: str) -> list[dict]:
    response = await client.get(
        f"/api/v1/interactions/{interaction_id}/attachments", headers=as_user(email)
    )
    assert response.status_code == 200
    items: list[dict] = response.json()
    return items


async def test_signed_contract_closes_missing_document(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    before = (
        await client.get(f"/api/v1/interactions/{item['id']}", headers=as_user(ANNA_KAM))
    ).json()
    assert "missing_document" in {signal["kind"] for signal in before["signals"]}

    uploaded = await upload_pdf(client, ANNA_KAM, item["id"], "signed_contract")

    assert uploaded["mime_type"] == "application/pdf"
    assert uploaded["size_bytes"] == len(PDF_BYTES)
    card = (
        await client.get(f"/api/v1/interactions/{item['id']}", headers=as_user(ANNA_KAM))
    ).json()
    assert "missing_document" not in {signal["kind"] for signal in card["signals"]}


@pytest.mark.parametrize(
    ("file_name", "content", "mime"),
    [
        ("Скан.png", PNG, "image/png"),
        ("Акт.docx", ZIP_FILE, None),
        ("Смета.xls", OLE2_FILE, "application/vnd.ms-excel"),
    ],
)
async def test_allowed_types_are_accepted(
    client: AsyncClient, file_name: str, content: bytes, mime: str | None
) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/attachments",
        files={"file": (file_name, content, "application/octet-stream")},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 201
    if mime is not None:
        assert response.json()["mime_type"] == mime


async def test_executable_renamed_to_pdf_is_refused(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/attachments",
        files={"file": ("Договор.pdf", EXE, "application/pdf")},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 415
    assert response.json()["code"] == "FILE_TYPE_NOT_ALLOWED"


async def test_file_over_limit_is_refused(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    small_limit = Settings(app_env="test", auth_mode="dev", max_upload_mb=1)
    monkeypatch.setattr(service, "get_settings", lambda: small_limit)
    big_file = b"%PDF-1.7\n" + b"0" * (2 * 1024 * 1024)

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/attachments",
        files={"file": ("Большой.pdf", big_file, "application/pdf")},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 413
    assert response.json()["code"] == "FILE_TOO_LARGE"


async def test_empty_file_is_refused(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/attachments",
        files={"file": ("Пустой.pdf", b"", "application/pdf")},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 422
    assert response.json()["errors"] == [{"field": "file", "message": "Пустой файл"}]


async def test_unknown_document_type_is_refused(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")

    response = await client.post(
        f"/api/v1/interactions/{item['id']}/attachments",
        files={"file": ("Договор.pdf", PDF_BYTES, "application/pdf")},
        data={"document_type": "transfer_akt"},
        headers=as_user(ANNA_KAM),
    )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["errors"] == [{"field": "document_type", "message": "Неизвестный тип документа"}]


async def test_foreign_interaction_accepts_nothing(client: AsyncClient) -> None:
    foreign = await find(client, MIKHAIL_KAM, search="УрФУ")

    upload = await client.post(
        f"/api/v1/interactions/{foreign['id']}/attachments",
        files={"file": ("Договор.pdf", PDF_BYTES, "application/pdf")},
        headers=as_user(ANNA_KAM),
    )
    listing = await client.get(
        f"/api/v1/interactions/{foreign['id']}/attachments", headers=as_user(ANNA_KAM)
    )

    assert (upload.status_code, listing.status_code) == (404, 404)


async def test_file_is_returned_to_its_owner_only(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    uploaded = await upload_pdf(client, ANNA_KAM, item["id"], "signed_contract")

    mine = await client.get(f"/api/v1/attachments/{uploaded['id']}/file", headers=as_user(ANNA_KAM))
    foreign = await client.get(
        f"/api/v1/attachments/{uploaded['id']}/file", headers=as_user(MIKHAIL_KAM)
    )

    assert mine.status_code == 200
    assert mine.content == PDF_BYTES
    assert "%D0%94%D0%BE%D0%B3%D0%BE%D0%B2%D0%BE%D1%80.pdf" in mine.headers["content-disposition"]
    assert foreign.status_code == 404


async def test_listing_shows_uploads_newest_first(client: AsyncClient) -> None:
    item = await find(client, ANNA_KAM, stage_code="signing")
    await upload_pdf(client, ANNA_KAM, item["id"], "signed_contract", file_name="Договор.pdf")
    await upload_pdf(client, ANNA_KAM, item["id"], file_name="Приложение.pdf")

    items = await attachments_of(client, ANNA_KAM, item["id"])

    assert [attachment["file_name"] for attachment in items] == ["Приложение.pdf", "Договор.pdf"]
    assert items[0]["document_type"] is None
    assert items[1]["document_type"] == "signed_contract"


def test_name_with_path_and_control_characters_is_cleaned() -> None:
    assert files.safe_name("../../etc/passwd") == "passwd"
    assert files.safe_name(r"C:\Users\kam\Договор?.pdf") == "Договор.pdf"
    assert files.safe_name("   ...   ") == "file"
