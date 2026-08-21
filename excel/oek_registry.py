"""Заполнение реестра ОЭК показаниями электросчётчиков.

Ресурсник (ОЭК) присылает книгу «Реестр индивидуальных приборов учета» —
по листу на услугу: электроэнергия, горячая вода, холодная вода. Бот
оставляет только лист по электроэнергии (воду мы не заполняем) и
проставляет в нём текущие показания напротив каждой квартиры.

Форму ресурсник меняет от периода к периоду, поэтому колонки ищутся по
заголовкам, а не по буквам: «Квартира», «Текущие показания … день»,
«Дата снятия показания». Если заголовки не нашлись — модуль честно падает
с OekFormatError, а не портит файл молча.

Формат файла сохраняется: .xls остаётся .xls (xlrd + xlutils/xlwt),
.xlsx остаётся .xlsx (openpyxl). Оформление шаблона не трогаем — пишем
значения стилем той ячейки, которая уже стоит в шаблоне.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

# Ищем шапку в первых строках: выше неё только реквизиты договора
HEADER_SEARCH_ROWS = 40
# Столько подряд пустых строк считаем концом таблицы (в реестре бывают
# разрывы между округами)
MAX_BLANK_ROWS = 15

# «Дата снятия показания» — в привычном виде 20.08.2026. В шаблоне ОЭК стоит
# американский формат m/d/yy (8/20/26), поэтому свой формат задаём явно.
# Пишем именно дату, без времени: час передачи ресурснику не нужен.
DATE_FORMAT = "DD.MM.YYYY"

XLS_SUFFIXES = (".xls",)
XLSX_SUFFIXES = (".xlsx", ".xlsm")
TEMPLATE_SUFFIXES = XLS_SUFFIXES + XLSX_SUFFIXES

# Лист по воде: его выбрасываем целиком
WATER_HINTS = ("горяч", "холод", "гвс", "хвс", "вода", "вод.")
# Лист по электроэнергии: его и заполняем. Проверяем «электроэнерг», а не
# «электро»: в шапке каждого листа есть «Адрес электронной почты» — по нему
# лист по воде тоже считался бы электрическим.
ELECTRICITY_HINTS = ("электроэнерг", "электрическ", "эл.энерг", "эл. энерг",
                     "э/э", "квт")

MONTH_NUMBERS = {"январ": 1, "феврал": 2, "март": 3, "апрел": 4, "мая": 5,
                 "май": 5, "июн": 6, "июл": 7, "август": 8, "сентябр": 9,
                 "октябр": 10, "ноябр": 11, "декабр": 12}


class OekFormatError(Exception):
    """Шаблон ОЭК не удалось разобрать — форма изменилась сильнее, чем ожидалось."""


# ---------------------------------------------------------------------------
# Разбор шаблона
# ---------------------------------------------------------------------------

def _norm(value) -> str:
    """Заголовок к сравнимому виду: нижний регистр, без ё и лишних пробелов."""
    text = str(value if value is not None else "")
    text = text.replace("ё", "е").replace("Ё", "Е").lower()
    return " ".join(text.split())


def apartment_key(value) -> str:
    """Номер помещения из ячейки реестра: «кв. 07» и 7.0 -> «7».

    Пустая строка означает «это не строка с квартирой» — заголовок, итог
    или разрыв таблицы.
    """
    if value is None:
        return ""
    if isinstance(value, float) and value == int(value):
        value = int(value)
    text = str(value).strip()
    if not text:
        return ""
    low = _norm(text)
    if low in ("квартира", "итого", "всего", "№", "n"):
        return ""
    for prefix in ("квартира", "кв.", "кв "):
        if low.startswith(prefix):
            text = text[len(prefix):].strip()
            break
    text = text.strip()
    # «007» и «7» в реестре — одна и та же квартира
    return text.lstrip("0") if text.lstrip("0") else text


@dataclass(frozen=True)
class RegistryLayout:
    """Где в листе лежат нужные колонки. Индексы — от нуля."""
    header_row: int
    apartment_col: int
    reading_col: int
    date_col: int | None = None


class _Grid:
    """Единый доступ к листу: у xlrd и openpyxl разные API, логика — одна."""

    def __init__(self, name: str, nrows: int, ncols: int, reader):
        self.name = name
        self.nrows = nrows
        self.ncols = ncols
        self._reader = reader

    def value(self, row: int, col: int):
        return self._reader(row, col)

    def service_text(self) -> str:
        """Что написано в строке «Услуга: …» — по ней и различаем листы."""
        for row in range(min(HEADER_SEARCH_ROWS, self.nrows)):
            for col in range(min(3, self.ncols)):
                text = _norm(self.value(row, col))
                if text.startswith("услуга"):
                    return text.split(":", 1)[-1].strip()
        return ""


def sheet_role(grid: _Grid) -> str:
    """«electricity» | «water» | «other».

    Сначала смотрим строку «Услуга:» — она у ОЭК есть на каждом листе и
    называет услугу прямо. Если её убрали, судим по названию листа.
    """
    for haystack in (grid.service_text(), _norm(grid.name)):
        if not haystack:
            continue
        if any(hint in haystack for hint in WATER_HINTS):
            return "water"
        if any(hint in haystack for hint in ELECTRICITY_HINTS):
            return "electricity"
    return "other"


def _reading_column(headers: list[str]) -> int | None:
    """Колонка «Текущие показания».

    У ОЭК их три — день, ночь, полупик. Дом однотарифный: заполняем «день».
    Если ресурсник оставит одну колонку без зоны — берём её.
    """
    candidates = [i for i, h in enumerate(headers)
                  if "текущ" in h and "показани" in h]
    if not candidates:
        return None
    day = [i for i in candidates if "день" in headers[i] or "дневн" in headers[i]]
    if day:
        return day[0]
    plain = [i for i in candidates
             if not any(zone in headers[i]
                        for zone in ("ночь", "ночн", "полупик", "пик"))]
    return plain[0] if plain else candidates[0]


def find_layout(grid: _Grid) -> RegistryLayout:
    """Ищет строку шапки и нужные колонки. Бросает OekFormatError, если не нашла."""
    for row in range(min(grid.nrows, HEADER_SEARCH_ROWS)):
        headers = [_norm(grid.value(row, col)) for col in range(grid.ncols)]
        apartment = next((i for i, h in enumerate(headers)
                          if h.startswith("квартира") or h in ("кв.", "кв")), None)
        if apartment is None:
            continue
        reading = _reading_column(headers)
        if reading is None:
            continue
        date_col = next((i for i, h in enumerate(headers)
                         if "дата" in h and "снят" in h), None)
        return RegistryLayout(header_row=row, apartment_col=apartment,
                              reading_col=reading, date_col=date_col)
    raise OekFormatError(
        "В листе не нашлась шапка реестра: нужны колонки «Квартира» и "
        "«Текущие показания». Похоже, ОЭК прислал другую форму — "
        "пришлите файл, и форму поправим.")


def data_rows(grid: _Grid, layout: RegistryLayout) -> list[tuple[int, str]]:
    """Строки с квартирами: [(индекс строки, номер квартиры)]."""
    rows: list[tuple[int, str]] = []
    blanks = 0
    for row in range(layout.header_row + 1, grid.nrows):
        key = apartment_key(grid.value(row, layout.apartment_col))
        if not key:
            blanks += 1
            if blanks >= MAX_BLANK_ROWS:
                break
            continue
        blanks = 0
        rows.append((row, key))
    return rows


def template_period(grid: _Grid) -> str:
    """Период из шапки шаблона («за август   2026» -> «2026-08»), '' если не разобрали."""
    for row in range(min(grid.nrows, HEADER_SEARCH_ROWS)):
        text = _norm(grid.value(row, 0))
        if not text.startswith("за "):
            continue
        month = next((num for stem, num in MONTH_NUMBERS.items()
                      if stem in text), None)
        year = next((int(word) for word in text.split()
                     if word.isdigit() and len(word) == 4), None)
        if month and year:
            return f"{year:04d}-{month:02d}"
    return ""


# ---------------------------------------------------------------------------
# Разведка шаблона: что бот в нём увидел
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TemplateInfo:
    """Как бот прочитал шаблон — показываем председателю при загрузке файла."""
    path: Path
    sheet: str
    period: str
    rows: int
    dropped_sheets: list[str]
    reading_header: str
    date_header: str


def open_grids(path: Path) -> list[_Grid]:
    """Листы книги в едином виде — .xls через xlrd, .xlsx через openpyxl."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in XLS_SUFFIXES:
        import xlrd
        book = xlrd.open_workbook(path)
        return [_xls_grid(book.sheet_by_index(i)) for i in range(book.nsheets)]
    if suffix in XLSX_SUFFIXES:
        from openpyxl import load_workbook
        book = load_workbook(path, data_only=True)
        return [_xlsx_grid(book[name]) for name in book.sheetnames]
    raise OekFormatError(
        f"Не умею читать «{path.name}». Реестр ОЭК приходит в .xls или .xlsx.")


