"""Бумажные бланки для передачи показаний — по одному на квартиру.

Жители, которые не пользуются мессенджерами, приносят показания на бумаге,
и разобрать чужой почерк удаётся не всегда: «1» против «7», «4» против «9».
Клетчатый бланк снимает почти все такие ошибки — под каждую цифру своя
клетка, а номер квартиры напечатан заранее, поэтому перепутать её нельзя.

Набор счётчиков берётся из реестра: у 1-2-комнатных один ХВС и один ГВС,
у 3-комнатных — кухня и санузел отдельно плюс строка «Сумма ГВС», которую
ждёт ОЭК.

Месяц на бланке не печатается — вместо него пустая строка «Период»: бланки
раздают пачкой вперёд, а период житель вписывает сам при заполнении.

Из кода:  generate_blanks(conn, out_path)
"""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from database.models import METER_KINDS

# Порядок строк на бланке — тот же, что в ведомости: заполненный бланк
# читается сверху вниз без перескакиваний
METER_ORDER = ("electricity", "cws", "cws_kitchen", "cws_bathroom",
               "hws", "hws_kitchen", "hws_bathroom")

# Строка для суммы ГВС — не прибор, но её ждёт ОЭК одной цифрой
HWS_TOTAL_ROW = "Сумма ГВС (кухня + ванна)"

# Куда сдавать заполненный бланк. Текст правится здесь — он печатается на
# каждом бланке. Строки короткие не случайно: объединённая ячейка длинный
# текст не переносит, а обрезает по краю бланка.
DELIVERY_LINES = (
    "Заполненный бланк передавайте с 16 по 18 число:",
    "• в ящик для показаний на информационном стенде;",
    "• или фото бланка председателю в Ватсап или Телеграм;",
    "• также показания можно передать в чате дома.",
)

# Сопроводительная памятка: печатается отдельным листом и выдаётся вместе с
# бланком. Жители, передающие показания на бумаге, чат обычно не читают —
# для них это единственное объяснение, откуда взялся новый бланк.
# Строки заранее разбиты по ширине листа: объединённая ячейка длинный текст
# не переносит, а обрезает.
COVER_LINES: tuple[tuple[str, int, bool], ...] = (
    ("Уважаемые соседи!", 14, True),
    ("", 11, False),
    ("С этого месяца показания счётчиков в нашем доме принимает и", 11, False),
    ("обрабатывает автоматическая система «Домовед»: реестр показаний и", 11, False),
    ("ведомость для ресурсоснабжающих организаций собираются программой,", 11, False),
    ("без переписывания вручную.", 11, False),
    ("", 11, False),
    ("Поэтому меняется и бумажный бланк. Новый бланк выдан председателем", 11, False),
    ("совета дома: на нём заранее напечатаны номер вашей квартиры и ваши", 11, False),
    ("счётчики, а под каждую цифру отведена отдельная клетка. Так показания", 11, False),
    ("читаются однозначно и не попадают в чужую квартиру.", 11, False),
    ("", 11, False),
    ("Как заполнять, чтобы цифры прочитались верно:", 12, True),
    ("• вверху бланка, в строке «Период», впишите месяц, за который", 11, False),
    ("  передаёте показания;", 11, False),
    ("• пишите ручкой — синей или чёрной, не карандашом;", 11, False),
    ("• цифры печатные и крупные, по одной в клетку: не выходите за", 11, False),
    ("  границы клетки и не соединяйте цифры между собой;", 11, False),
    ("• начинайте с левой клетки, лишние клетки справа оставьте пустыми;", 11, False),
    ("• «1» пишите с уголком, «7» — с перекладиной посередине, иначе их", 11, False),
    ("  легко перепутать; «0» не перечёркивайте;", 11, False),
    ("• только чёрные цифры со счётчика (кубометры). Красные (литры),", 11, False),
    ("  запятые и дробную часть писать не нужно;", 11, False),
    ("• в строке «Сумма ГВС» — кухня плюс ванна, одной цифрой:", 11, False),
    ("  её отдельно ждёт ОЭК;", 11, False),
    ("• ошиблись — зачеркните всю строку одной чертой и напишите", 11, False),
    ("  правильное показание рядом, на полях бланка;", 11, False),
    ("• внизу поставьте дату и подпись.", 11, False),
    ("", 11, False),
    ("Куда передавать заполненный бланк:", 12, True),
    ("• с 16 по 18 число — в ящик для показаний на информационном стенде;", 11, False),
    ("• или фото бланка председателю дома в Ватсап или Телеграм;", 11, False),
    ("• также показания можно передать в чате дома.", 11, False),
    ("", 11, False),
    ("Показания, переданные позже срока, будут приняты, но учтены уже", 11, False),
    ("в следующем расчётном периоде.", 11, False),
    ("", 11, False),
    ("Своевременно переданные показания — это ответственность каждого", 11, False),
    ("жителя, что позволяет минимизировать расход по ОДН. Благодарю всех", 11, False),
    ("за понимание и участие в процессе сбора показаний по нашему дому.", 11, False),
    ("", 11, False),
    ("С уважением, председатель совета дома", 11, False),
)

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
DELIVERY_ROW_HEIGHT = 15
GAP_ROW_HEIGHT = 8
COVER_ROW_HEIGHT = 16
COVER_GAP_HEIGHT = 9

