"""Книга Excel «DH OS — Модуль "Сбор показаний"».

Формируется из базы данных (единого ядра системы) по кнопке председателя.
База остаётся источником истины: бот пишет показания в неё, а книга — это
рабочее представление, которое можно свободно открывать и править, ничего
не ломая.

Состав книги:
    Лист 1. Реестр квартир      — главный, по строке на квартиру
    Лист 2. Переданные показания — полная история передач
    Лист 3. Текущие показания    — последние значения по каждой квартире
    Лист 4. Контроль передачи    — ежедневная панель председателя
    Лист 5. Настройки            — справочники и правила проверки
"""
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from bot.config import config
from bot.services.reading_service import current_period, period_title
from database import repository
from database.models import DELTA_WARN_DEFAULT, DELTA_WARN_LIMITS, SOURCE_LABELS
from excel import style

SHEET_REGISTRY = "Реестр квартир"
SHEET_HISTORY = "Переданные показания"
SHEET_CURRENT = "Текущие показания"
SHEET_CONTROL = "Контроль передачи"
SHEET_SETTINGS = "Настройки"

# Лист 1: основные (A-L) и служебные (M-Q) колонки
REGISTRY_COLUMNS = [
    "№ квартиры", "Тип", "Telegram ID", "WhatsApp", "ХВС кухня", "ХВС сан.узел",
    "ГВС кухня", "ГВС ванна", "Электроэнергия", "Последняя передача", "Статус",
    "Примечание",
    # служебные — заполняет система
    "Username Telegram", "ФИО", "Дата регистрации", "Последний вход",
    "Способ передачи",
]
REGISTRY_WIDTHS = [12, 18, 14, 14, 12, 14, 12, 12, 15, 18, 16, 24,
                   18, 24, 18, 18, 18]
SERVICE_FIRST_COL = 13  # M — с неё начинаются служебные столбцы

HISTORY_COLUMNS = ["Дата", "Время", "Квартира", "ХВС кухня", "ХВС сан.узел",
                   "ГВС кухня", "ГВС ванна", "Электроэнергия", "Источник"]
HISTORY_WIDTHS = [12, 10, 12, 12, 14, 12, 12, 15, 18]

CURRENT_COLUMNS = ["№ квартиры", "Тип", "ХВС кухня", "ХВС сан.узел", "ГВС кухня",
                   "ГВС ванна", "Электроэнергия", "Период", "Обновлено", "Источник"]
CURRENT_WIDTHS = [12, 18, 12, 14, 12, 12, 15, 12, 18, 18]

# Соответствие приборов колонкам книги: у квартир с одним счётчиком
# ХВС попадает в «ХВС кухня», ГВС — в «ГВС кухня».
KIND_TO_COLUMN = {
    "cws_kitchen": "ХВС кухня", "cws": "ХВС кухня",
    "cws_bathroom": "ХВС сан.узел",
    "hws_kitchen": "ГВС кухня", "hws": "ГВС кухня",
    "hws_bathroom": "ГВС ванна",
    "electricity": "Электроэнергия",
}
METER_COLUMNS = ["ХВС кухня", "ХВС сан.узел", "ГВС кухня", "ГВС ванна", "Электроэнергия"]


def build_workbook(conn: sqlite3.Connection, out_path: Path,
                   period: str | None = None) -> Path:
    period = period or current_period()
    wb = Workbook()

    _sheet_registry(wb.active, conn, period)
    _sheet_history(wb.create_sheet(SHEET_HISTORY), conn)
    _sheet_current(wb.create_sheet(SHEET_CURRENT), conn)
    _sheet_control(wb.create_sheet(SHEET_CONTROL), conn, period)
    _sheet_settings(wb.create_sheet(SHEET_SETTINGS))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out_path)
    return out_path


# --------------------------------------------------------------------------
# Лист 1. Реестр квартир
# --------------------------------------------------------------------------