def inspect_template(path: Path, drop_water_sheets: bool = True) -> TemplateInfo:
    """Разбирает шаблон, ничего не записывая. Бросает OekFormatError."""
    path = Path(path)
    grids = open_grids(path)
    target, dropped = _choose_sheets(grids, drop_water_sheets)
    layout = find_layout(target)
    header = [str(target.value(layout.header_row, col) or "").strip()
              for col in range(target.ncols)]
    return TemplateInfo(
        path=path, sheet=target.name, period=template_period(target),
        rows=len(data_rows(target, layout)), dropped_sheets=dropped,
        reading_header=header[layout.reading_col],
        date_header=header[layout.date_col] if layout.date_col is not None else "",
    )


# ---------------------------------------------------------------------------
# Результат заполнения
# ---------------------------------------------------------------------------

@dataclass
class OekResult:
    """Что получилось: файл и расхождения, которые стоит показать председателю."""
    path: Path
    template: Path
    sheet: str
    template_period: str = ""
    filled: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    not_in_registry: list[str] = field(default_factory=list)
    dropped_sheets: list[str] = field(default_factory=list)
    date_written: bool = False

    @property
    def rows_total(self) -> int:
        return len(self.filled) + len(self.empty) + len(self.unknown)

    def summary(self, period_name: str = "") -> str:
        """Короткий отчёт для сообщения в Telegram."""
        head = "📨 <b>Реестр ОЭК</b>"
        if period_name:
            head += f" — {period_name}"
        lines = [head, "",
                 f"Заполнено показаний: {len(self.filled)} из {self.rows_total}"]
        if self.empty:
            lines.append(f"Не передали: {_join(self.empty)}")
        if self.unknown:
            lines.append(f"Строки реестра без квартиры в базе: {_join(self.unknown)}")
        if self.not_in_registry:
            lines.append("Показания есть, строки в реестре нет: "
                         f"{_join(self.not_in_registry)}")
        if self.dropped_sheets:
            lines.append("Убраны листы: " + ", ".join(self.dropped_sheets))
        return "\n".join(lines)


