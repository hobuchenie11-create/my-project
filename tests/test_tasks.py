"""Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки."""
from datetime import date

import pytest

from bot.services import task_service
from database import repository
from database.init_db import init_db


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "tasks.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    yield conn
    conn.close()


def _by_title(conn, period, part):
    return next(r for r in repository.tasks_for_period(conn, period)
                if part.lower() in r["title"].lower())


def test_templates_cover_the_chairman_cycle(conn):
    task_service.ensure_templates(conn)
    codes = {t["code"] for t in repository.active_task_templates(conn)}
    assert codes == {"bank_statement", "posting_invoices",
                     "nonresidential_payment", "submit_readings_rso"}


def test_generate_creates_tasks_with_windows(conn):
    created = task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    assert created == 4

    bank = _by_title(conn, "2026-09", "выписку из банка")
    assert bank["start_date"] == "2026-09-02"     # окно 2-5 числа
    assert bank["due_date"] == "2026-09-05"

    invoices = _by_title(conn, "2026-09", "квитанц")
    assert (invoices["start_date"], invoices["due_date"]) == ("2026-09-05", "2026-09-10")

    payment = _by_title(conn, "2026-09", "нежилому")
    assert payment["due_date"] == "2026-09-18"    # до 18 числа

    readings = _by_title(conn, "2026-09", "ресурсоснабжающим")
    assert (readings["start_date"], readings["due_date"]) == ("2026-09-20", "2026-09-25")


def test_generation_is_idempotent(conn):
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    again = task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    assert again == 0                            # повторный запуск не дублирует


def test_cycle_continues_into_next_year(conn):
    # Из декабря цикл разворачивается в январь-март следующего года
    task_service.generate_tasks(conn, date(2026, 12, 1), months_ahead=3)
    assert repository.tasks_for_period(conn, "2027-01")
    assert repository.tasks_for_period(conn, "2027-03")


def test_generate_year_covers_twelve_months(conn):
    created = task_service.generate_year(conn, 2027)
    assert created == 12 * 4
    assert len(repository.tasks_in_year(conn, 2027)) == 48


def test_short_month_does_not_break_dates(conn):
    # У шаблона день 25, февраль короче — дата остаётся корректной
    task_service.generate_tasks(conn, date(2027, 2, 1), months_ahead=0)
    readings = _by_title(conn, "2027-02", "ресурсоснабжающим")
    assert readings["due_date"] == "2027-02-25"


def test_overdue_and_active_states(conn):
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    bank = _by_title(conn, "2026-09", "выписку из банка")   # 2-5 сентября

    assert task_service.view(bank, date(2026, 9, 1)).is_active_now is False  # ещё рано
    assert task_service.view(bank, date(2026, 9, 3)).is_active_now is True
    assert task_service.view(bank, date(2026, 9, 10)).is_overdue is True


def test_complete_payment_stores_amount_and_date(conn):
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    payment = _by_title(conn, "2026-09", "нежилому")

    task_service.complete_task(conn, payment["id"], tg_id=1,
                               amount=4520.30, paid_at="2026-09-17")
    row = repository.get_task(conn, payment["id"])
    assert row["status"] == "done"
    assert row["amount"] == 4520.30
    assert row["paid_at"] == "2026-09-17"

    history = repository.task_history(conn, payment["id"])
    assert any("4520" in e["details"] for e in history)      # записано в журнал


def test_done_task_is_not_reminded(conn):
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    bank = _by_title(conn, "2026-09", "выписку из банка")

    overdue_day = date(2026, 9, 12)
    assert any("выписку" in m for m in task_service.reminders_for_today(conn, overdue_day))

    task_service.set_status(conn, bank["id"], "done", tg_id=1)
    assert not any("выписку" in m
                   for m in task_service.reminders_for_today(conn, overdue_day))


def test_reminder_on_window_start(conn):
    task_service.generate_tasks(conn, date(2026, 9, 1), months_ahead=0)
    messages = task_service.reminders_for_today(conn, date(2026, 9, 2))
    assert any("Пора начинать" in m and "выписку" in m for m in messages)


def test_council_digest_hides_internal_details(conn):
    task_service.generate_tasks(conn, date.today(), months_ahead=0)
    payment = _by_title(conn, task_service._month_period(date.today()), "нежилому")
    task_service.set_status(conn, payment["id"], "in_progress", tg_id=1)
    task_service.complete_task(conn, payment["id"], tg_id=1, amount=9999.0,
                               paid_at=date.today().isoformat())

    digest = task_service.council_digest(conn)
    assert "Совет дома" in digest
    assert "9999" not in digest                  # суммы Совету не показываем
    assert "заполняется" not in digest.lower()


def test_year_plan_export(conn, tmp_path):
    from excel.tasks_export import export_year_plan
    from openpyxl import load_workbook

    task_service.generate_year(conn, 2027)
    out = export_year_plan(conn, 2027, tmp_path / "plan.xlsx")

    wb = load_workbook(out)
    assert wb.sheetnames == ["Годовой план", "Регламент"]
    ws = wb["Годовой план"]
    assert "2027" in ws.cell(1, 1).value
    titles = [ws.cell(r, 2).value for r in range(3, 60)]
    assert any(t and "выписку из банка" in t.lower() for t in titles)
    assert any(t and "январь" in str(ws.cell(r, 1).value or "").lower()
               for r in range(3, 10) for t in [1])
