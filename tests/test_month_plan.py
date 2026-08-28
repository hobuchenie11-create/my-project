"""План месяца в боте: задачи приходят по одной, с кнопками.

Одним сообщением план читался, но заполнить по нему ничего было нельзя:
отметить выполнение и вписать сумму можно только у задачи со своими
кнопками, а в «Срочных» задача появляется лишь когда открылось её окно —
аренда с окном 25-30 числа до 25-го туда не попадала.
"""
import asyncio
from datetime import date

import pytest

from bot.handlers import tasks as tasks_handler
from bot.services import task_service
from database import repository
from database.init_db import init_db


class FakeMessage:
    def __init__(self):
        self.sent: list[tuple[str, object]] = []

    async def answer(self, text, reply_markup=None, **kwargs):
        self.sent.append((text, reply_markup))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "plan.db"
    init_db(path, apartments_count=1, nonresidential_count=0)
    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    return path


def _show(db) -> FakeMessage:
    message = FakeMessage()
    asyncio.run(tasks_handler.show_month_plan(message))
    return message


def test_every_task_comes_with_its_own_buttons(db):
    message = _show(db)
    header, *tasks = message.sent

    assert header[0].startswith("📅 <b>План на")
    assert header[1] is None                    # у заголовка кнопок нет

    conn = repository.connect()
    try:
        expected = repository.tasks_for_period(conn, tasks_handler._period_now())
    finally:
        conn.close()

    assert len(tasks) == len(expected)
    assert all(markup is not None for _, markup in tasks)


def test_rent_is_clickable_before_its_window_opens(db):
    """Аренду отмечают 25-30 числа, а увидеть и заполнить её нужно раньше."""
    message = _show(db)
    rent = next((text, markup) for text, markup in message.sent
                if "ренда за нежилое" in text)

    assert rent[1] is not None
    buttons = [b.text for row in rent[1].inline_keyboard for b in row]
    assert "✅ Выполнено" in buttons


def test_header_counts_what_is_done(db):
    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)
        rows = repository.tasks_for_period(conn, tasks_handler._period_now())
        repository.update_task(conn, rows[0]["id"], status="done",
                               done_at=date.today().isoformat())
        total = len(rows)
    finally:
        conn.close()

    header = _show(db).sent[0][0]
    assert f"Выполнено: 1 из {total}" in header
