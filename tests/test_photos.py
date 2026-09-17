"""Снимок бланка или счётчика: бот его не читает, но и не молчит.

Молчание в ответ на фотографию неотличимо от «принял»: житель уверен,
что показания переданы, а в ведомости их нет.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import photos

CHAIRMAN = 555
RESIDENT = 777


class Msg:
    def __init__(self, chat_type="private", tg_id=CHAIRMAN, chat_id=None,
                 mime=None):
        self.from_user = SimpleNamespace(id=tg_id, full_name="Житель")
        self.chat = SimpleNamespace(
            id=chat_id if chat_id is not None else -100123,
            type=chat_type, title="Дом")
        self.document = SimpleNamespace(mime_type=mime) if mime else None
        self.answers: list[str] = []
        self.replies: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)

    async def reply(self, text, **kwargs):
        self.replies.append(text)


@pytest.fixture(autouse=True)
def chairman_is_admin(monkeypatch):
    monkeypatch.setattr(photos, "config",
                        replace(photos.config, admin_ids=(CHAIRMAN,),
                                council_chat_id=-500))


def test_resident_is_told_the_photo_was_not_read():
    message = Msg(tg_id=RESIDENT)
    asyncio.run(photos.refuse_photo(message))

    answer = message.answers[0]
    assert "не записаны" in answer
    assert "Хвс 267" in answer            # готовый образец под рукой
    assert "кухня" in answer              # и подсказка про четыре счётчика


def test_chairman_gets_the_batch_hint():
    """Председатель переписывает бланки пачкой — ей нужен другой совет."""
    message = Msg(tg_id=CHAIRMAN)
    asyncio.run(photos.refuse_photo(message))

    answer = message.answers[0]
    assert "несколько квартир" in answer
    assert "сводкой" in answer


def test_photo_in_the_house_chat_gets_a_short_reply():
    message = Msg(chat_type="supergroup", tg_id=RESIDENT)
    asyncio.run(photos.refuse_photo(message))

    assert message.replies and "не записаны" in message.replies[0]
    assert message.answers == []


def test_council_chat_is_left_alone():
    """В чате Совета свои фотографии — актов, счетов, подъездов."""
    message = Msg(chat_type="supergroup", tg_id=CHAIRMAN, chat_id=-500)
    asyncio.run(photos.refuse_photo(message))

    assert message.replies == [] and message.answers == []


def test_a_deleted_message_in_the_chat_does_not_break_the_bot():
    from aiogram.exceptions import TelegramBadRequest

    message = Msg(chat_type="supergroup", tg_id=RESIDENT)

    async def refuse(text, **kwargs):
        raise TelegramBadRequest(method=SimpleNamespace(),
                                 message="message to be replied not found")

    message.reply = refuse
    asyncio.run(photos.refuse_photo(message))      # не должно упасть


@pytest.mark.parametrize("mime, expected", [
    ("image/jpeg", True),
    ("image/png", True),
    ("application/vnd.ms-excel", False),
    (None, False),
])
def test_image_sent_as_a_file_is_recognised(mime, expected):
    """Фото «без сжатия» приходит документом — иначе его заберёт модуль задач."""
    assert photos._is_image_document(Msg(mime=mime)) is expected
