"""Диаграммы статистики в PDF: столбики рисует сам fpdf2, без headless-браузера (ADR-013).

Те же числа интерфейс рисует ECharts по полю `option`, а сервер — этими примитивами. Картинка
нужна там, где браузера нет: отчёт на почту, распечатка на совещание, приложение к письму вузу.
"""

from datetime import UTC, datetime

from fpdf import FPDF

from app.modules.analytics.schemas import ChartOut
from app.modules.reports.renderers import find_font

MARGIN_MM = 12
TITLE_SIZE = 14
CHART_TITLE_SIZE = 11
LABEL_SIZE = 7
# Высота области столбиков: под ней подписи, над ней заголовок.
PLOT_HEIGHT_MM = 52
# Над самым высоким столбиком остаётся место под его значение, иначе оно налезет на заголовок.
VALUE_ROOM_MM = 6
BAR_GAP_MM = 2
BAR_COLOR = (47, 111, 237)
GRID_COLOR = (215, 215, 215)


def _bars(pdf: FPDF, chart: ChartOut) -> None:
    pdf.set_font("report", size=CHART_TITLE_SIZE)
    pdf.cell(0, 7, chart.title, new_x="LMARGIN", new_y="NEXT")
    top = pdf.get_y()
    width = pdf.w - 2 * MARGIN_MM
    bottom = top + PLOT_HEIGHT_MM

    pdf.set_draw_color(*GRID_COLOR)
    pdf.line(MARGIN_MM, bottom, MARGIN_MM + width, bottom)
    if not chart.values:
        pdf.set_font("report", size=LABEL_SIZE)
        pdf.set_xy(MARGIN_MM, bottom + 2)
        pdf.cell(0, 5, "Нет данных за период", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        return

    largest = max(chart.values) or 1
    step = width / len(chart.values)
    bar_width = max(step - BAR_GAP_MM, 1.5)
    pdf.set_fill_color(*BAR_COLOR)
    pdf.set_font("report", size=LABEL_SIZE)
    for index, value in enumerate(chart.values):
        height = (PLOT_HEIGHT_MM - VALUE_ROOM_MM) * value / largest
        left = MARGIN_MM + index * step + (step - bar_width) / 2
        if height > 0:
            pdf.rect(left, bottom - height, bar_width, height, style="F")
        # Значение над столбиком, подпись под осью: так читается без легенды.
        pdf.set_xy(left - 2, bottom - height - 4)
        pdf.cell(bar_width + 4, 4, str(value), align="C")
        pdf.set_xy(left - 2, bottom + 1)
        pdf.multi_cell(bar_width + 4, 3, chart.labels[index], align="C", max_line_height=3)
    pdf.set_y(bottom + 12)


def render_charts(title: str, subtitle: str, charts: list[ChartOut]) -> bytes:
    """Одна страница на диаграмму: печатать и пересылать проще, чем скриншоты экрана."""
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margin(MARGIN_MM)
    pdf.add_font("report", "", str(find_font()))
    pdf.set_auto_page_break(auto=True, margin=MARGIN_MM)
    pdf.add_page()
    pdf.set_font("report", size=TITLE_SIZE)
    pdf.cell(0, 9, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("report", size=LABEL_SIZE + 1)
    pdf.cell(0, 5, subtitle, new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        5,
        f"Сформировано {datetime.now(UTC):%d.%m.%Y %H:%M} UTC",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)
    for chart in charts:
        # Диаграмма не должна разрываться между страницами: не помещается — переносим целиком.
        if pdf.get_y() + PLOT_HEIGHT_MM + 24 > pdf.h - MARGIN_MM:
            pdf.add_page()
        _bars(pdf, chart)
    return bytes(pdf.output())