_thick = Side(style="medium")
CELL_BORDER = Border(left=_thick, right=_thick, top=_thick, bottom=_thick)
CUT_LINE = Border(bottom=Side(style="dashed"))


def generate_blanks(conn, out_path: Path,
                    numbers: list[str] | None = None) -> Path:
    """Книга с бланками: по одному на квартиру, два-три бланка на лист А4.

    Месяц на бланке не печатается: бланки раздают пачкой вперёд, а период
    житель вписывает сам, когда садится заполнять.
    """
    from database import repository

    apartments = [a for a in repository.list_apartments(conn)
                  if a["type"] == "residential"]
    if numbers:
        wanted = {str(n).strip() for n in numbers}
        apartments = [a for a in apartments if a["number"] in wanted]

    wb = Workbook()
    _draw_cover(wb.active)

    ws = wb.create_sheet("Бланки")
    _setup_sheet(ws)

    row = 1
    used = 0.0
    for apartment in apartments:
        meters = [m["kind"] for m in repository.meters_for_apartment(conn, apartment["id"])]
        height = _blank_height(meters)
        if used and used + height > PAGE_BUDGET_PT:
            ws.row_breaks.append(Break(id=row - 1))   # бланк не режем пополам
            used = 0.0
        row = _draw_blank(ws, row, apartment["number"], meters)
        used += height

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def _draw_cover(ws) -> None:
    """Лист «Памятка» — печатается и выдаётся вместе с бланком.

    Отдельным листом, а не страницей среди бланков: памятка нужна в
    нескольких экземплярах, а бланки — по одному на квартиру.
    """
    ws.title = "Памятка"
    last_col = 1 + DIGIT_CELLS + 1
    ws.column_dimensions["A"].width = LABEL_WIDTH
    for col in range(2, last_col + 1):
        ws.column_dimensions[get_column_letter(col)].width = DIGIT_WIDTH

    for i, (text, size, bold) in enumerate(COVER_LINES, start=1):
        ws.merge_cells(start_row=i, start_column=1, end_row=i, end_column=last_col)
        cell = ws.cell(row=i, column=1, value=text or None)
        cell.font = Font(size=size, bold=bold)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[i].height = (COVER_ROW_HEIGHT if text
                                       else COVER_GAP_HEIGHT)

    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1        # памятка всегда на одном листе
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_area = f"A1:{get_column_letter(last_col)}{len(COVER_LINES)}"
    ws.page_margins.left = 0.6
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.4


def _meter_rows(meters: list[str]) -> int:
    """Сколько строк с клетками будет на бланке (с учётом строки суммы ГВС)."""
    rows = sum(1 for kind in METER_ORDER if kind in meters)
    return rows + (1 if "hws_kitchen" in meters else 0)


def _blank_height(meters: list[str]) -> float:
    return (TITLE_ROW_HEIGHT + NUMBER_ROW_HEIGHT
            + _meter_rows(meters) * DIGIT_ROW_HEIGHT
            + 2 * TEXT_ROW_HEIGHT
            + len(DELIVERY_LINES) * DELIVERY_ROW_HEIGHT
            + 2 * GAP_ROW_HEIGHT)


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


def _draw_blank(ws, row: int, number: str, meters: list[str]) -> int:
    """Рисует один бланк с строки row. Возвращает строку, с которой начать следующий."""
    last_col = 1 + DIGIT_CELLS + 1

    row = _text_row(ws, row, "ПОКАЗАНИЯ СЧЁТЧИКОВ", last_col,
                    Font(bold=True, size=13), TITLE_ROW_HEIGHT, "center")

    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
    flat = ws.cell(row=row, column=1, value=f"Кв. {number}")
    flat.font = Font(bold=True, size=22)
    flat.alignment = Alignment(horizontal="left", vertical="center")
    ws.merge_cells(start_row=row, start_column=4, end_row=row, end_column=last_col)
    period = ws.cell(row=row, column=4, value="Период: __________________")
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
    row = _text_row(ws, row, "Дата ___________   Подпись ___________",
                    last_col, Font(size=11), TEXT_ROW_HEIGHT, "left")
    for i, line in enumerate(DELIVERY_LINES):
        row = _text_row(ws, row, line, last_col,
                        Font(size=9, bold=i == 0), DELIVERY_ROW_HEIGHT, "left")

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
