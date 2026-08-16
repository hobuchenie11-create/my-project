"""Удаление тестовых показаний: фильтры, безопасность, влияние на проверки."""
import pytest

from bot.services.reading_service import save_reading
from database import repository
from database.cleanup import _parse_date, describe
from database.init_db import init_db


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "cleanup.db"
    init_db(db, apartments_count=3, nonresidential_count=1)
    conn = repository.connect(db)
    yield conn
    conn.close()


def _reading(conn, apartment, kind, value, created_at, period="2026-08"):
    """Показание с заданной датой внесения — имитируем тестовые записи."""
    row = repository.get_apartment_by_number(conn, apartment)
    meter = repository.get_meter(conn, row["id"], kind)
    conn.execute(
        """INSERT INTO readings (meter_id, user_id, period, value, source, created_at)
           VALUES (?, NULL, ?, ?, 'chat', ?)""",
        (meter["id"], period, value, created_at))
    conn.commit()


def test_dates_are_parsed_in_both_formats():
    assert _parse_date("15.08.2026") == "2026-08-15 00:00:00"
    assert _parse_date("2026-08-15") == "2026-08-15 00:00:00"
    with pytest.raises(SystemExit):
        _parse_date("позавчера")


def test_before_keeps_later_readings(conn):
    _reading(conn, "1", "cws", 121, "2026-08-02 10:00:00")   # тестовое
    _reading(conn, "1", "cws", 119, "2026-08-16 17:05:00")   # настоящее

    doomed = repository.find_readings(conn, before="2026-08-15 00:00:00")
    assert [r["value"] for r in doomed] == [121]

    repository.delete_readings(conn, [r["id"] for r in doomed])
    left = repository.find_readings(conn)
    assert [r["value"] for r in left] == [119]


def test_filters_by_apartment_and_period(conn):
    _reading(conn, "1", "cws", 10, "2026-08-02 10:00:00")
    _reading(conn, "2", "cws", 20, "2026-08-02 10:00:00")
    _reading(conn, "3", "cws", 30, "2026-07-02 10:00:00", period="2026-07")

    assert len(repository.find_readings(conn, apartment="2")) == 1
    assert len(repository.find_readings(conn, period="2026-07")) == 1
    assert len(repository.find_readings(conn, period="2026-08")) == 2


def test_empty_selection_deletes_nothing(conn):
    _reading(conn, "1", "cws", 10, "2026-08-16 10:00:00")
    doomed = repository.find_readings(conn, before="2026-08-01 00:00:00")

    assert doomed == []
    assert repository.delete_readings(conn, []) == 0
    assert len(repository.find_readings(conn)) == 1


def test_real_reading_is_accepted_after_cleanup(conn):
    """Ради этого всё и затевалось: настоящее показание перестаёт отклоняться."""
    _reading(conn, "1", "cws", 121, "2026-08-02 10:00:00")   # тестовое, завышенное
    apartment = repository.get_apartment_by_number(conn, "1")

    rejected = save_reading(conn, apartment["id"], "cws", 119, None, source="chat")
    assert not rejected.ok and "меньше предыдущего" in rejected.error

    doomed = repository.find_readings(conn, before="2026-08-15 00:00:00")
    repository.delete_readings(conn, [r["id"] for r in doomed])

    accepted = save_reading(conn, apartment["id"], "cws", 119, None, source="chat")
    assert accepted.ok
    assert not accepted.warning          # и «необычно большого расхода» тоже нет


def test_description_lists_flats_and_totals(conn):
    _reading(conn, "1", "cws", 121, "2026-08-02 10:00:00")
    _reading(conn, "2", "electricity", 15000, "2026-08-02 10:00:00")

    text = describe(repository.find_readings(conn))
    assert "Кв. 1" in text and "Кв. 2" in text
    assert "ХВС" in text and "Электроэнергия" in text
    assert "Всего показаний: 2" in text
    assert describe([]) == "Под фильтр ничего не попало."
