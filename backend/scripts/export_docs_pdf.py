"""Собирает сопроводительную документацию в один PDF: архитектура, методы, руководства, меры.

Сдача просит документацию файлом .doc или .pdf, а тексты живут в Markdown. Pandoc и LibreOffice
для этого не нужны: тот же `fpdf2`, которым строятся отчёты, умеет всё, что здесь требуется —
заголовки, абзацы, списки, таблицы и врезки кода (ADR-013).

Запуск: `python -m scripts.export_docs_pdf` (или `make docs-pdf`). Диаграммы Mermaid в PDF
не переносятся: их рисует GitHub, и в тексте остаётся ссылка.
"""

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fpdf import FPDF
from fpdf.fonts import FontFace

from app.modules.reports.renderers import find_font

ROOT = Path(__file__).resolve().parents[2]
OUT_PATH = ROOT / "docs" / "РадарВузов-документация.pdf"
MARGIN_MM = 14
SIZES = {1: 16, 2: 13, 3: 11}
BODY_SIZE = 9.5
CODE_FILL = (243, 243, 243)
HEAD_FILL = (232, 232, 232)

# Порядок — как читают: что это, как считает, как пользоваться и как с этим жить.
DOCUMENTS: tuple[tuple[str, str], ...] = (
    ("ARCHITECTURE.md", "Архитектура и решения"),
    ("docs/DATA_PROCESSING.md", "Методы обработки данных"),
    ("docs/USER_GUIDE.md", "Руководство пользователя"),
    ("docs/ADMIN_GUIDE.md", "Руководство администратора"),
    ("docs/DEPLOY.md", "Сборка, установка и стенд"),
    ("docs/SECURITY.md", "Меры защиты"),
    ("docs/LOAD_TEST.md", "Нагрузочный тест и масштабирование"),
    ("docs/architecture/DIAGRAMS.md", "Диаграммы"),
    ("docs/COMPLIANCE.md", "Соответствие техническому заданию"),
)
# Mermaid в PDF не нарисуешь, поэтому диаграммы заранее отрисованы в картинки.
DIAGRAM_IMAGES = ROOT / "docs" / "architecture" / "images"

LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
TAG = re.compile(r"<[^>]+>")
CODE = re.compile(r"`([^`]+)`")
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
IMAGE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$")
BULLET = re.compile(r"^(\s*)[-*]\s+(.*)$")
NUMBER = re.compile(r"^(\s*)(\d+)\.\s+(.*)$")


def plain(text: str) -> str:
    """Markdown без разметки: ссылки остаются текстом, выделение снимается."""
    text = LINK.sub(r"\1", text)
    text = BOLD.sub(r"\1", text)
    text = ITALIC.sub(r"\1", text)
    # Якоря оглавления нужны на GitHub, в листе бумаги от них только мусор.
    text = TAG.sub("", text)
    return CODE.sub(r"\1", text).replace("&nbsp;", " ")


@dataclass(slots=True)
class Document:
    title: str
    lines: list[str]


def _cells(row: str) -> list[str]:
    return [plain(cell.strip()) for cell in row.strip().strip("|").split("|")]


def _is_separator(row: str) -> bool:
    return bool(row.strip()) and set(row.strip()) <= set("|-: ")


