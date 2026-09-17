"""Бот не должен молчать: журнал входящих и ответ при внутренней ошибке."""
import asyncio
import logging
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace

import pytest
from aiogram.types import Chat, Message, User

from bot import diagnostics


def real_message(text: str) -> Message:
    """Настоящее сообщение aiogram — журнал входящих смотрит именно на него."""
    return Message(
        message_id=1, date=datetime.now(),
        chat=Chat(id=-100123, type="private"),
        from_user=User(id=777, is_bot=False, first_name="Елена",
                       last_name="Викторовна"),
        text=text)


CHAIRMAN = 555
RESIDENT = 777


class FakeBot:
    """Личка: что и кому бот отправил помимо ответа на сообщение."""

    def __init__(self):
        self.dm: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.dm.append((chat_id, text))


class FakeMessage:
    """Сообщение, пришедшее боту. Ответы складываем в список."""

    def __init__(self, text="Кв 31\nЭлект. 29814", chat_type="private",
                 tg_id=CHAIRMAN):
        self.text = text
        self.caption = None
        self.content_type = "text"
        self.chat = SimpleNamespace(id=-100123, type=chat_type, title="Дом")
        self.from_user = SimpleNamespace(id=tg_id, full_name="Елена Викторовна")
        self.replies: list[str] = []
        self.bot = FakeBot()

    async def answer(self, text, **kwargs):
        self.replies.append(text)


@pytest.fixture(autouse=True)
def chairman_is_admin(monkeypatch):
    """Config заморожен — подменяем копию целиком, а не отдельное поле."""
    monkeypatch.setattr(diagnostics, "config",
                        replace(diagnostics.config, admin_ids=(CHAIRMAN,)))


def _update(message=None):
    return SimpleNamespace(message=message, edited_message=None,
                           callback_query=None)


def _error(message=None, exc=None):
    return SimpleNamespace(update=_update(message),
                           exception=exc or ValueError("что-то пошло не так"))


def test_incoming_message_is_logged_before_handlers(caplog):
    """Даже если дальше всё упадёт, в журнале останется, что пришло."""
    message = real_message("Кв 31\nЭлект. 29814\nХвс 304\nГвс 140С")
    middleware = diagnostics.IncomingLogMiddleware()
    seen = []

    async def handler(event, data):
        seen.append(event)
        return "ok"

    with caplog.at_level(logging.INFO, logger="bot.diagnostics"):
        result = asyncio.run(middleware(handler, message, {}))

    assert result == "ok" and seen == [message]
    assert "Входящее" in caplog.text
    assert "Кв 31" in caplog.text
    assert "Гвс 140С" in caplog.text


def test_long_message_is_trimmed_in_the_log(caplog):
    """Пересланная переписка не должна забивать журнал целиком."""
    message = real_message("Кв 1\n" + "Хвс 100\n" * 200)
    middleware = diagnostics.IncomingLogMiddleware()

    async def handler(event, data):
        return None

    with caplog.at_level(logging.INFO, logger="bot.diagnostics"):
        asyncio.run(middleware(handler, message, {}))

    line = caplog.records[0].getMessage()
    assert "…" in line
    assert len(line) < diagnostics.LOG_TEXT_LIMIT + 200


def test_non_message_events_pass_through():
    """Нажатие кнопки через журнал сообщений проходит без изменений."""
    middleware = diagnostics.IncomingLogMiddleware()
    callback = SimpleNamespace(data="task:done:5")

    async def handler(event, data):
        return "готово"

    assert asyncio.run(middleware(handler, callback, {})) == "готово"


def test_chairman_gets_the_technical_answer(caplog):
    """Обработчик упал — председатель получает ответ, а не тишину."""
    message = FakeMessage(tg_id=CHAIRMAN)

    with caplog.at_level(logging.ERROR, logger="bot.diagnostics"):
        handled = asyncio.run(diagnostics.report_error(_error(message)))

    assert handled is True
    assert message.replies, "бот промолчал в ответ на ошибку"
    assert "не записаны" in message.replies[0]
    assert "logs/dhos.log" in message.replies[0]
    assert "Кв 31" in caplog.text                 # видно, на чём упало
    assert "что-то пошло не так" in caplog.text   # и сама ошибка
    assert "ValueError" in caplog.text            # вместе со стеком


