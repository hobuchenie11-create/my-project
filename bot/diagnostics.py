"""Чтобы бот не молчал: журнал входящих и ответ при внутренней ошибке.

Показания жителя могут пропасть незаметно. Если обработчик падает с
ошибкой, aiogram пишет её в лог и на этом останавливается — человек не
получает вообще ничего и уверен, что бот «просто не обработал». Разобрать
такой случай потом тоже нечем: в журнале видно только то, что сообщение
успешно записано, а про упавшее нет ни строчки.

Здесь два сторожа:

* ``IncomingLogMiddleware`` — пишет в журнал каждое входящее сообщение
  ДО обработчиков. Даже если дальше всё рухнет, в логе останется, что
  именно пришло и от кого.
* ``setup_error_handler`` — ловит любую ошибку обработчика, пишет её со
  стеком и отвечает человеку, что показания не записаны и текст нужно
  прислать ещё раз. Молчание — худший из возможных ответов: житель
  считает показания переданными, а в ведомости их нет.
"""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import ErrorEvent, Message, TelegramObject

logger = logging.getLogger(__name__)

# Сколько текста сообщения писать в журнал. Показания короткие, а вот
# пересланная переписка бывает на сотню строк — она журнал только забьёт.
LOG_TEXT_LIMIT = 200

FAILURE_TEXT = (
    "⚠️ Не смог обработать это сообщение — внутри бота случилась ошибка.\n\n"
    "Показания <b>не записаны</b>. Пришлите их, пожалуйста, ещё раз — "
    "по одной квартире в сообщении. Если повторится, сообщите председателю: "
    "подробности ошибки уже записаны в журнал бота (logs/dhos.log)."
)


def _describe(message: Message) -> str:
    """Короткая строка о сообщении для журнала — без лишних переносов."""
    text = message.text or message.caption or ""
    text = text.replace("\n", " ⏎ ")
    if len(text) > LOG_TEXT_LIMIT:
        text = text[:LOG_TEXT_LIMIT] + "…"
    if not text:
        text = f"<{message.content_type}>"
    return text


class IncomingLogMiddleware(BaseMiddleware):
    """Пишет в журнал каждое входящее сообщение до его разбора."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                "Входящее [%s %s] от %s (%s): %s",
                event.chat.type, event.chat.id,
                user.full_name if user else "?",
                user.id if user else "?",
                _describe(event),
            )
        return await handler(event, data)


def _message_of(event: ErrorEvent) -> Message | None:
    """Сообщение, на котором всё сломалось, — чтобы ответить именно на него."""
    update = event.update
    if update.message is not None:
        return update.message
    if update.edited_message is not None:
        return update.edited_message
    if update.callback_query is not None:
        return update.callback_query.message
    return None


async def report_error(event: ErrorEvent) -> bool:
    """Любая ошибка обработчика — в журнал со стеком и ответ человеку."""
    message = _message_of(event)
    logger.error(
        "Ошибка при обработке сообщения%s: %s",
        f" «{_describe(message)}»" if message else "",
        event.exception,
        exc_info=event.exception,
    )

    if message is None:
        return True
    try:
        await message.answer(FAILURE_TEXT)
    except Exception:                     # noqa: BLE001 — молчим, но в журнал
        logger.exception("Не удалось даже сообщить об ошибке в чат")
    return True                           # ошибка обработана, бот работает дальше


def setup(dp: Dispatcher) -> None:
    """Подключает оба сторожа к диспетчеру."""
    dp.message.outer_middleware(IncomingLogMiddleware())
    dp.errors.register(report_error)
