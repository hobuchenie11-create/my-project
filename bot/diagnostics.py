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
* ``report_error`` — ловит любую ошибку обработчика, пишет её со стеком и
  следит, чтобы человек не остался без ответа. Молчание — худший из
  возможных ответов: житель считает показания переданными, а в ведомости
  их нет.

Кому что говорим при ошибке:

* в общем чате дома — ничего. Разговоры про «внутреннюю ошибку бота» и
  журнал только пугают жителей и выглядят как поломка всего дома;
* жителю в личке — коротко и без техники: показания не приняты, пришлите
  ещё раз, не выйдет — передайте председателю;
* председателю в личку — подробности: из какого чата, от кого, что было
  в сообщении и где смотреть стек.
"""
import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, Dispatcher
from aiogram.types import ErrorEvent, Message, TelegramObject

from bot.config import config

logger = logging.getLogger(__name__)

# Сколько текста сообщения писать в журнал. Показания короткие, а вот
# пересланная переписка бывает на сотню строк — она журнал только забьёт.
LOG_TEXT_LIMIT = 200

# Председателю — с техникой: она знает, что делать с журналом
ADMIN_FAILURE_TEXT = (
    "⚠️ Не смог обработать это сообщение — внутри бота случилась ошибка.\n\n"
    "Показания <b>не записаны</b>. Пришлите их, пожалуйста, ещё раз — "
    "по одной квартире в сообщении. Подробности ошибки записаны в журнал "
    "бота (logs/dhos.log)."
)

# Жителю — только то, что ему делать. Ни «ошибки бота», ни журнала
RESIDENT_FAILURE_TEXT = (
    "⚠️ Показания не приняты. Пришлите их, пожалуйста, ещё раз — "
    "по одной квартире в сообщении.\n\n"
    "Если снова не получится, передайте показания председателю."
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


def _is_group(message: Message) -> bool:
    return message.chat.type in ("group", "supergroup")


def _admin_notice(message: Message, exception: BaseException) -> str:
    """Что показать председателю: откуда пришло, от кого и что сломалось."""
    user = message.from_user
    where = (f"в чате «{message.chat.title or message.chat.id}»"
             if _is_group(message) else "в личке")
    return (f"⚠️ <b>Ошибка при обработке сообщения</b> {where}.\n"
            f"От: {user.full_name if user else 'неизвестно'}\n\n"
            f"<code>{_describe(message)}</code>\n\n"
            f"{type(exception).__name__}: {exception}\n\n"
            "Показания <b>не записаны</b>. Подробности со стеком — "
            "в журнале бота (logs/dhos.log).")


async def _notify_admins(message: Message, exception: BaseException) -> None:
    """Подробности об ошибке уходят председателю в личку — и только ей."""
    bot = getattr(message, "bot", None)
    if bot is None:
        return
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, _admin_notice(message, exception))
        except Exception:                 # noqa: BLE001 — молчим, но в журнал
            logger.exception("Не удалось сообщить председателю %s об ошибке",
                             admin_id)


async def report_error(event: ErrorEvent) -> bool:
    """Любая ошибка обработчика — в журнал со стеком и ответ по адресу.

    В общий чат дома при ошибке не пишем ничего: жителей такие сообщения
    вводят в заблуждение — выглядит, будто сломалась вся система дома.
    Председатель получает разбор в личку, житель — короткую просьбу
    прислать показания ещё раз.
    """
    message = _message_of(event)
    logger.error(
        "Ошибка при обработке сообщения%s: %s",
        f" «{_describe(message)}»" if message else "",
        event.exception,
        exc_info=event.exception,
    )

    if message is None:
        return True

    user = message.from_user
    is_admin = bool(user and user.id in config.admin_ids)

    if _is_group(message):
        # В чат дома — ни слова: разбирается это в личке с председателем
        await _notify_admins(message, event.exception)
        return True

    try:
        await message.answer(ADMIN_FAILURE_TEXT if is_admin
                             else RESIDENT_FAILURE_TEXT)
    except Exception:                     # noqa: BLE001 — молчим, но в журнал
        logger.exception("Не удалось даже сообщить об ошибке в чат")

    if not is_admin:
        # Председатель должна знать, что у жителя не прошли показания
        await _notify_admins(message, event.exception)
    return True                           # ошибка обработана, бот работает дальше


# Через сколько неудачных попыток подряд писать подсказку про VPN. aiogram
# ждёт около пяти секунд между попытками, так что это примерно минута.
NETWORK_HINT_EVERY = 12

NETWORK_HINT = (
    "Нет связи с api.telegram.org. Чаще всего это выключенный VPN или "
    "прокси-клиент: включите его — бот подключится сам, перезапускать "
    "не нужно. Показания, присланные тем временем, Telegram хранит около "
    "суток и отдаст боту, как только связь появится."
)


class NetworkHintFilter(logging.Filter):
    """Объясняет по-русски, почему бот не может достучаться до Telegram.

    В журнале это выглядит как стена английских строк «Failed to fetch
    updates… tryings = 67», по которой непонятно, что делать. Раз в минуту
    дописываем рядом человеческую подсказку.
    """

    def __init__(self) -> None:
        super().__init__()
        self.failures = 0

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "Failed to fetch updates" not in message:
            if record.levelno < logging.WARNING:
                self.failures = 0     # связь восстановилась
            return True

        self.failures += 1
        if self.failures % NETWORK_HINT_EVERY == 1:
            logger.warning("%s (попыток подряд: %s)", NETWORK_HINT,
                           self.failures)
        return True


def setup(dp: Dispatcher) -> None:
    """Подключает сторожа к диспетчеру и к журналу."""
    dp.message.outer_middleware(IncomingLogMiddleware())
    dp.errors.register(report_error)
    logging.getLogger("aiogram.dispatcher").addFilter(NetworkHintFilter())