def _join(values: list[str], limit: int = 25) -> str:
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f" … (всего {len(values)})"


# ---------------------------------------------------------------------------
# Заполнение
# ---------------------------------------------------------------------------

def _as_number(value: float) -> float | int:
    """Показание в реестр: 31668.0 -> 31668, дробное оставляем как есть."""
    value = round(float(value), 3)
    return int(value) if value == int(value) else value


def fill_registry(template: Path, readings: dict[str, float], out_path: Path,
                  taken_on: date | None = None,
                  known_apartments: set[str] | None = None,
                  drop_water_sheets: bool = True) -> OekResult:
    """Заполняет реестр ОЭК и сохраняет копию в out_path. Шаблон не меняется.

    readings          — {номер помещения: показание} по электроэнергии;
    taken_on          — дата снятия показаний (в колонку «Дата снятия»);
    known_apartments  — номера из нашего справочника: строки реестра, которых
                        там нет, попадут в отчёт отдельно, а не в «не передали».
    """
    template = Path(template)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    suffix = template.suffix.lower()
    if suffix in XLS_SUFFIXES:
        return _fill_xls(template, readings, out_path, taken_on,
                         known_apartments, drop_water_sheets)
    if suffix in XLSX_SUFFIXES:
        return _fill_xlsx(template, readings, out_path, taken_on,
                          known_apartments, drop_water_sheets)
    raise OekFormatError(
        f"Не умею читать «{template.name}». Реестр ОЭК приходит в .xls или .xlsx.")


def _fill_xls(template: Path, readings: dict[str, float], out_path: Path,
              taken_on: date | None, known: set[str] | None,
              drop_water: bool) -> OekResult:
    import copy

    import xlrd
    from xlutils.filter import XLRDReader, XLWTWriter, process

    book = xlrd.open_workbook(template, formatting_info=True)
    grids = [_xls_grid(book.sheet_by_index(i)) for i in range(book.nsheets)]
    target, dropped = _choose_sheets(grids, drop_water)
    layout = find_layout(target)
    rows = data_rows(target, layout)

    writer = XLWTWriter()
    process(XLRDReader(book, template.name), writer)
    out_book = writer.output[0][1]
    styles = writer.style_list

    _drop_xls_sheets(out_book, dropped)
    names = [sheet.name for sheet in _xls_sheets(out_book)]
    out_sheet = out_book.get_sheet(names.index(target.name))
    read_sheet = book.sheet_by_name(target.name)

    write_date = bool(taken_on is not None and layout.date_col is not None
                      and rows)
    if write_date:
        # Оформление ячейки берём из шаблона, а формат числа задаём свой:
        # у ОЭК в колонке стоит американское «m/d/yy» (8/20/26), читать реестр
        # с такими датами неудобно. copy — поверхностная: шрифт и рамки те же
        # объекты, меняем только формат, и стиль один на всю колонку.
        date_style = copy.copy(
            styles[read_sheet.cell_xf_index(rows[0][0], layout.date_col)])
        date_style.num_format_str = DATE_FORMAT

    result = _build_result(template, out_path, target.name, dropped,
                           readings, rows, known)
    result.template_period = template_period(target)
    for row, key in rows:
        value = readings.get(key)
        if value is None:
            continue
        style = styles[read_sheet.cell_xf_index(row, layout.reading_col)]
        out_sheet.write(row, layout.reading_col, _as_number(value), style)
        if write_date:
            out_sheet.write(row, layout.date_col, taken_on, date_style)
            result.date_written = True

    out_book.save(str(out_path))
    return result


