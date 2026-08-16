"""Сумма платежа вводится по частям: 214,33+155+207 — бот считает и расшифровывает."""
from datetime import date

import pytest

from bot.services import task_service
from bot.services.validation import parse_amount
from database import repository
from database.init_db import init_db


def test_single_amount():
    amount = parse_amount("4520,30")
    assert amount.total == 4520.30
    assert amount.is_split is False
    assert amount.breakdown("Квитанции") == ""     # расшифровывать нечего


def test_several_receipts_are_summed():
    amount = parse_amount("214,33+155,0+207,0")
    assert amount.total == 576.33
    assert amount.is_split is True
    assert amount.breakdown("Квитанции") == "Квитанции: 214,33 + 155 + 207"


def test_spaces_and_dots_are_accepted():
    assert parse_amount("214.33 + 155 + 207").total == 576.33
    assert parse_amount(" 7643+7327 ").total == 14970
    assert parse_amount("155+").total == 155           # лишний плюс в конце


def test_garbage_is_rejected():
    assert parse_amount("214,33+abc") is None
    assert parse_amount("") is None
    assert parse_amount("+") is None
    assert parse_amount("-500") is None


def test_rounding_keeps_kopecks():
    amount = parse_amount("93,41+198+149")
    assert amount.total == 440.41
    assert amount.breakdown("Квитанции") == "Квитанции: 93,41 + 198 + 149"


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "amounts.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    yield conn
    conn.close()


def _task(conn, part):
    return next(r for r in repository.tasks_for_period(conn, "2026-09")
                if part.lower() in r["title"].lower())


def test_breakdown_is_saved_as_the_task_note(conn):
    utilities = _task(conn, "коммунальных услуг")
    amount = parse_amount("214,33+155+207")

    task_service.complete_task(conn, utilities["id"], tg_id=1,
                               amount=amount.total, paid_at="2026-09-17",
                               amount_field="utility_amount",
                               note=amount.breakdown("Квитанции"))

    row = repository.get_task(conn, utilities["id"])
    assert row["utility_amount"] == 576.33
    assert row["note"] == "Квитанции: 214,33 + 155 + 207"
    assert row["status"] == "done"


def test_existing_note_survives_a_single_amount(conn):
    """Одна сумма — расшифровки нет, и старое примечание не затирается."""
    utilities = _task(conn, "коммунальных услуг")
    repository.update_task(conn, utilities["id"], note="платёж через Сбербанк")

    amount = parse_amount("4520,30")
    task_service.complete_task(conn, utilities["id"], tg_id=1,
                               amount=amount.total, paid_at="2026-09-17",
                               amount_field="utility_amount",
                               note=amount.breakdown("Квитанции"))

    assert repository.get_task(conn, utilities["id"])["note"] == "платёж через Сбербанк"