def _sheet_registry(ws, conn: sqlite3.Connection, period: str) -> None:
    ws.title = SHEET_REGISTRY
    ncols = len(REGISTRY_COLUMNS)

    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncols)
    title = ws.cell(row=1, column=1,
                    value=f"DH OS · Реестр квартир — {period_title(period)}")
    title.font = style.FONT_TITLE
    title.fill = style.FILL_TITLE
    title.alignment = style.CENTER
    ws.row_dimensions[1].height = 24

    for col, name in enumerate(REGISTRY_COLUMNS, start=1):
        ws.cell(row=2, column=col, value=name)
    style.style_header(ws, 2, ncols, REGISTRY_WIDTHS)

    submitted = repository.apartments_submitted(conn, period)
    current = _current_by_apartment(conn)

    row = 3
    for apt in repository.registry_rows(conn):
        # Факт передачи важнее регистрации: сдал — значит «Передал»
        if apt["number"] in submitted:
            status = style.STATUS_SUBMITTED
        elif apt["tg_id"] is None:
            status = style.STATUS_NO_TELEGRAM
        else:
            status = style.STATUS_NOT_SUBMITTED

        values = current.get(apt["number"], {})
        cells = [
            apt["number"],
            style.room_label(apt["rooms"], apt["type"]),
            apt["tg_id"] or "",
            "",  # WhatsApp — заполняется вручную
            values.get("ХВС кухня", ""),
            values.get("ХВС сан.узел", ""),
            values.get("ГВС кухня", ""),
            values.get("ГВС ванна", ""),
            values.get("Электроэнергия", ""),
            _short_dt(apt["last_submission"]),
            status,
            apt["note"] or "",
            f"@{apt['username']}" if apt["username"] else "",
            apt["full_name"] or "",
            _short_dt(apt["registered_at"]),
            _short_dt(apt["last_seen"]),
            SOURCE_LABELS.get(apt["last_source"], ""),
        ]

        fill = style.room_fill(apt["rooms"], apt["type"])
        for col, value in enumerate(cells, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = style.BORDER
            cell.alignment = style.LEFT if col in (12, 14) else style.CENTER
            if col == 2:
                cell.fill = fill                      # тип квартиры — цветом
            elif col == 11:
                cell.fill = style.status_fill(status)  # статус — цветом
            elif col >= SERVICE_FIRST_COL:
                cell.fill = style.FILL_SERVICE
                cell.protection = Protection(locked=True)
            else:
                cell.protection = Protection(locked=False)
        row += 1

    ws.freeze_panes = "C3"                       # закреплены шапка и номер квартиры
    ws.auto_filter.ref = f"A2:{get_column_letter(ncols)}{row - 1}"

    # Выпадающий список статусов из листа «Настройки»
    dv = DataValidation(type="list",
                        formula1=f"'{SHEET_SETTINGS}'!$A$3:$A$5", allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"K3:K{row - 1}")

    # Защищаем только служебные столбцы (остальные ячейки редактируются)
    ws.protection.enable()
    ws.protection.autoFilter = False
    ws.protection.sort = False


# --------------------------------------------------------------------------
# Лист 2. Переданные показания (история)
# --------------------------------------------------------------------------

def _sheet_history(ws, conn: sqlite3.Connection) -> None:
    for col, name in enumerate(HISTORY_COLUMNS, start=1):
        ws.cell(row=1, column=col, value=name)
    style.style_header(ws, 1, len(HISTORY_COLUMNS), HISTORY_WIDTHS)

    # Одна передача = все показания квартиры, записанные в один момент
    batches: dict[tuple, dict] = defaultdict(dict)
    order: list[tuple] = []
    for r in repository.all_readings(conn):
        key = (r["created_at"], r["apartment_number"], r["source"])
        if key not in batches:
            order.append(key)
        column = KIND_TO_COLUMN.get(r["kind"])
        if column:
            batches[key][column] = r["value"]

    row = 2
    for created_at, number, source in order:
        values = batches[(created_at, number, source)]
        day, time = _split_dt(created_at)
        cells = [day, time, number] + [values.get(c, "") for c in METER_COLUMNS] \
            + [SOURCE_LABELS.get(source, source)]
        for col, value in enumerate(cells, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = style.BORDER
            cell.alignment = style.CENTER
        row += 1

    ws.freeze_panes = "A2"
    if row > 2:
        ws.auto_filter.ref = f"A1:{get_column_letter(len(HISTORY_COLUMNS))}{row - 1}"


# --------------------------------------------------------------------------
# Лист 3. Текущие показания
# --------------------------------------------------------------------------

def _sheet_current(ws, conn: sqlite3.Connection) -> None:
    for col, name in enumerate(CURRENT_COLUMNS, start=1):
        ws.cell(row=1, column=col, value=name)
    style.style_header(ws, 1, len(CURRENT_COLUMNS), CURRENT_WIDTHS)

    latest: dict[str, dict] = defaultdict(dict)
    meta: dict[str, tuple] = {}
    for r in repository.current_readings_rows(conn):
        column = KIND_TO_COLUMN.get(r["kind"])
        if column:
            latest[r["apartment_number"]][column] = r["value"]
        prev = meta.get(r["apartment_number"])
        if prev is None or r["created_at"] > prev[1]:
            meta[r["apartment_number"]] = (r["period"], r["created_at"], r["source"])

    row = 2
    for apt in repository.registry_rows(conn):
        number = apt["number"]
        values = latest.get(number, {})
        period, created_at, source = meta.get(number, ("", "", ""))
        cells = [number, style.room_label(apt["rooms"], apt["type"])] \
            + [values.get(c, "") for c in METER_COLUMNS] \
            + [period, _short_dt(created_at), SOURCE_LABELS.get(source, "")]
        for col, value in enumerate(cells, start=1):
            cell = ws.cell(row=row, column=col, value=value)
            cell.border = style.BORDER
            cell.alignment = style.CENTER
            if col == 2:
                cell.fill = style.room_fill(apt["rooms"], apt["type"])
        row += 1

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(CURRENT_COLUMNS))}{row - 1}"