def test_resident_gets_a_plain_answer_without_the_technical_part():
    """Жителя «внутренняя ошибка бота» и журнал только путают."""
    message = FakeMessage(tg_id=RESIDENT)

    asyncio.run(diagnostics.report_error(_error(message)))

    answer = message.replies[0]
    assert "не приняты" in answer
    assert "ещё раз" in answer
    assert "ошибка" not in answer.lower()
    assert "dhos.log" not in answer
    # а председателю при этом ушёл разбор
    assert message.bot.dm and message.bot.dm[0][0] == CHAIRMAN
    assert "Кв 31" in message.bot.dm[0][1]


def test_house_chat_hears_nothing_at_all():
    """В чат дома при ошибке не пишем ничего — жителей это пугает."""
    message = FakeMessage(chat_type="supergroup", tg_id=RESIDENT)

    asyncio.run(diagnostics.report_error(_error(message)))

    assert message.replies == [], "в общем чате бот должен промолчать"
    assert message.bot.dm, "но председателю сообщить обязан"
    chat_id, text = message.bot.dm[0]
    assert chat_id == CHAIRMAN
    assert "в чате «Дом»" in text
    assert "Елена Викторовна" in text
    assert "ValueError" in text


def test_failure_without_message_is_only_logged(caplog):
    """Ошибка не на сообщении — отвечать некому, но в журнал попадает."""
    with caplog.at_level(logging.ERROR, logger="bot.diagnostics"):
        handled = asyncio.run(
            diagnostics.report_error(_error(None, RuntimeError("нет чата"))))

    assert handled is True
    assert "нет чата" in caplog.text


def test_failure_answer_that_itself_fails_does_not_break_the_bot(caplog):
    """Даже если ответить не вышло (жителя нет в личке) — бот живёт дальше."""
    message = FakeMessage()

    async def refuse(text, **kwargs):
        raise RuntimeError("chat not found")

    message.answer = refuse

    with caplog.at_level(logging.ERROR, logger="bot.diagnostics"):
        handled = asyncio.run(diagnostics.report_error(_error(message)))

    assert handled is True
    assert "Не удалось даже сообщить об ошибке" in caplog.text


def test_network_failures_get_a_hint_in_russian(caplog):
    """Стена «Failed to fetch updates» ничего не объясняет — дописываем почему."""
    hint = diagnostics.NetworkHintFilter()
    dispatcher = logging.getLogger("aiogram.dispatcher")

    with caplog.at_level(logging.WARNING):
        for _ in range(diagnostics.NETWORK_HINT_EVERY + 1):
            hint.filter(dispatcher.makeRecord(
                "aiogram.dispatcher", logging.ERROR, __file__, 1,
                "Failed to fetch updates - TelegramNetworkError", (), None))

    hints = [r for r in caplog.records if "api.telegram.org" in r.getMessage()]
    assert len(hints) == 2, "подсказка раз в минуту, а не на каждую попытку"
    assert "VPN" in hints[0].getMessage()
    assert "перезапускать" in hints[0].getMessage()


def test_counter_resets_once_the_connection_is_back():
    """Связь вернулась — счётчик обнуляется, и следующий обрыв снова объяснён."""
    hint = diagnostics.NetworkHintFilter()
    for _ in range(5):
        hint.filter(logging.LogRecord("aiogram.dispatcher", logging.ERROR,
                                      __file__, 1,
                                      "Failed to fetch updates", (), None))
    assert hint.failures == 5

    hint.filter(logging.LogRecord("aiogram.dispatcher", logging.INFO,
                                  __file__, 1, "Update id=1 is handled",
                                  (), None))
    assert hint.failures == 0


def test_other_log_lines_pass_through_untouched():
    hint = diagnostics.NetworkHintFilter()
    record = logging.LogRecord("aiogram.dispatcher", logging.INFO, __file__, 1,
                               "Start polling", (), None)
    assert hint.filter(record) is True
