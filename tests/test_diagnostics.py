"""Бот не должен молчать: журнал входящих и ответ при внутренней ошибке."""
import asyncio
import logging
from datetime import datetime
from types import SimpleNamespace

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


class FakeMessage:
    """Сообщение, пришедшее боту. Ответы складываем в список."""

    def __init__(self, text="Кв 31\nЭлект. 29814", chat_type="private"):
        self.text = text
        self.caption = None
        self.content_type = "text"
        self.chat = SimpleNamespace(id=-100123, type=chat_type)
        self.from_user = SimpleNamespace(id=777, full_name="Елена Викторовна")
        self.replies: list[str] = []

    async def answer(self, text, **kwargs):
        self.replies.append(text)


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


def test_handler_failure_answers_instead_of_silence(caplog):
    """Обработчик упал — человек получает ответ, а не тишину."""
    message = FakeMessage()

    with caplog.at_level(logging.ERROR, logger="bot.diagnostics"):
        handled = asyncio.run(diagnostics.report_error(_error(message)))

    assert handled is True
    assert message.replies, "бот промолчал в ответ на ошибку"
    assert "не записаны" in message.replies[0]
    assert "ещё раз" in message.replies[0]
    assert "Кв 31" in caplog.text                 # видно, на чём упало
    assert "что-то пошло не так" in caplog.text   # и сама ошибка
    assert "ValueError" in caplog.text            # вместе со стеком


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