def _fill_xlsx(template: Path, readings: dict[str, float], out_path: Path,
               taken_on: date | None, known: set[str] | None,
               drop_water: bool) -> OekResult:
    from openpyxl import load_workbook

    # Пишем в копию: openpyxl сохраняет книгу целиком, шаблон должен остаться
    shutil.copyfile(template, out_path)
    book = load_workbook(out_path)
    grids = [_xlsx_grid(book[name]) for name in book.sheetnames]
    target, dropped = _choose_sheets(grids, drop_water)
    layout = find_layout(target)
    rows = data_rows(target, layout)

    sheet = book[target.name]
    result = _build_result(template, out_path, target.name, dropped,
                           readings, rows, known)
    result.template_period = template_period(target)
    for row, key in rows:
        value = readings.get(key)
        if value is None:
            continue
        sheet.cell(row=row + 1, column=layout.reading_col + 1,
                   value=_as_number(value))
        if taken_on is not None and layout.date_col is not None:
            cell = sheet.cell(row=row + 1, column=layout.date_col + 1)
            cell.value = taken_on            # только дата, без времени
            cell.number_format = DATE_FORMAT
            result.date_written = True

    for name in dropped:
        del book[name]
    book.save(out_path)
    return result


# ---------------------------------------------------------------------------
# Вспомогательное
# ---------------------------------------------------------------------------

def _xls_grid(sheet) -> _Grid:
    return _Grid(sheet.name, sheet.nrows, sheet.ncols,
                 lambda r, c, s=sheet: s.cell_value(r, c))


def _xlsx_grid(sheet) -> _Grid:
    return _Grid(sheet.title, sheet.max_row, sheet.max_column,
                 lambda r, c, s=sheet: s.cell(row=r + 1, column=c + 1).value)


def _choose_sheets(grids: list[_Grid], drop_water: bool) -> tuple[_Grid, list[str]]:
    """Возвращает лист по электроэнергии и имена листов, которые надо убрать."""
    roles = {grid.name: sheet_role(grid) for grid in grids}
    target = next((g for g in grids if roles[g.name] == "electricity"), None)
    if target is None:
        if len(grids) == 1:
            # Ресурсник прислал единственный лист без слова «электроэнергия» —
            # заполнять всё равно нечего больше
            target = grids[0]
        else:
            raise OekFormatError(
                "В книге нет листа по электроэнергии. Листы: "
                + ", ".join(g.name for g in grids))
    dropped = [g.name for g in grids
               if drop_water and roles[g.name] == "water" and g.name != target.name]
    return target, dropped


def _build_result(template: Path, out_path: Path, sheet: str, dropped: list[str],
                  readings: dict[str, float], rows: list[tuple[int, str]],
                  known: set[str] | None) -> OekResult:
    """Раскладывает строки реестра на «заполнено / не передали / чужие»."""
    keys = [key for _, key in rows]
    in_registry = set(keys)
    result = OekResult(path=out_path, template=template, sheet=sheet,
                       dropped_sheets=dropped)
    for key in keys:
        if readings.get(key) is not None:
            result.filled.append(key)
        elif known is not None and key not in known:
            # Строка в реестре есть, а такого помещения в справочнике бота нет:
            # его не «забыли передать» — за него никто и не отвечает
            result.unknown.append(key)
        else:
            result.empty.append(key)
    # Нежилые помещения и общедомовой прибор в реестр ОЭК не входят —
    # у них отдельный договор. Показания по ним остаются в ведомости.
    result.not_in_registry = [num for num in readings if num not in in_registry]
    return result


def _xls_sheets(book) -> list:
    """Список листов xlwt-книги. Публичного доступа у xlwt нет."""
    sheets = getattr(book, "_Workbook__worksheets", None)
    if sheets is None:                       # пригвождено версией в requirements
        raise OekFormatError(
            "Версия xlwt не даёт добраться до списка листов — "
            "проверьте requirements.txt (xlwt).")
    return sheets


def _drop_xls_sheets(book, names: list[str]) -> None:
    """Убирает листы из копии книги (у xlwt нет remove_sheet)."""
    if not names:
        return
    sheets = _xls_sheets(book)
    kept = [sheet for sheet in sheets if sheet.name not in names]
    if not kept:
        raise OekFormatError("После удаления листов книга осталась пустой.")
    sheets[:] = kept
    book._Workbook__active_sheet = 0
    for index, sheet in enumerate(kept):
        sheet.selected = index == 0