# --------------------------------------------------------------------------
# Лист 4. Контроль передачи (панель председателя)
# --------------------------------------------------------------------------

def _sheet_control(ws, conn: sqlite3.Connection, period: str) -> None:
    ws.column_dimensions["A"].width = 44
    ws.column_dimensions["B"].width = 16

    ws.merge_cells("A1:B1")
    title = ws.cell(row=1, column=1,
                    value=f"Контроль передачи — {period_title(period)}")
    title.font = style.FONT_TITLE
    title.fill = style.FILL_TITLE
    title.alignment = style.CENTER
    ws.row_dimensions[1].height = 24

    reg = f"'{SHEET_REGISTRY}'"
    last_row = len(repository.registry_rows(conn)) + 2
    status_range = f"{reg}!$K$3:$K${last_row}"
    tg_range = f"{reg}!$C$3:$C${last_row}"
    source_range = f"{reg}!$Q$3:$Q${last_row}"

    rows = [
        ("Всего квартир", f"=COUNTA({reg}!$A$3:$A${last_row})"),
        ("Передали показания", f'=COUNTIF({status_range},"{style.STATUS_SUBMITTED}")'),
        ("Не передали", "=B3-B4"),
        ("Процент передачи", "=IF(B3=0,0,B4/B3)"),
        ("Зарегистрированы в Telegram", f"=COUNT({tg_range})"),
        ("Квартиры без регистрации в Telegram", f"=B3-COUNT({tg_range})"),
        ("Передают через WhatsApp", f'=COUNTIF({source_range},"WhatsApp")'),
    ]

    row = 3
    for label, formula in rows:
        name_cell = ws.cell(row=row, column=1, value=label)
        name_cell.font = style.FONT_BOLD
        name_cell.border = style.BORDER
        name_cell.alignment = style.LEFT
        value_cell = ws.cell(row=row, column=2, value=formula)
        value_cell.border = style.BORDER
        value_cell.alignment = style.CENTER
        if label == "Процент передачи":
            value_cell.number_format = "0%"
        elif label == "Передали показания":
            value_cell.fill = style.FILL_SUBMITTED
        elif label == "Не передали":
            value_cell.fill = style.FILL_NOT_SUBMITTED
        elif label.startswith("Квартиры без") or label.startswith("Передают через"):
            value_cell.fill = style.FILL_NO_TELEGRAM
        row += 1

    note = ws.cell(row=row + 1, column=1,
                   value="Значения пересчитываются автоматически по листу «Реестр квартир».")
    note.alignment = style.LEFT

    legend_row = row + 3
    ws.cell(row=legend_row, column=1, value="Цветовая схема DH OS").font = style.FONT_BOLD
    legend = [
        ("1-комнатные", style.FILL_1_ROOM),
        ("2-комнатные", style.FILL_2_ROOM),
        ("3-комнатные", style.FILL_3_ROOM),
        ("Передали показания", style.FILL_SUBMITTED),
        ("Не передали", style.FILL_NOT_SUBMITTED),
        ("Не зарегистрированы в Telegram", style.FILL_NO_TELEGRAM),
    ]
    for i, (label, fill) in enumerate(legend, start=legend_row + 1):
        cell = ws.cell(row=i, column=1, value=label)
        cell.fill = fill
        cell.border = style.BORDER
        cell.alignment = style.LEFT


