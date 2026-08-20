"""Выгрузка ведомости передачи показаний в Excel (.xlsx)."""
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from bot.services.report_service import STATEMENT_COLUMNS, Statement
from database.models import LATE_NOTE

# В печатной колонке пометка короткая — длинная фраза переносилась
# на три строки и сдвигала границу листа. Расшифровка под таблицей.
LATE_MARK = "После срока"

# «Электроэнергия» — единственное слово шире своей колонки: перенос рвал его
# посреди слова («Электроэнерги/я»). В шапке печатаем сокращение.
PRINT_HEADERS = {"Электроэнергия": "Эл. энергия"}

# Длинные названия в печатной форме сокращаем — колонка «Кв.» узкая
SHORT_NAMES = {
    "Нежилое помещение №1": "Нежилое №1",
    "Нежилое помещение №2": "Нежилое №2",
    "Общедомовой прибор учета": "Общедомовой ПУ",
}

# Ширины подобраны так, чтобы таблица заполняла лист А4 почти целиком:
# лист вписывается по ширине, и чем уже таблица, тем крупнее печатаются цифры.
# Первая колонка узкая — в ней в основном номера квартир, а длинные подписи
# («Нежилое помещение №1», «Общедомовой прибор учета») переносятся по строкам.
COLUMN_WIDTHS = [13, 3.5, 14, 11, 11, 12, 11, 11, 13]
WRAP_COLUMNS = {1, 9}  # «Кв.» и «Примечание» — с переносом текста

# Размер шрифта ведомости: читаемый на распечатанном листе
FONT_SIZE = 14

# Разбивка по листам жёсткая: нежилые, общедомовой прибор и кв. 1–40 на первом
# листе, кв. 41–80 на втором. Поэтому высоты строк заданы явно — иначе одна
# строка с переносом текста сдвигает границу, и последние квартиры уезжают.
FLATS_ON_FIRST_PAGE = 40
FLAT_ROW_HEIGHT = 21      # хватает для шрифта 14 и держит 43 строки на листе
SPECIAL_ROW_HEIGHT = 44   # нежилые и ОДПУ: подпись переносится на две строки
TITLE_ROW_HEIGHT = 20
SPACER_ROW_HEIGHT = 6
HEADER_ROW_HEIGHT = 34

# Шапку и примечание печатаем мельче: место нужно цифрам, а не подписям.
# 10 пунктов — чтобы «Электроэнергия» уместилась в колонку целиком, а не
# переносилась посреди слова («Электроэнер/гия»).
HEADER_FONT_SIZE = 10
NOTE_FONT_SIZE = 12

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
        cell = ws.cell(row=3, column=col, value=PRINT_HEADERS.get(name, name))
        cell.font = Font(bold=True, size=HEADER_FONT_SIZE)
        cell.fill = HEADER_FILL
        cell.border = BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center",
                                   wrap_text=True)
        ws.column_dimensions[get_column_letter(col)].width = COLUMN_WIDTHS[col - 1]
    ws.row_dimensions[1].height = TITLE_ROW_HEIGHT
    ws.row_dimensions[2].height = SPACER_ROW_HEIGHT
    ws.row_dimensions[3].height = HEADER_ROW_HEIGHT
    body_font = Font(size=FONT_SIZE)
    flats_seen = 0
    break_row = None
    for i, row in enumerate(statement.rows, start=4):
        cells = row.as_cells()
        cells[0] = SHORT_NAMES.get(cells[0], cells[0])
        cells[-1] = _short_note(cells[-1])
        for col, value in enumerate(cells, start=1):
            cell = ws.cell(row=i, column=col, value=value)
            cell.border = BORDER
            cell.font = body_font
            if col in WRAP_COLUMNS:
                # Номера квартир — по центру колонки: у края их неудобно читать
                # при печати. Примечание оставляем по левому краю — это текст.
                cell.alignment = Alignment(
                    horizontal="center" if col == 1 else "left",
                    vertical="center", wrap_text=True)
                # «Кв.» и «Примечание» — мельче: длинные подписи («Общедомовой
                # ПУ») должны переноситься по словам, а не разрываться внутри
                cell.font = Font(size=NOTE_FONT_SIZE)
            else:
                cell.alignment = Alignment(horizontal="center", vertical="center")
        if str(row.number).strip().isdigit():
            flats_seen += 1
            if flats_seen == FLATS_ON_FIRST_PAGE:
                break_row = i          # после этой квартиры — второй лист
            ws.row_dimensions[i].height = FLAT_ROW_HEIGHT
        else:
            ws.row_dimensions[i].height = SPECIAL_ROW_HEIGHT

    footer_row = len(statement.rows) + 5
    if any(LATE_NOTE in row.note for row in statement.rows):
        legend = ws.cell(row=footer_row - 1, column=1,
                         value=f"«{LATE_MARK}» — {LATE_NOTE.lower()}: "
                               "будут учтены в следующем расчётном периоде")
        legend.font = Font(size=FONT_SIZE - 2, italic=True)

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
    ws.page_margins.top = 0.3
    ws.page_margins.bottom = 0.3
    ws.page_margins.header = 0.0
    ws.page_margins.footer = 0.2

    ws.freeze_panes = "A4"               # при просмотре на экране шапка закреплена
    ws.oddFooter.right.text = "Стр. &P из &N"


def _short_note(note: str) -> str:
    """Длинную пометку об опоздании в печатной форме сокращаем."""
    if not note:
        return note
    return note.replace(LATE_NOTE, LATE_MARK)
