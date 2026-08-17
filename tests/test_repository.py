import pytest

from bot.services.reading_service import save_reading
from bot.services.report_service import build_statement
from database import repository
from database.init_db import init_db
from database.models import apartment_meters


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "test.db"
    init_db(db, apartments_count=3, nonresidential_count=1)
    conn = repository.connect(db)
    yield conn
    conn.close()


def test_seed(conn):
    apartments = repository.list_apartments(conn)
    assert len(apartments) == 5              # 3 квартиры, нежилое, общедомовой
    assert apartments[0]["number"] == "1"
    assert apartments[3]["number"] == "Нежилое помещение №1"
    assert apartments[4]["number"] == "Общедомовой прибор учета"
    # По умолчанию квартира — один ХВС и один ГВС (+ электро)
    assert len(repository.meters_for_apartment(conn, apartments[0]["id"])) == 3
    # Нежилое №1 — электричество и вода, общедомовой — только электричество
    assert [m["kind"] for m in repository.meters_for_apartment(
        conn, apartments[3]["id"])] == ["electricity", "cws", "hws"]
    assert [m["kind"] for m in repository.meters_for_apartment(
        conn, apartments[4]["id"])] == ["electricity"]


def test_save_and_last_reading(conn):
    apt = repository.get_apartment_by_number(conn, "1")
    result = save_reading(conn, apt["id"], "electricity", 100.0, None, period="2026-07")
    assert result.ok

    result = save_reading(conn, apt["id"], "electricity", 90.0, None, period="2026-08")
    assert not result.ok  # меньше предыдущего

    result = save_reading(conn, apt["id"], "electricity", 150.0, None, period="2026-08")
    assert result.ok


def test_statement_split_apartment(conn):
    # Делаем кв. 2 с раздельным учетом (2 ХВС + 2 ГВС)
    apt = repository.get_apartment_by_number(conn, "2")
    repository.set_meters(conn, apt["id"], apartment_meters(2, 2))
    save_reading(conn, apt["id"], "electricity", 500, None, period="2026-07")
    save_reading(conn, apt["id"], "hws_kitchen", 10, None, period="2026-07")
    save_reading(conn, apt["id"], "hws_bathroom", 20, None, period="2026-07")

    statement = build_statement(conn, "2026-07")
    assert len(statement.rows) == 5  # 3 квартиры, нежилое, общедомовой прибор
    numbers = [r.number for r in statement.rows]
    assert numbers[:2] == ["Нежилое помещение №1", "Общедомовой прибор учета"]

    row = next(r for r in statement.rows if r.number == "2")
    assert row.submitted
    assert row.electricity == 500
    assert row.hws_sum == 30
    assert statement.submitted_count == 1
    assert statement.total_count == 5


def test_statement_single_apartment(conn):
    # Квартира с одним ХВС/ГВС: значения идут в «ХВС кухня» и «ГВС сумма»
    apt = repository.get_apartment_by_number(conn, "3")
    save_reading(conn, apt["id"], "cws", 40, None, period="2026-07")
    save_reading(conn, apt["id"], "hws", 55, None, period="2026-07")

    row = next(r for r in build_statement(conn, "2026-07").rows if r.number == "3")
    assert row.cws_kitchen == 40
    assert row.hws_sum == 55


def test_submitted_set(conn):
    apt = repository.get_apartment_by_number(conn, "3")
    save_reading(conn, apt["id"], "cws", 5, None, period="2026-07")
    assert repository.apartments_submitted(conn, "2026-07") == {"3"}
