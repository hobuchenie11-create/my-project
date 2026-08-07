"""Выгрузка ведомости передачи показаний в Excel (.xlsx)."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from bot.services.report_service import STATEMENT_COLUMNS, Statement

# Первая колонка узкая — в ней в основном номера квартир, а длинные подписи
# («Нежилое помещение №1», «Общедомовой прибор учета») переносятся по строкам.
# Освободившееся место отдано колонкам с показаниями и примечанием.
COLUMN_WIDTHS = [13, 4, 17, 12, 12, 14, 12, 12, 28]
WRAP_COLUMNS = {1, 9}  # «Кв.» и «Примечание» — с переносом текста

# Размер шрифта ведомости: читаемый на распечатанном листе
FONT_SIZE = 12
FLATS_ON_FIRST_PAGE = 40  # столько квартир на первом листе, остальные — на втором
FLAT_ROW_HEIGHT = 22      # строки квартир повыше — лист заполнен, удобно писать от руки

_thin = Side(style="thin")
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)
HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")


def export_statement(statement: Statement, period_name: str, out_path: Path) -> Path:
    """Отдельный файл ведомости — его председатель отправляет ресурсникам."""
    wb = Workbook()
    ws = wb.active
    fill_statement_sheet(ws, statement, period_name)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def fill_statement_sheet(ws, statement: Statement, period_name: str) -> None:
    """Заполняет готовый лист ведомостью — используется и в отдельном файле,
    и как лист внутри книги DH OS."""
    ws.title = "Ведомость"

    ncols = len(STATEMENT_COLUMNS)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    title = ws.cell(row=1, column=1,
                    value=f"Ведомость передачи показаний за {period_name}")
    title.font = Font(bold=True, size=FONT_SIZE + 3)
    title.alignment = Alignment(horizontal="center")

    for col, name in enumerate(STATEMENT_COLUMNS, start=1):
        cell = ws.cell(row=3, column=col, value=name)
        cell.font = Font(bold=True, size=FONT_SIZE)
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = COLUMN_WIDTHS[col - 1]
    ws.row_dimensions[3].height = 34

    # Высоту строк не задаём: Excel сам растянет те, где текст переносится
    # («Нежилое помещение №1», длинные примечания), иначе он обрезался бы.
    body_font = Font(size=FONT_SIZE)
    flats_seen = 0
    break_row = None
    for i, row in enumerate(statement.rows, start=4):
        for col, value in enumerate(row.as_cells(), start=1):
            cell = ws.cell(row=i, column=col, value=value)
            cell.border = BORDER
            cell.font = body_font
            if col in WRAP_COLUMNS:
                cell.alignment = Alignment(horizontal="left", vertical="center",
                                           wrap_text=True)
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")
        if str(row.number).strip().isdigit():
            flats_seen += 1
            if flats_seen == FLATS_ON_FIRST_PAGE:
                break_row = i          # после этой квартиры — второй лист
            # Высоту задаём только там, где текст заведомо в одну строку;
            # строкам с переносом (нежилые, длинные примечания) — авто.
            if len(row.note) < 28:
                ws.row_dimensions[i].height = FLAT_ROW_HEIGHT

    footer_row = len(statement.rows) + 5
    total = ws.cell(row=footer_row, column=1,
                    value=f"Сдали показания: {statement.submitted_count} "
                          f"из {statement.total_count}")
    total.font = Font(size=FONT_SIZE, bold=True)
    sign = ws.cell(row=footer_row + 2, column=1,
                   value="Председатель: ______________________")
    sign.font = body_font

    _setup_print(ws, last_row=footer_row + 2, ncols=ncols,
                 page_break_row=break_row)


def _setup_print(ws, last_row: int, ncols: int,
                 page_break_row: int | None = None) -> None:
    """Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждом листе."""
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    # По высоте не сжимаем: ведомость печатается крупным шрифтом на двух листах,
    # так её удобнее читать и заполнять от руки.
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.print_title_rows = "3:3"          # шапка таблицы повторяется на каждом листе
    ws.print_area = f"A1:{get_column_letter(ncols)}{last_row}"
    if page_break_row and page_break_row < last_row:
        ws.row_breaks.append(Break(id=page_break_row))

    ws.page_margins.left = 0.4
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    ws.freeze_panes = "A4"               # при просмотре на экране шапка закреплена
    ws.oddFooter.right.text = "Стр. &P из &N"
