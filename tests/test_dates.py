"""Разбор даты, введённой руками, и починка уже испорченных записей."""
from datetime import date

import pytest

from bot.utils.dates import looks_broken, parse_user_date, repair_year
from database import repository
from database.init_db import init_db
from database.repair import repair_broken_years

TODAY = date(2026, 9, 16)


@pytest.mark.parametrize("text, expected", [
    ("30.09.2026", date(2026, 9, 30)),
    ("30/09/2026", date(2026, 9, 30)),
    ("30-09-2026", date(2026, 9, 30)),
    ("30 09 2026", date(2026, 9, 30)),
    ("  05.01.2027  ", date(2027, 1, 5)),
])
def test_full_date_in_any_separator(text, expected):
    assert parse_user_date(text, today=TODAY) == expected


@pytest.mark.parametrize("text, expected", [
    ("30.09.26", date(2026, 9, 30)),
    ("25.09.26", date(2026, 9, 25)),
    ("07.01.27", date(2027, 1, 7)),
])
def test_two_digit_year_is_the_two_thousands(text, expected):
    """Главная причина «просрочено на 730471 дн.»: 26 — это 2026, не 26 год."""
    assert parse_user_date(text, today=TODAY) == expected


def test_words_instead_of_a_date():
    assert parse_user_date("сегодня", today=TODAY) == TODAY
    assert parse_user_date("Завтра", today=TODAY) == date(2026, 9, 17)
    assert parse_user_date("вчера", today=TODAY) == date(2026, 9, 15)


def test_due_date_without_a_year_looks_forward():
    """Срок задачи всегда впереди: «30.09» — этот сентябрь, «07.01» — январь."""
    assert parse_user_date("30.09", today=TODAY, prefer="future") == date(2026, 9, 30)
    assert parse_user_date("07.01", today=TODAY, prefer="future") == date(2027, 1, 7)


def test_past_date_without_a_year_looks_back():
    """Оплата и поверка уже случились — год берём назад."""
    assert parse_user_date("10.09", today=TODAY, prefer="past") == date(2026, 9, 10)
    assert parse_user_date("30.09", today=TODAY, prefer="past") == date(2025, 9, 30)


@pytest.mark.parametrize("text", [
    "", None, "завтра утром", "тридцатое", "30.09.1998", "30.13.2026",
    "31.04.2026", "30.09.2126", "30", "30.09.2026.10",
])
def test_nonsense_is_refused_instead_of_stored(text):
    """Лучше переспросить, чем записать дату, которой не бывает."""
    assert parse_user_date(text, today=TODAY) is None


def test_leap_day_without_a_year_skips_non_leap_years():
    assert parse_user_date("29.02", today=date(2027, 1, 10),
                           prefer="future") == date(2028, 2, 29)


def test_broken_year_is_recognised_and_repaired():
    assert looks_broken("0026-09-30") is True
    assert looks_broken("2026-09-30") is False
    assert looks_broken("") is False
    assert repair_year("0026-09-30") == "2026-09-30"
    assert repair_year("2026-09-30") == "2026-09-30"


def test_repair_fixes_tasks_already_in_the_database(tmp_path):
    """Задачи, записанные 26 годом, после обновления встают на свои даты."""
    db = tmp_path / "repair.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    try:
        broken = repository.create_task(
            conn, "уточнить у инженера про сан.обработку",
            due_date="0026-09-30", period="0026-09", source="chairman")
        healthy = repository.create_task(
            conn, "оплатить GSM", due_date="2026-09-07", period="2026-09",
            source="chairman")
        conn.commit()

        assert repair_broken_years(conn) == 1

        fixed = repository.get_task(conn, broken)
        assert fixed["due_date"] == "2026-09-30"
        assert fixed["period"] == "2026-09"
        assert repository.get_task(conn, healthy)["due_date"] == "2026-09-07"

        # повторный запуск ничего не трогает
        assert repair_broken_years(conn) == 0
    finally:
        conn.close()


def test_init_db_repairs_on_startup(tmp_path):
    """Починка идёт при каждом старте бота — руками ничего делать не нужно."""
    db = tmp_path / "startup.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    try:
        task_id = repository.create_task(conn, "штатлевание входных дверей",
                                         due_date="0026-09-25", source="chairman")
        conn.commit()
    finally:
        conn.close()

    init_db(db, apartments_count=2, nonresidential_count=1)

    conn = repository.connect(db)
    try:
        assert repository.get_task(conn, task_id)["due_date"] == "2026-09-25"
    finally:
        conn.close()
