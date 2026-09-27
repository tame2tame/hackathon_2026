"""Сборщик PDF документации: разметка снимается, а содержимое остаётся."""

import pytest

from scripts import export_docs_pdf
from scripts.export_docs_pdf import MissingSource, _cells, build, plain


def test_code_keeps_angle_brackets_and_markup_is_removed() -> None:
    text = 'Заголовок `Authorization: Bearer <токен>` и <a id="x"></a>[ссылка](u) **жирно**'

    # Раньше «<токен>» пропадал и в документации оставалось «Bearer ».
    assert plain(text) == "Заголовок Authorization: Bearer <токен> и ссылка жирно"


def test_escaped_pipe_stays_inside_the_cell() -> None:
    assert _cells(r"| `a \| b` | c |") == ["a | b", "c"]


def test_missing_document_stops_the_build(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        export_docs_pdf, "DOCUMENTS", (*export_docs_pdf.DOCUMENTS, ("docs/НЕТ.md", "Нет"))
    )

    with pytest.raises(MissingSource, match=r"docs/НЕТ\.md"):
        build()


def test_same_sources_give_the_same_file() -> None:
    assert build() == build()