class Builder:
    def __init__(self) -> None:
        self.pdf = FPDF(orientation="P", unit="mm", format="A4")
        self.pdf.set_margin(MARGIN_MM)
        self.pdf.add_font("doc", "", str(find_font()))
        self.pdf.set_auto_page_break(auto=True, margin=MARGIN_MM)

    def cover(self, documents: list[Document]) -> None:
        pdf = self.pdf
        pdf.add_page()
        pdf.set_font("doc", size=22)
        pdf.multi_cell(0, 10, "«Радар вузов»", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("doc", size=12)
        pdf.multi_cell(
            0,
            6,
            "CRM контроля взаимодействия ИТ Школы Ростелекома с вузами.\n"
            "Кейс №6, ЛЦТ 2026. Сопроводительная документация.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(4)
        pdf.set_font("doc", size=BODY_SIZE)
        pdf.multi_cell(
            0,
            5,
            f"Собрано {datetime.now(UTC):%d.%m.%Y} командой «make docs-pdf» из документов "
            "репозитория: правится исходный Markdown, а не этот файл.\n"
            "Диаграммы связей, программно-аппаратной архитектуры и базы данных — "
            "docs/architecture/DIAGRAMS.md, модель для Archi — docs/architecture/model.xml.",
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(6)
        pdf.set_font("doc", size=SIZES[2])
        pdf.cell(0, 8, "Содержание", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("doc", size=BODY_SIZE)
        for number, document in enumerate(documents, start=1):
            pdf.cell(0, 5, f"{number}. {document.title}", new_x="LMARGIN", new_y="NEXT")

    def heading(self, level: int, text: str) -> None:
        self.pdf.ln(2)
        self.pdf.set_font("doc", size=SIZES.get(level, BODY_SIZE + 1))
        self.pdf.multi_cell(0, 6, plain(text), new_x="LMARGIN", new_y="NEXT")
        self.pdf.set_font("doc", size=BODY_SIZE)

    def paragraph(self, text: str, indent: float = 0.0) -> None:
        self.pdf.set_x(MARGIN_MM + indent)
        self.pdf.multi_cell(
            self.pdf.w - 2 * MARGIN_MM - indent, 4.6, plain(text), new_x="LMARGIN", new_y="NEXT"
        )

    def code(self, lines: list[str]) -> None:
        if not lines:
            return
        self.pdf.set_font("doc", size=BODY_SIZE - 1.5)
        self.pdf.set_fill_color(*CODE_FILL)
        self.pdf.multi_cell(
            0, 4.2, "\n".join(lines), new_x="LMARGIN", new_y="NEXT", fill=True, border=0
        )
        self.pdf.set_font("doc", size=BODY_SIZE)
        self.pdf.ln(1)

    def table(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        columns = max(len(row) for row in rows)
        widths = self._widths(rows, columns)
        self.pdf.set_font("doc", size=BODY_SIZE - 1.5)
        headings = FontFace(emphasis="", fill_color=HEAD_FILL)
        with self.pdf.table(col_widths=widths, line_height=4, headings_style=headings) as table:
            for row in rows:
                line = table.row()
                for index in range(columns):
                    line.cell(row[index] if index < len(row) else "")
        self.pdf.set_font("doc", size=BODY_SIZE)
        self.pdf.ln(2)

    def _widths(self, rows: list[list[str]], columns: int) -> tuple[float, ...]:
        """Колонка шире там, где текста больше: иначе «ID» занимает четверть страницы."""
        total = self.pdf.w - 2 * MARGIN_MM
        longest = [
            max((len(row[index]) for row in rows if index < len(row)), default=1)
            for index in range(columns)
        ]
        # Крайности сглажены: очень длинная колонка не должна съесть соседей целиком.
        weights = [max(9.0, min(float(value), 60.0)) for value in longest]
        share = total / sum(weights)
        return tuple(weight * share for weight in weights)

    def diagram(self, number: int) -> None:
        """Диаграмма — отдельная страница на боку: на портретной её подписи не прочесть."""
        path = DIAGRAM_IMAGES / f"diagram-{number}.png"
        if not path.is_file():
            return
        self.pdf.add_page(orientation="L")
        self.pdf.image(str(path), w=self.pdf.w - 2 * MARGIN_MM)
        self.pdf.add_page(orientation="P")

    def picture(self, source: str, caption: str) -> None:
        """Скриншот из справки: в документе он файлом, а не ссылкой на API."""
        name = source.rsplit("/", 1)[-1]
        path = ROOT / "backend" / "app" / "help" / "images" / name
        if not path.is_file():
            return
        width = self.pdf.w - 2 * MARGIN_MM
        # Картинка не должна разрываться: не помещается на странице — уходит на следующую.
        if self.pdf.get_y() + width * 0.6 > self.pdf.h - MARGIN_MM:
            self.pdf.add_page()
        self.pdf.image(str(path), w=width)
        if caption:
            self.pdf.set_font("doc", size=BODY_SIZE - 1.5)
            self.pdf.multi_cell(0, 4, caption, new_x="LMARGIN", new_y="NEXT", align="C")
            self.pdf.set_font("doc", size=BODY_SIZE)
        self.pdf.ln(2)

    def document(self, document: Document) -> None:
        self.pdf.add_page()
        self.heading(1, document.title)
        first_heading_skipped = False
        block: list[str] = []
        table: list[list[str]] = []
        in_code = False
        mermaid = False
        diagrams = 0
        for raw in document.lines:
            line = raw.rstrip()
            if line.startswith("```"):
                if in_code and mermaid:
                    diagrams += 1
                    self.diagram(diagrams)
                elif in_code:
                    self.code(block)
                mermaid = line.startswith("```mermaid")
                block = []
                in_code = not in_code
                continue
            if in_code:
                block.append(line)
                continue
            if line.startswith("|"):
                if not _is_separator(line):
                    table.append(_cells(line))
                continue
            if table:
                self.table(table)
                table = []
            picture = IMAGE.match(line)
            if picture:
                self.picture(picture.group(2), picture.group(1))
                continue
            heading = HEADING.match(line)
            bullet = BULLET.match(line)
            number = NUMBER.match(line)
            if heading:
                if len(heading.group(1)) == 1 and not first_heading_skipped:
                    # Заголовок документа уже напечатан: второй такой же читателю не нужен.
                    first_heading_skipped = True
                    continue
                self.heading(len(heading.group(1)), heading.group(2))
            elif bullet:
                self.paragraph(f"• {bullet.group(2)}", indent=3 + len(bullet.group(1)))
            elif number:
                self.paragraph(
                    f"{number.group(2)}. {number.group(3)}", indent=3 + len(number.group(1))
                )
            elif plain(line).strip():
                self.paragraph(line)
            else:
                self.pdf.ln(1.5)
        if table:
            self.table(table)
        if in_code:
            self.code(block)


def build() -> bytes:
    documents = [
        Document(title, (ROOT / path).read_text(encoding="utf-8").splitlines())
        for path, title in DOCUMENTS
        if (ROOT / path).exists()
    ]
    builder = Builder()
    builder.cover(documents)
    for document in documents:
        builder.document(document)
    return bytes(builder.pdf.output())


def main() -> None:
    OUT_PATH.write_bytes(build())
    size_kb = OUT_PATH.stat().st_size // 1024
    print(f"Документация собрана: {OUT_PATH} ({size_kb} КБ)")


if __name__ == "__main__":
    main()
