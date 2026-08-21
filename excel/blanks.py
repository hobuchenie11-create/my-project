"""Бумажные бланки для передачи показаний — по одному на квартиру.

Жители, которые не пользуются мессенджерами, приносят показания на бумаге,
и разобрать чужой почерк удаётся не всегда: «1» против «7», «4» против «9».
Клетчатый бланк снимает почти все такие ошибки — под каждую цифру своя
клетка, а номер квартиры напечатан заранее, поэтому перепутать её нельзя.

Набор счётчиков берётся из реестра: у 1-2-комнатных один ХВС и один ГВС,
у 3-комнатных — кухня и санузел отдельно плюс строка «Сумма ГВС», которую
ждёт ОЭК.

Из кода:  generate_blanks(conn, out_path, period_name)
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from bot.config import config
from database.models import METER_KINDS

# Порядок строк на бланке — тот же, что в ведомости: заполненный бланк
# читается сверху вниз без перескакиваний
METER_ORDER = ("electricity", "cws", "cws_kitchen", "cws_bathroom",
               "hws", "hws_kitchen", "hws_bathroom")

# Строка для суммы ГВС — не прибор, но её ждёт ОЭК одной цифрой
HWS_TOTAL_ROW = "Сумма ГВС (кухня + ванна)"

DIGIT_CELLS = 6          # 61682 — пять знаков, шестой про запас

# Сколько высоты помещается на листе А4 (пункты). Бланки разной длины —
# у 1-2-комнатной три прибора, у 3-комнатной шесть, — поэтому на лист их
# набирается сколько влезет: по три коротких или по два длинных.
PAGE_BUDGET_PT = 780

LABEL_WIDTH = 26
DIGIT_WIDTH = 5.4
UNIT_WIDTH = 8

DIGIT_ROW_HEIGHT = 30    # клетка под рукописную цифру — крупная
TITLE_ROW_HEIGHT = 22
NUMBER_ROW_HEIGHT = 34
TEXT_ROW_HEIGHT = 18
GAP_ROW_HEIGHT = 8

_thick = Side(style="medium")
CELL_BORDER = Border(left=_thick, right=_thick, top=_thick, bottom=_thick)
CUT_LINE = Border(bottom=Side(style="dashed"))


def generate_blanks(conn, out_path: Path, period_name: str,
                    numbers: list[str] | None = None) -> Path:
    """Книга с бланками: по одному на квартиру, два бланка на лист А4."""
    from database import repository

    apartments = [a for a in repository.list_apartments(conn)
                  if a["type"] == "residential"]
    if numbers:
        wanted = {str(n).strip() for n in numbers}
        apartments = [a for a in apartments if a["number"] in wanted]

    wb = Workbook()
    ws = wb.active
    ws.title = "Бланки"
    _setup_sheet(ws)

    row = 1
    used = 0.0
    for apartment in apartments:
        meters = [m["kind"] for m in repository.meters_for_apartment(conn, apartment["id"])]
        height = _blank_height(meters)
        if used and used + height > PAGE_BUDGET_PT:
            ws.row_breaks.append(Break(id=row - 1))   # бланк не режем пополам
            used = 0.0
        row = _draw_blank(ws, row, apartment["number"], meters, period_name)
        used += height

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def _meter_rows(meters: list[str]) -> int:
    """Сколько строк с клетками будет на бланке (с учётом строки суммы ГВС)."""
    rows = sum(1 for kind in METER_ORDER if kind in meters)
    return rows + (1 if "hws_kitchen" in meters else 0)


def _blank_height(meters: list[str]) -> float:
    return (TITLE_ROW_HEIGHT + NUMBER_ROW_HEIGHT
            + _meter_rows(meters) * DIGIT_ROW_HEIGHT
            + 2 * TEXT_ROW_HEIGHT + 2 * GAP_ROW_HEIGHT)


def _setup_sheet(ws) -> None:
    ws.column_dimensions["A"].width = LABEL_WIDTH
    for col in range(2, 2 + DIGIT_CELLS):
        ws.column_dimensions[get_column_letter(col)].width = DIGIT_WIDTH
    ws.column_dimensions[get_column_letter(2 + DIGIT_CELLS)].width = UNIT_WIDTH

    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.page_margins.left = 0.5
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.4
    ws.page_margins.bottom = 0.3
    ws.page_margins.header = 0.0
    ws.page_margins.footer = 0.0


def _draw_blank(ws, row: int, number: str, meters: list[str],
                period_name: str) -> int:
    """Рисует один бланк с строки row. Возвращает строку, с которой начать следующий."""
    last_col = 1 + DIGIT_CELLS + 1

    row = _text_row(ws, row, "ПОКАЗАНИЯ СЧЁТЧИКОВ", last_col,
                    Font(bold=True, size=13), TITLE_ROW_HEIGHT, "center")

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    flat = ws.cell(row=row, column=1, value=f"Кв. {number}")
    flat.font = Font(bold=True, size=22)
    flat.alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=last_col)
    period = ws.cell(row=row, column=4, value=f"за {period_name}")
    period.font = Font(size=12)
    period.alignment = Alignment(horizontal="right", vertical="center")
    ws.row_dimensions[row].height = NUMBER_ROW_HEIGHT
    row += 1

    for kind in METER_ORDER:
        if kind in meters:
            row = _meter_row(ws, row, METER_KINDS[kind],
                             "кВт·ч" if kind == "electricity" else "м³")
    # Раздельный учёт ГВС — ресурснику нужна ещё и сумма одной цифрой
    if "hws_kitchen" in meters:
        row = _meter_row(ws, row, HWS_TOTAL_ROW, "м³")

    # Обе строки — по одной строчке текста: объединённая ячейка не переносит
    # длинный текст, а обрезает его по краю бланка
    row = _text_row(ws, row,
                    "Пишите только чёрные цифры (кубометры), "
                    "красные (литры) — не нужно.",
                    last_col, Font(size=10, italic=True), TEXT_ROW_HEIGHT, "left")
    row = _text_row(ws, row,
                    "Дата ___________   Подпись ___________   "
                    f"Сдать до {config.readings_day_end} числа",
                    last_col, Font(size=11), TEXT_ROW_HEIGHT, "left")

    # Пунктир — линия отреза между бланками на листе
    for col in range(1, last_col + 1):
        ws.cell(row=row, column=col).border = CUT_LINE
    ws.row_dimensions[row].height = GAP_ROW_HEIGHT
    ws.row_dimensions[row + 1].height = GAP_ROW_HEIGHT   # отступ до следующего
    return row + 2


def _meter_row(ws, row: int, label: str, unit: str) -> int:
    """Строка прибора: подпись, клетки под цифры, единица измерения."""
    name = ws.cell(row=row, column=1, value=label)
    name.font = Font(size=12)
    name.alignment = Alignment(horizontal="right", vertical="center")

    for col in range(2, 2 + DIGIT_CELLS):
        cell = ws.cell(row=row, column=col)
        cell.border = CELL_BORDER
        cell.font = Font(size=16)
        cell.alignment = Alignment(horizontal="center", vertical="center")

    unit_cell = ws.cell(row=row, column=2 + DIGIT_CELLS, value=unit)
    unit_cell.font = Font(size=10)
    unit_cell.alignment = Alignment(horizontal="left", vertical="center")

    ws.row_dimensions[row].height = DIGIT_ROW_HEIGHT
    return row + 1


def _text_row(ws, row: int, text: str, last_col: int, font: Font,
              height: float, align: str) -> int:
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    cell = ws.cell(row=row, column=1, value=text)
    cell.font = font
    cell.alignment = Alignment(horizontal=align, vertical="center")
    ws.row_dimensions[row].height = height
    return row + 1
