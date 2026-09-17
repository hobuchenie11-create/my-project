"""Правка уже принятого показания: «Исправить» в первой строке.

Ошибка в ведомости не должна тянуться в следующий месяц: расход считается
от последнего показания, поэтому исправлять надо саму цифру, а не пересчёт.
"""
import pytest

from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, receipt_text,
                                          save_parsed_readings, save_reading)
from bot.services.report_service import build_statement
from database import repository
from database.init_db import init_db


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    init_db(db, apartments_count=3, nonresidential_count=0)
    conn = repository.connect(db)
    yield conn
    conn.close()


@pytest.fixture()
def flat(conn):
    return repository.get_apartment_by_number(conn, "1")


def test_correction_mark_is_recognised():
    parsed = parse_message("Исправить\nКв. 56\nЭл.эн 61682")
    assert parsed.is_correction is True
    assert parsed.apartment_number == "56"
    # Само слово в подпись прибора не попадает
    assert parsed.values == {"electricity": 61682}


def test_plain_message_is_not_a_correction():
    assert parse_message("Кв. 56\nЭл.эн 61682").is_correction is False


def test_correction_replaces_value_in_statement(conn, flat):
    save_reading(conn, flat["id"], "electricity", 99999, None)   # опечатка
    save_reading(conn, flat["id"], "electricity", 15230, None, correction=True)

    statement = build_statement(conn, current_period())
    row = next(r for r in statement.rows if r.number == "1")
    assert row.electricity == 15230
    # Старое показание остаётся в истории — правка ничего не удаляет
    history = repository.readings_history_for_apartment(conn, flat["id"])
    assert [h["value"] for h in history] == [15230, 99999]


def test_correction_may_lower_the_value(conn, flat):
    """Обычная запись меньше предыдущей отклоняется, правка — принимается."""
    save_reading(conn, flat["id"], "electricity", 99999, None)

    rejected = save_reading(conn, flat["id"], "electricity", 15230, None)
    assert rejected.ok is False and "меньше показания за" in rejected.error

    fixed = save_reading(conn, flat["id"], "electricity", 15230, None,
                         correction=True)
    assert fixed.ok is True


def test_correction_still_checked_against_previous_month(conn, flat):
    """Запас прочности: исправленное показание не может быть меньше прошлого месяца."""
    save_reading(conn, flat["id"], "electricity", 15000, None, period="2026-06")
    save_reading(conn, flat["id"], "electricity", 15230, None, period="2026-07")

    result = save_reading(conn, flat["id"], "electricity", 14000, None,
                          period="2026-07", correction=True)
    assert result.ok is False
    assert "меньше показания за" in result.error


def test_correction_keeps_next_month_consumption_right(conn, flat):
    """Ради этого всё и делается: расход следующего месяца — от исправленной цифры."""
    save_reading(conn, flat["id"], "electricity", 99999, None, period="2026-07")
    save_reading(conn, flat["id"], "electricity", 15230, None, period="2026-07",
                 correction=True)

    # В августе показание 15310 приняли бы только если база знает про 15230
    august = save_reading(conn, flat["id"], "electricity", 15310, None,
                          period="2026-08")
    assert august.ok is True


def test_correction_does_not_mark_reading_as_late(conn, flat):
    """Исправляют обычно после срока — пометку наследуем от исходной записи."""
    save_reading(conn, flat["id"], "electricity", 99999, None, late=False)
    save_reading(conn, flat["id"], "electricity", 15230, None, correction=True)

    rows = repository.readings_for_period(conn, current_period())
    assert [r["late"] for r in rows if r["kind"] == "electricity"] == [0]


def test_receipt_shows_what_was_replaced(conn, flat):
    save_reading(conn, flat["id"], "electricity", 99999, None)
    parsed = parse_message("Исправить\nКв. 1\nЭл.эн 15230")
    outcome = save_parsed_readings(conn, flat, parsed, None, correction=True)

    assert outcome.saved == {"electricity": 15230}
    assert outcome.replaced == {"electricity": 99999}
    text = receipt_text(conn, flat, outcome.saved, replaced=outcome.replaced)
    assert "исправлены" in text
    assert "15230" in text and "было 99999" in text


