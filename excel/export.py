"""Выгрузка ведомости передачи показаний в Excel (.xlsx)."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from bot.services.report_service import STATEMENT_COLUMNS, Statement

COLUMN_WIDTHS = [22, 5, 15, 11, 11, 13, 11, 11, 22]

_thin = Side(style="thin")
BORDER = Border(left=_thin, right=_thin, top=_thin, bottom=_thin)
HEADER_FILL = PatternFill("solid", fgColor="DDEBF7")


def export_statement(statement: Statement, period_name: str, out_path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Ведомость"

    ncols = len(STATEMENT_COLUMNS)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    title = ws.cell(row=1, column=1,
                    value=f"Ведомость передачи показаний за {period_name}")
    title.font = Font(bold=True, size=14)
    title.alignment = Alignment(horizontal="center")

    for col, name in enumerate(STATEMENT_COLUMNS, start=1):
        cell = ws.cell(row=3, column=col, value=name)
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = COLUMN_WIDTHS[col - 1]

    for i, row in enumerate(statement.rows, start=4):
        for col, value in enumerate(row.as_cells(), start=1):
            cell = ws.cell(row=i, column=col, value=value)
            cell.border = BORDER
            if col in (1, 9):
                cell.alignment = Alignment(horizontal="left")
            else:
                cell.alignment = Alignment(horizontal="center")

    footer_row = len(statement.rows) + 5
    ws.cell(row=footer_row, column=1,
            value=f"Сдали показания: {statement.submitted_count} из {statement.total_count}")
    ws.cell(row=footer_row + 2, column=1, value="Председатель: ______________________")

    _setup_print(ws, last_row=footer_row + 2, ncols=ncols)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


def _setup_print(ws, last_row: int, ncols: int) -> None:
    """Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждой странице."""
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0        # по высоте — сколько нужно страниц
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    ws.print_title_rows = "3:3"          # шапка таблицы повторяется на каждом листе
    ws.print_area = f"A1:{get_column_letter(ncols)}{last_row}"

    ws.page_margins.left = 0.4
    ws.page_margins.right = 0.4
    ws.page_margins.top = 0.5
    ws.page_margins.bottom = 0.5

    ws.freeze_panes = "A4"               # при просмотре на экране шапка закреплена
    ws.oddFooter.right.text = "Стр. &P из &N"
