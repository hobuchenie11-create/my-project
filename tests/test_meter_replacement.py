"""Замена счётчика: показания нового прибора начинаются с нуля.

Житель пишет «Гвс ванна 3 (заменили счетчик)». Без пометки бот отклонял
такое показание как «меньше предыдущего» — и записать показания нового
прибора было нечем, кроме как руками председателя.
"""
import pytest

from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, receipt_text,
                                          save_parsed_readings, save_reading)
from database import repository
from database.init_db import init_db

MESSAGE = """Кв.49
Эл.эн 31457
Хвс кухня 207
Хвс санузел 396
Гвс кухня 94
Гвс ванна 3 (заменили счетчик)
Сумма ГВ 97"""


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "replace.db"
    init_db(db, apartments_count=50, nonresidential_count=0)
    conn = repository.connect(db)
    yield conn
    conn.close()


@pytest.fixture()
def flat(conn):
    """Кв. 49 с четырьмя счётчиками воды и показаниями прошлого месяца."""
    from bot.services import meters_service

    apartment = repository.get_apartment_by_number(conn, "49")
    meters_service.apply_layout(conn, apartment["id"], 2, 2)
    for kind, value in (("electricity", 31000), ("cws_kitchen", 200),
                        ("cws_bathroom", 390), ("hws_kitchen", 90),
                        ("hws_bathroom", 178)):
        save_reading(conn, apartment["id"], kind, value, None,
                     period="2026-09")
    conn.commit()
    return repository.get_apartment_by_number(conn, "49")


def test_note_is_recognised_and_does_not_eat_the_reading():
    parsed = parse_message(MESSAGE)

    assert parsed.apartment_number == "49"
    assert parsed.values["hws_bathroom"] == 3
    assert parsed.replaced_meters == {"hws_bathroom"}
    assert parsed.errors == []


@pytest.mark.parametrize("line", [
    "Гвс ванна 3 (заменили счетчик)",
    "Гвс ванна 3 — заменили счётчик",
    "Гвс ванна 3, новый счетчик",
    "Гвс ванна 3 (поменяли прибор учёта)",
    "Гвс ванна 3 счётчик заменён",
])
def test_the_wording_may_vary(line):
    parsed = parse_message(f"Кв. 49\n{line}")

    assert parsed.values.get("hws_bathroom") == 3, line
    assert parsed.replaced_meters == {"hws_bathroom"}, line


def test_note_on_its_own_line_belongs_to_the_meter_above():
    parsed = parse_message("Кв. 49\nГвс ванна 3\nзаменили счетчик")

    assert parsed.values["hws_bathroom"] == 3
    assert parsed.replaced_meters == {"hws_bathroom"}


def test_replaced_meter_starts_over(conn, flat):
    """Было 178, стало 3 — показание принимается, а не отклоняется."""
    outcome = save_parsed_readings(conn, flat, parse_message(MESSAGE), None,
                                   period=current_period())

    assert outcome.errors == []
    assert outcome.saved["hws_bathroom"] == 3
    assert outcome.new_meters == ["hws_bathroom"]


def test_other_meters_are_still_checked(conn, flat):
    """Замена одного прибора не отменяет проверку остальных."""
    message = MESSAGE.replace("Хвс кухня 207", "Хвс кухня 20")

    outcome = save_parsed_readings(conn, flat, parse_message(message), None,
                                   period=current_period())

    assert "hws_bathroom" in outcome.saved          # заменённый принят
    assert "cws_kitchen" not in outcome.saved       # а опечатка — нет
    assert any("меньше" in error for error in outcome.errors)


def test_receipt_says_the_meter_is_new(conn, flat):
    outcome = save_parsed_readings(conn, flat, parse_message(MESSAGE), None,
                                   period=current_period())

    receipt = receipt_text(conn, flat, outcome.saved,
                           new_meters=outcome.new_meters)

    assert "(новый счётчик)" in receipt
    assert "как начальное" in receipt


def test_next_month_counts_from_the_new_meter(conn, flat):
    """Следующее показание сверяется уже с цифрой нового прибора."""
    save_parsed_readings(conn, flat, parse_message(MESSAGE), None,
                         period="2026-10")

    result = save_reading(conn, flat["id"], "hws_bathroom", 1, None,
                          period="2026-11")
    assert result.ok is False                       # 1 меньше 3 — ошибка
    assert save_reading(conn, flat["id"], "hws_bathroom", 9, None,
                        period="2026-11").ok is True