def test_correction_touches_only_named_meters(conn, flat):
    save_reading(conn, flat["id"], "electricity", 99999, None)
    save_reading(conn, flat["id"], "cws", 120, None)

    parsed = parse_message("Исправить\nКв. 1\nЭл.эн 15230")
    save_parsed_readings(conn, flat, parsed, None, correction=True)

    statement = build_statement(conn, current_period())
    row = next(r for r in statement.rows if r.number == "1")
    assert row.electricity == 15230
    assert row.cws_kitchen == 120


# ---------------------------------------------------------------------------
# Правка за прошлый месяц
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("line, period", [
    ("Исправить за август", "2026-08"),
    ("Исправить за Август", "2026-08"),
    ("Исправить 08.2026", "2026-08"),
    ("Исправить за август 2026", "2026-08"),
    ("Исправить за сентябрь", "2026-09"),
    ("Исправить за декабрь", "2025-12"),      # декабря 2026 ещё не было
])
def test_correction_names_the_month(line, period):
    parsed = parse_message(f"{line}\nКв 68\nХвс кухня 147")
    assert parsed.is_correction
    assert parsed.period == period
    assert parsed.values == {"cws_kitchen": 147.0}


def test_correction_without_a_month_stays_in_the_current_period():
    parsed = parse_message("Исправить\nКв 68\nХвс кухня 147")
    assert parsed.is_correction and parsed.period is None


def test_month_is_looked_for_only_in_corrections():
    """«Гвс 05.2026» в обычном сообщении — описка, а не период."""
    parsed = parse_message("Кв 68\nГвс 05.2026")
    assert parsed.period is None


def test_previous_month_can_be_fixed_and_unblocks_the_current(conn, flat):
    """Из-за неверного августа сентябрь не принимался — правка это снимает."""
    # август записан с ошибкой: 197 вместо 147
    save_parsed_readings(conn, flat, parse_message("Кв 1\nХвс 197"),
                         None, period="2026-08")

    # сентябрьское показание бот отклоняет
    blocked = save_parsed_readings(conn, flat, parse_message("Кв 1\nХвс 150"),
                                   None, period="2026-09")
    assert blocked.saved == {}
    assert any("меньше показания за август" in e for e in blocked.errors)

    # правка за август
    parsed = parse_message("Исправить за август\nКв 1\nХвс 147")
    assert parsed.period == "2026-08"
    fixed = save_parsed_readings(conn, flat, parsed, None,
                                 correction=True, period=parsed.period)
    assert fixed.saved == {"cws": 147.0}

    # теперь сентябрь принимается
    again = save_parsed_readings(conn, flat, parse_message("Кв 1\nХвс 150"),
                                 None, period="2026-09")
    assert again.saved == {"cws": 150.0}
    assert again.errors == []

    meter = repository.get_meter(conn, flat["id"], "cws")
    august = repository.reading_for_period(conn, meter["id"], "2026-08")
    assert august["value"] == 147.0, "в ведомость за август идёт правка"


def test_the_wrong_august_figure_stays_in_history(conn, flat):
    """Прежняя цифра не стирается — по журналу видно, что и когда поправили."""
    save_parsed_readings(conn, flat, parse_message("Кв 1\nХвс 197"),
                         None, period="2026-08")
    parsed = parse_message("Исправить за август\nКв 1\nХвс 147")
    save_parsed_readings(conn, flat, parsed, None, correction=True,
                         period=parsed.period)

    rows = repository.readings_history_for_apartment(conn, flat["id"])
    august = [r["value"] for r in rows if r["period"] == "2026-08"]
    assert sorted(august) == [147.0, 197.0]
