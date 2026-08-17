"""Приём показаний из общего чата: в чью квартиру они попадают."""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import group
from database import repository
from database.init_db import init_db


class FakeBot:
    def __init__(self):
        self.dm: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.dm.append((chat_id, text))

    async def set_message_reaction(self, **kwargs):
        pass


class FakeMessage:
    """Сообщение в общем чате дома от жителя."""

    def __init__(self, text, tg_id=555):
        self.text = text
        self.message_id = 1
        self.bot = FakeBot()
        self.chat = SimpleNamespace(id=-100123, type="supergroup", title="Дом")
        self.from_user = SimpleNamespace(id=tg_id, username="rezident")
        self.replies: list[str] = []

    async def reply(self, text, **kwargs):
        self.replies.append(text)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "group.db"
    init_db(path, apartments_count=50, nonresidential_count=1)
    conn = repository.connect(path)
    # Житель зарегистрирован как кв. 49, но пишет показания за кв. 29
    apartment_49 = repository.get_apartment_by_number(conn, "49")
    repository.create_user(conn, 555, "Житель", apartment_49["id"])
    conn.close()

    real_connect = repository.connect
    monkeypatch.setattr(group.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    # config — frozen dataclass, поэтому подменяем не поле, а копию целиком
    monkeypatch.setattr(group, "config",
                        replace(group.config, group_chat_id=-100123))
    return path


def _readings(db, number):
    conn = repository.connect(db)
    try:
        apartment = repository.get_apartment_by_number(conn, number)
        rows = repository.readings_history_for_apartment(conn, apartment["id"])
        return {r["kind"]: r["value"] for r in rows}
    finally:
        conn.close()


def test_readings_go_to_the_flat_named_in_the_message(db):
    """«Кв,, 29» от жителя кв. 49 — записываем в 29-ю, а не в квартиру автора."""
    message = FakeMessage("Кв,, 29\nЭлектро 12254\nХв,кух,36\nСан,уз,,229\n"
                          "Гв,кух,,114\nГв, ванная, 179\nСум,,гв,,293")
    asyncio.run(group.handle_group_message(message))

    assert _readings(db, "29")["electricity"] == 12254.0
    assert _readings(db, "49") == {}          # чужая квартира не тронута

    receipt = message.bot.dm[0][1]
    assert "кв. 29" in receipt


def test_unreadable_number_saves_nothing(db):
    """Номер назвали, но не прочитали — лучше переспросить, чем угадать."""
    message = FakeMessage("Кв.\nЭлектро 12254\nХвс 36")
    asyncio.run(group.handle_group_message(message))

    assert _readings(db, "49") == {}          # в квартиру отправителя не пишем
    assert "не разобрал номер квартиры" in message.bot.dm[0][1]


def test_message_without_a_number_uses_the_sender_flat(db):
    """Номер не назван вовсе — берём квартиру из регистрации, это привычно."""
    message = FakeMessage("Хвс 36\nГвс 42")
    asyncio.run(group.handle_group_message(message))

    assert _readings(db, "49")["cws"] == 36.0


def test_ordinary_chat_message_is_ignored(db):
    message = FakeMessage("Добрый день! Когда будет собрание?")
    asyncio.run(group.handle_group_message(message))

    assert message.bot.dm == []
    assert message.replies == []


def test_message_from_another_chat_is_logged_not_swallowed(db, caplog, monkeypatch):
    """Чужой чат — предупреждение в лог: так видно смену ID чата дома."""
    monkeypatch.setattr(group, "config",
                        replace(group.config, group_chat_id=-100999))
    group._hinted_chats.clear()

    message = FakeMessage("Кв. 5\nХвс 30")
    with caplog.at_level("WARNING"):
        asyncio.run(group.handle_group_message(message))

    assert _readings(db, "5") == {}                  # ничего не записали
    assert "GROUP_CHAT_ID" in caplog.text
    assert str(message.chat.id) in caplog.text


def test_council_chat_is_skipped_before_the_id_check(db, monkeypatch):
    monkeypatch.setattr(group, "config",
                        replace(group.config, group_chat_id=None,
                                council_chat_id=-100123))
    message = FakeMessage("Кв. 5\nХвс 30")
    asyncio.run(group.handle_group_message(message))

    assert _readings(db, "5") == {}


def test_reaction_failure_is_logged(db, caplog):
    """Реакции в чате запрещены: показания записаны, но это должно быть видно."""
    from aiogram.exceptions import TelegramBadRequest

    message = FakeMessage("Кв. 5\nХвс 30")

    async def refuse(**kwargs):
        raise TelegramBadRequest(method=None, message="REACTION_INVALID")

    message.bot.set_message_reaction = refuse
    with caplog.at_level("WARNING"):
        asyncio.run(group.handle_group_message(message))

    assert _readings(db, "5")["cws"] == 30.0          # записали
    assert "Не удалось поставить" in caplog.text


def test_resident_is_answered_when_nothing_else_reaches_them(db):
    """Ни реакции, ни лички — отвечаем в чате, иначе житель без подтверждения."""
    from aiogram.exceptions import TelegramBadRequest

    message = FakeMessage("Кв. 5\nХвс 30", tg_id=777)   # не запускал бота

    async def refuse(*args, **kwargs):
        raise TelegramBadRequest(method=None, message="blocked")

    message.bot.set_message_reaction = refuse
    message.bot.send_message = refuse
    asyncio.run(group.handle_group_message(message))

    assert message.replies and "показания приняты" in message.replies[0]


def test_accepted_readings_are_logged(db, caplog):
    message = FakeMessage("Кв. 5\nХвс 30\nГвс 42")
    with caplog.at_level("INFO"):
        asyncio.run(group.handle_group_message(message))

    assert "записано показаний 2" in caplog.text
