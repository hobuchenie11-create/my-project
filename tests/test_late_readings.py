"""Регламент сбора: срок — до формирования ведомости 20 числа в 14:00."""
from datetime import date, datetime

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
    (21, True),    # ведомость уже ушла
    (25, True),
    (30, True),
])
def test_is_late_by_day(day, expected):
    assert is_late(date(2026, 7, day)) is expected


@pytest.mark.parametrize("hour, expected", [
    (9, False),    # утро 20 числа — ещё попадёт в текущую ведомость
    (13, False),
    (14, True),    # ведомость сформирована
    (18, True),
])
def test_statement_day_decided_by_the_hour(hour, expected):
    """20 числа всё решает час: до 14:00 показания ещё не опоздали."""
    assert is_late(datetime(2026, 7, 20, hour, 30)) is expected


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


def test_late_reading_still_lands_in_the_current_statement(conn):
    """Опоздавшие показания видны в реестре — с пометкой, но не потеряны."""
    apt = repository.get_apartment_by_number(conn, "1")
    save_reading(conn, apt["id"], "electricity", 100, None,
                 period="2026-07", late=True)
    save_reading(conn, apt["id"], "cws", 55, None, period="2026-07", late=True)

    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "1")
    assert row.submitted
    assert row.electricity == 100 and row.cws_kitchen == 55
    assert row.note == LATE_NOTE


def test_morning_of_the_statement_day_is_not_marked_late(conn):
    """Показания 20 числа до 14:00 идут в ведомость без пометки."""
    apt = repository.get_apartment_by_number(conn, "2")
    save_reading(conn, apt["id"], "electricity", 100, None, period="2026-07",
                 late=is_late(datetime(2026, 7, 20, 9, 40)))

    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "2")
    assert row.submitted
    assert LATE_NOTE not in row.note


def test_closing_message_invites_to_keep_sending():
    """Сообщение в чат: сбор закрыт, но показания принимаются дальше."""
    from bot.texts import collection_closed_text

    text = collection_closed_text(date(2026, 8, 20))
    assert "за август завершён" in text
    assert "Передать показания можно и сейчас" in text
    assert "следующем расчётном периоде" in text
    assert "до 25 числа" in text                  # ресурсники ждут до 25-го
    assert "с 15 по 19 число" in text             # когда следующий сбор
