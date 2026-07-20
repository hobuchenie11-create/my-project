"""Раскладка распознанных показаний на приборы конкретной квартиры."""
import pytest

from bot.services.parser import parse_message
from bot.services.reading_service import save_parsed_readings
from database import repository
from database.init_db import init_db


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    # кв. 1 — полная (3-комн, по умолчанию), кв. 2 — compact (1-2 комн)
    apt2 = repository.get_apartment_by_number(conn, "2")
    repository.upsert_apartment(conn, "2", "residential", 2, layout="compact")
    repository.set_meters(conn, apt2["id"], ["electricity", "cws", "hws"])
    conn.commit()
    yield conn
    conn.close()


def test_full_apartment_split(conn):
    apt = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв 1\nЭл 100\nХвс кухня 5\nХвс с/у 6\n"
                           "Гвс кухня 7\nГвс ванна 8\nСумма гвс 15")
    outcome = save_parsed_readings(conn, apt, parsed, None, period="2026-07")
    assert outcome.saved == {
        "electricity": 100.0, "cws_kitchen": 5.0, "cws_bathroom": 6.0,
        "hws_kitchen": 7.0, "hws_bathroom": 8.0,
    }
    assert not outcome.errors


def test_full_apartment_sum_mismatch_warns(conn):
    apt = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв 1\nГвс кухня 7\nГвс ванна 8\nСумма гвс 99")
    outcome = save_parsed_readings(conn, apt, parsed, None, period="2026-07")
    assert any("не сходится" in w for w in outcome.warnings)


def test_compact_apartment_single(conn):
    apt = repository.get_apartment_by_number(conn, "2")
    parsed = parse_message("Кв 2\nЭл.эн 200\nхвс 10\nгвс 20")
    outcome = save_parsed_readings(conn, apt, parsed, None, period="2026-07")
    assert outcome.saved == {"electricity": 200.0, "cws": 10.0, "hws": 20.0}


def test_compact_apartment_rejects_split(conn):
    apt = repository.get_apartment_by_number(conn, "2")
    parsed = parse_message("Кв 2\nХвс кухня 10")
    outcome = save_parsed_readings(conn, apt, parsed, None, period="2026-07")
    assert not outcome.saved
    assert outcome.errors
