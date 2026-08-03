"""Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»."""
from datetime import date

import pytest

from bot.services.parser import parse_message
from bot.services.reading_service import is_late, save_parsed_readings, save_reading
from bot.services.report_service import build_statement
from database import repository
from database.init_db import init_db
from database.models import LATE_NOTE


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    init_db(db, apartments_count=3, nonresidential_count=0)
    conn = repository.connect(db)
    yield conn
    conn.close()


@pytest.mark.parametrize("day, expected", [
    (14, False),   # до начала сбора — считается сроком (показания примут)
    (15, False),   # первый день сбора
    (19, False),   # последний день сбора
    (20, True),    # день формирования ведомости — уже после срока
    (25, True),
    (30, True),
])
def test_is_late_by_day(day, expected):
    assert is_late(date(2026, 7, day)) is expected


def test_reading_in_time_has_no_note(conn):
    apt = repository.get_apartment_by_number(conn, "1")
    save_reading(conn, apt["id"], "electricity", 100, None,
                 period="2026-07", late=False)
    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "1")
    assert row.submitted
    assert LATE_NOTE not in row.note


def test_late_reading_marked_in_statement(conn):
    apt = repository.get_apartment_by_number(conn, "2")
    save_reading(conn, apt["id"], "electricity", 100, None,
                 period="2026-07", late=True)
    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "2")
    assert row.submitted                     # записано в текущем месяце
    assert row.note == LATE_NOTE             # с пометкой


def test_late_flag_stored_for_parsed_message(conn):
    apt = repository.get_apartment_by_number(conn, "3")
    parsed = parse_message("Кв 3\nЭл 500\nХвс 10\nГвс 20")
    outcome = save_parsed_readings(conn, apt, parsed, None,
                                   period="2026-07", late=True)
    assert outcome.anything_saved
    rows = repository.readings_for_period(conn, "2026-07")
    assert all(r["late"] == 1 for r in rows if r["apartment_number"] == "3")


def test_late_note_appended_to_existing_note(conn):
    repository.upsert_apartment(conn, "1", "residential", 1, note="Счётчик заменён")
    conn.commit()
    apt = repository.get_apartment_by_number(conn, "1")
    save_reading(conn, apt["id"], "electricity", 100, None,
                 period="2026-07", late=True)
    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "1")
    assert "Счётчик заменён" in row.note
    assert LATE_NOTE in row.note