# --------------------------------------------------------------------------
# Лист 5. Настройки (справочники)
# --------------------------------------------------------------------------

def _sheet_settings(ws) -> None:
    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 30
    ws.column_dimensions["D"].width = 18

    ws.merge_cells("A1:D1")
    title = ws.cell(row=1, column=1, value="Справочники и правила проверки DH OS")
    title.font = style.FONT_TITLE
    title.fill = style.FILL_TITLE
    title.alignment = style.CENTER

    for col, name in enumerate(["Статусы", "Типы квартир", "Способ передачи",
                                "Правило"], start=1):
        ws.cell(row=2, column=col, value=name)
    style.style_header(ws, 2, 4, [26, 26, 30, 18])

    for i, value in enumerate(style.STATUSES, start=3):
        ws.cell(row=i, column=1, value=value).border = style.BORDER
    for i, value in enumerate(style.ROOM_TYPES, start=3):
        ws.cell(row=i, column=2, value=value).border = style.BORDER
    for i, value in enumerate(style.SOURCES, start=3):
        ws.cell(row=i, column=3, value=value).border = style.BORDER

    rules = [
        ("Период приёма показаний, с",  config.readings_day_start),
        ("Период приёма показаний, по", config.readings_day_end),
        ("Дни напоминаний", ", ".join(map(str, config.reminder_days))),
        ("Порог расхода воды за месяц, м³", DELTA_WARN_DEFAULT),
        ("Порог расхода электроэнергии, кВт·ч",
         DELTA_WARN_LIMITS.get("electricity", "")),
        ("Показание меньше предыдущего", "не принимается"),
    ]
    row = 8
    ws.cell(row=row, column=1, value="Правила проверки").font = style.FONT_BOLD
    row += 1
    for label, value in rules:
        ws.cell(row=row, column=1, value=label).border = style.BORDER
        cell = ws.cell(row=row, column=2, value=value)
        cell.border = style.BORDER
        cell.alignment = style.CENTER
        row += 1

    ws.cell(row=row + 1, column=1,
            value="Изменения правил вносятся в настройках системы (.env), "
                  "здесь показаны действующие значения.")


# --------------------------------------------------------------------------

def _current_by_apartment(conn: sqlite3.Connection) -> dict[str, dict]:
    result: dict[str, dict] = defaultdict(dict)
    for r in repository.current_readings_rows(conn):
        column = KIND_TO_COLUMN.get(r["kind"])
        if column:
            result[r["apartment_number"]][column] = r["value"]
    return result


def _short_dt(value: str | None) -> str:
    """'2026-07-28 03:59:12' -> '28.07.2026 03:59'"""
    if not value:
        return ""
    try:
        day, time = value.split(" ")
        y, m, d = day.split("-")
        return f"{d}.{m}.{y} {time[:5]}"
    except (ValueError, AttributeError):
        return value


def _split_dt(value: str | None) -> tuple[str, str]:
    if not value:
        return "", ""
    parts = value.split(" ")
    day = parts[0]
    try:
        y, m, d = day.split("-")
        day = f"{d}.{m}.{y}"
    except ValueError:
        pass
    return day, parts[1][:5] if len(parts) > 1 else ""


def generate_workbook(period: str | None = None) -> Path:
    """Собирает книгу из базы и возвращает путь к файлу."""
    period = period or current_period()
    conn = repository.connect()
    try:
        out = config.reports_dir / f"DH_OS_sbor_pokazaniy_{period}.xlsx"
        build_workbook(conn, out, period)
        repository.save_report(conn, period, str(out))
    finally:
        conn.close()
    return out


if __name__ == "__main__":
    print(f"Книга сохранена: {generate_workbook()}")
