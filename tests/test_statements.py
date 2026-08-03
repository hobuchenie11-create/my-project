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
    assert numbers[:5] == ["1", "2", "3", "4", "5"]          # по порядку
    assert numbers[-1] == "Общедомовой прибор учета"


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
    assert ws.sheet_properties.pageSetUpPr.fitToPage is True
    assert ws.print_title_rows == "$3:$3"      # шапка повторяется на каждой странице
    assert ws.print_area is not None


def test_debtors_statement(db, tmp_path):
    conn = repository.connect(db)
    try:
        apt = repository.get_apartment_by_number(conn, "2")
        repository.create_user(conn, 42, "Петров И.И.", apt["id"])
        save_reading(conn, apt["id"], "electricity", 100, None, period="2026-07")
    finally:
        conn.close()

    out, count = build_debtors_statement("2026-07", tmp_path / "d.xlsx", db)
    assert count == 5                        # 6 помещений, сдало одно

    ws = load_workbook(out).active
    assert "Ведомость непередавших" in ws.cell(1, 1).value
    numbers = [ws.cell(r, 1).value for r in range(4, 4 + count)]
    assert "2" not in numbers                # сдавшая квартира не попала
    assert numbers[:3] == ["1", "3", "4"]    # по порядку
    assert ws.print_title_rows == "$3:$3"
