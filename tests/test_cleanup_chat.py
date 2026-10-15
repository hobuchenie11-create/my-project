"""Кнопка «Очистить переписку»: бот убирает за собой ленту в Telegram."""
import asyncio
from types import SimpleNamespace

import pytest
from aiogram.exceptions import TelegramAPIError

from bot.handlers import admin

CHAIRMAN = 555


class CleaningBot:
    """Telegram, который не даёт удалять чужое и слишком старое."""

    def __init__(self, deletable: set[int]):
        self.deletable = deletable
        self.deleted: list[int] = []
        self.sent: list[str] = []

    async def delete_message(self, chat_id, message_id):
        if message_id not in self.deletable:
            raise TelegramAPIError(method=None, message="message can't be deleted")
        self.deleted.append(message_id)
        return True

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append(text)


class Callback:
    def __init__(self, data, bot, message_id=1000):
        self.data = data
        self.bot = bot
        self.answered = None
        self.edited: list[str] = []
        self.message = SimpleNamespace(
            chat=SimpleNamespace(id=CHAIRMAN, type="private"),
            message_id=message_id,
            edit_text=self._edit,
            answer=self._answer,
        )
        self.answers: list[str] = []

    async def _edit(self, text, **kwargs):
        self.edited.append(text)

    async def _answer(self, text, **kwargs):
        self.answers.append(text)

    async def answer(self, text=None, **kwargs):
        self.answered = text


@pytest.fixture(autouse=True)
def fast(monkeypatch):
    """Паузы между партиями в тесте не нужны."""
    async def no_sleep(_seconds):
        return None

    monkeypatch.setattr(admin.asyncio, "sleep", no_sleep)


def test_only_what_telegram_allows_is_deleted():
    """Старые и чужие сообщения не удаляются — и не ломают очистку."""
    bot = CleaningBot(deletable={1000, 999, 998, 900})
    callback = Callback("cleanup:yes", bot)

    asyncio.run(admin.do_cleanup(callback))

    assert sorted(bot.deleted) == [900, 998, 999, 1000]
    assert "Удалено сообщений: 4" in bot.sent[0]
    assert "48 часов" in bot.sent[0]            # почему убралось не всё


def test_cleanup_does_not_dig_deeper_than_the_limit():
    bot = CleaningBot(deletable=set(range(1, 1001)))
    callback = Callback("cleanup:yes", bot)

    asyncio.run(admin.do_cleanup(callback))

    assert len(bot.deleted) == admin.CLEANUP_DEPTH
    assert min(bot.deleted) == 1000 - admin.CLEANUP_DEPTH + 1


def test_cleanup_asks_before_doing_it():
    bot = CleaningBot(deletable={1000})
    callback = Callback("cleanup:no", bot)

    asyncio.run(admin.cancel_cleanup(callback))

    assert bot.deleted == []
    assert "оставила как есть" in callback.edited[0]


def test_warning_says_the_data_is_safe():
    """Жительнице важно знать, что показания от очистки не пострадают."""
    class Msg:
        def __init__(self):
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    message = Msg()
    asyncio.run(admin.ask_cleanup(message))

    text = message.answers[0]
    assert "не трогает" in text
    assert "48 часов" in text
