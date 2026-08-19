"""Раскладка распознанных показаний на приборы конкретной квартиры."""
import pytest

from bot.services.parser import parse_message
from bot.services.reading_service import save_parsed_readings
from database import repository
from database.init_db import init_db
from database.models import apartment_meters


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    # кв. 1 — раздельный учет (2 ХВС + 2 ГВС), кв. 2 — один ХВС/ГВС (по умолчанию)
    apt1 = repository.get_apartment_by_number(conn, "1")
    repository.set_meters(conn, apt1["id"], apartment_meters(2, 2))
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


def test_compact_apartment_takes_a_single_location(conn):
    """Прибор один, названо одно место — это он и есть (счётчик в санузле)."""
    apt = repository.get_apartment_by_number(conn, "2")
    parsed = parse_message("Кв 2\nХвс кухня 10")
    outcome = save_parsed_readings(conn, apt, parsed, None, period="2026-07")
    assert outcome.saved == {"cws": 10.0}
    assert outcome.errors == []


def test_total_line_in_a_flat_with_separate_meters(conn):
    """«ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор."""
    apartment = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв. 1\nЭлектро 21694\nХвс кухня 138\n"
                           "Хвс санузел 617\nГвс кухня 206\nГвс ванна 622\n"
                           "Гвс 828")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.errors == []                   # никаких «нет такого прибора»
    assert outcome.warnings == []                 # 206 + 622 = 828, сходится
    assert outcome.saved["hws_kitchen"] == 206
    assert outcome.saved["hws_bathroom"] == 622


def test_total_line_that_does_not_add_up_warns(conn):
    apartment = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв. 1\nГвс кухня 206\nГвс ванна 622\nГвс 800")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.errors == []
    assert any("не сходится" in w for w in outcome.warnings)


def test_cold_total_is_checked_too(conn):
    apartment = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв. 1\nХвс кухня 138\nХвс санузел 617\nХвс 755")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.errors == []
    assert outcome.warnings == []                 # 138 + 617 = 755


def test_single_meter_accepts_a_location_label(conn):
    """У кв. 2 один ХВС и один ГВС, а житель подписал место установки."""
    apartment = repository.get_apartment_by_number(conn, "2")
    parsed = parse_message("Кв. 2\nЭл.эн 15304\nХвс сан.узел 120\nГвс ванна 88")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.errors == []
    assert outcome.saved == {"electricity": 15304.0, "cws": 120.0, "hws": 88.0}


def test_two_locations_for_one_meter_are_not_guessed(conn):
    """Прибор один, а мест названо два — записывать наугад нельзя."""
    apartment = repository.get_apartment_by_number(conn, "2")
    parsed = parse_message("Кв. 2\nХвс кухня 10\nХвс сан.узел 20")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.saved == {}
    assert any("один счётчик" in e for e in outcome.errors)


def test_separate_meters_still_need_their_locations(conn):
    """У кв. 1 учёт раздельный — подписи по местам работают как раньше."""
    apartment = repository.get_apartment_by_number(conn, "1")
    parsed = parse_message("Кв. 1\nХвс кухня 10\nХвс сан.узел 20\n"
                           "Гвс кухня 30\nГвс ванна 40")
    outcome = save_parsed_readings(conn, apartment, parsed, None)

    assert outcome.errors == []
    assert outcome.saved == {"cws_kitchen": 10.0, "cws_bathroom": 20.0,
                             "hws_kitchen": 30.0, "hws_bathroom": 40.0}
