"""Сводка для Совета дома уходит в свой чат, а не в чат показаний."""
import asyncio
from types import SimpleNamespace

import pytest

from bot.handlers import tasks as tasks_handler
from bot.services import task_service
from database import repository
from database.init_db import init_db

GROUP_CHAT = -1001111111111      # чат дома: там жители передают показания
COUNCIL_CHAT = -1002222222222    # чат Совета дома: туда сводка


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


class FakeMessage:
    def __init__(self):
        self.bot = FakeBot()
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


@pytest.fixture()
def digest_env(tmp_path, monkeypatch):
    db = tmp_path / "council.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    task_service.generate_tasks(conn, months_ahead=0)
    conn.close()

    # Обработчик открывает базу сам — подставляем тестовую
    real_connect = repository.connect
    monkeypatch.setattr(tasks_handler.repository, "connect",
                        lambda *a, **kw: real_connect(db))
    return db


def _run(message):
    asyncio.run(tasks_handler.send_council_digest(message))


def test_digest_goes_to_the_council_chat(digest_env, monkeypatch):
    monkeypatch.setattr(tasks_handler, "config",
                        SimpleNamespace(group_chat_id=GROUP_CHAT,
                                        council_chat_id=COUNCIL_CHAT))
    message = FakeMessage()
    _run(message)

    assert [chat for chat, _ in message.bot.sent] == [COUNCIL_CHAT]
    assert "Совет дома" in message.bot.sent[0][1]
    assert "Совета дома" in message.answers[0]


def test_digest_never_goes_to_the_readings_chat(digest_env, monkeypatch):
    """Чат показаний подключён, чат Совета — нет: в чат жителей не пишем."""
    monkeypatch.setattr(tasks_handler, "config",
                        SimpleNamespace(group_chat_id=GROUP_CHAT,
                                        council_chat_id=None))
    message = FakeMessage()
    _run(message)

    assert message.bot.sent == []                     # в чат дома — ничего
    assert "COUNCIL_CHAT_ID" in message.answers[0]    # подсказка, как подключить
    assert "Совет дома" in message.answers[-1]        # текст сводки — председателю


def test_readings_are_not_collected_in_the_council_chat():
    """Обсуждения Совета не разбираются как показания."""
    import inspect

    from bot.handlers import group

    source = inspect.getsource(group.handle_group_message)
    assert "council_chat_id" in source
