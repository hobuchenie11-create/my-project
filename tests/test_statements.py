"""Печатные ведомости: для ресурсоснабжающих организаций и непередавших."""
import pytest
from openpyxl import load_workbook

from bot.services.reading_service import save_reading
from bot.services.report_service import build_statement
from database import repository
from database.init_db import init_db
from excel.export import export_statement
from reports.debtors_statement import build_debtors_statement


@pytest.fixture()
def db(tmp_path):
    path = tmp_path / "test.db"
    init_db(path, apartments_count=5, nonresidential_count=1)
    return path


def test_statement_lists_apartments_in_order(db, tmp_path):
    conn = repository.connect(db)
    try:
        statement = build_statement(conn, "2026-07")
    finally:
        conn.close()
    numbers = [r.number for r in statement.rows]
    # Нежилые помещения и общедомовой прибор — первыми, чтобы попадали на
    # первую страницу; затем квартиры строго по порядку.
    assert numbers[0] == "Нежилое помещение №1"
    assert numbers[1] == "Общедомовой прибор учета"
    assert numbers[2:7] == ["1", "2", "3", "4", "5"]


def test_statement_is_print_ready(db, tmp_path):
    conn = repository.connect(db)
    try:
        statement = build_statement(conn, "2026-07")
    finally:
        conn.close()
    out = export_statement(statement, "июль 2026", tmp_path / "v.xlsx")

    ws = load_workbook(out).active
    assert ws.page_setup.orientation == "portrait"
    assert ws.page_setup.fitToWidth == 1
    # По высоте не сжимаем — ведомость печатается крупным шрифтом на двух листах
    assert ws.page_setup.fitToHeight == 0
    assert ws.sheet_properties.pageSetUpPr.fitToPage is True
    assert ws.print_title_rows == "$3:$3"      # шапка повторяется на каждой странице
    assert ws.print_area is not None


def test_page_break_splits_flats_across_two_sheets(tmp_path):
    """В доме на 80 квартир ведомость печатается на двух листах: на первом —
    нежилые, общедомовой прибор и квартиры 1-40, на втором — остальные."""
    db = tmp_path / "big.db"
    init_db(db, apartments_count=80, nonresidential_count=2)
    conn = repository.connect(db)
    try:
        statement = build_statement(conn, "2026-07")
    finally:
        conn.close()
    out = export_statement(statement, "июль 2026", tmp_path / "big.xlsx")

    ws = load_workbook(out).active
    assert len(ws.row_breaks.brk) == 1              # ровно один перенос
    break_row = ws.row_breaks.brk[0].id
    # До переноса: 3 служебные строки + 40 квартир, последняя из них — кв. 40
    assert ws.cell(break_row, 1).value == "40"
    assert ws.cell(break_row + 1, 1).value == "41"


def test_long_note_wraps_instead_of_overflowing(db, tmp_path):
    """Длинное примечание должно переноситься внутри колонки, иначе при печати
    оно обрезается по краю листа А4."""
    conn = repository.connect(db)
    try:
        apt = repository.get_apartment_by_number(conn, "1")
        save_reading(conn, apt["id"], "electricity", 100, None,
                     period="2026-07", late=True)
        statement = build_statement(conn, "2026-07")
    finally:
        conn.close()
    out = export_statement(statement, "июль 2026", tmp_path / "v.xlsx")

    ws = load_workbook(out).active
    row = next(r for r in range(4, 12) if ws.cell(r, 1).value == "1")
    note = ws.cell(row, 9)
    # В печатной форме пометка сокращена: длинная фраза занимала три строки
    assert note.value and "срока" in note.value.lower()
    assert note.alignment.wrap_text is True
    # «Общедомовой прибор учета» в первой колонке тоже длиннее её ширины
    assert ws.cell(4, 1).alignment.wrap_text is True


def test_debtors_statement(db, tmp_path):
    conn = repository.connect(db)
    try:
        apt = repository.get_apartment_by_number(conn, "2")
        repository.create_user(conn, 42, "Петров И.И.", apt["id"])
        save_reading(conn, apt["id"], "electricity", 100, None, period="2026-07")
    finally:
        conn.close()

    out, count = build_debtors_statement("2026-07", tmp_path / "d.xlsx", db)
    assert count == 6                        # 7 строк реестра, сдала одна

    ws = load_workbook(out).active
    assert "Ведомость непередавших" in ws.cell(1, 1).value
    numbers = [ws.cell(r, 1).value for r in range(4, 4 + count)]
    assert "2" not in numbers                # сдавшая квартира не попала
    assert numbers[:3] == ["1", "3", "4"]    # по порядку
    assert ws.print_title_rows == "$3:$3"
