"""Фото и сканы: бот их не читает, но и молчать в ответ не должен.

Жители фотографируют бумажный бланк или сам счётчик и присылают снимок.
Распознавания в системе нет, и обработчика для фотографий раньше тоже не
было — снимок просто не подходил ни под один фильтр, и бот молчал. Со
стороны это неотличимо от «принял»: человек уверен, что показания
переданы, а в ведомости их нет.

Отдельный роутер, а не строчка в manual.py, потому что подключать его
надо раньше модуля задач: тот забирает любой присланный документ как
правки годового плана, а фотография, отправленная «файлом», приходит
именно документом.
"""
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from bot.config import config

logger = logging.getLogger(__name__)

router = Router()

# Фото, отправленное «без сжатия», приходит документом с таким типом
IMAGE_MIME_PREFIX = "image/"

EXAMPLE = ("<code>Кв. 34\n"
           "Эл.эн 16553\n"
           "Хвс 267\n"
           "Гвс 215</code>")

RESIDENT_TEXT = (
    "📷 Фото я не читаю — показания с него не записаны.\n\n"
    "Пришлите, пожалуйста, цифры текстом:\n\n" + EXAMPLE + "\n\n"
    "Если счётчиков воды четыре, пишите по местам: «Хвс кухня», "
    "«Хвс санузел», «Гвс кухня», «Гвс санузел»."
)

CHAIRMAN_TEXT = (
    "📷 Фото я не читаю — показания с него не записаны.\n\n"
    "Перепишите бланк текстом, можно сразу несколько квартир одним "
    "сообщением — каждую с новой строки «Кв. …»:\n\n" + EXAMPLE + "\n\n"
    "Разберу по квартирам сам и отвечу одной сводкой."
)

CHAT_TEXT = (
    "📷 Фото я не читаю — показания с него не записаны. "
    "Пришлите, пожалуйста, цифры текстом: «Кв. 34 / Эл.эн 16553 / "
    "Хвс 267 / Гвс 215»."
)


def _is_image_document(message: Message) -> bool:
    """Снимок, отправленный файлом, а не картинкой."""
    document = message.document
    return bool(document and (document.mime_type or "")
                .startswith(IMAGE_MIME_PREFIX))


@router.message(F.photo)
@router.message(F.document, _is_image_document)
async def refuse_photo(message: Message) -> None:
    """Отвечает, что снимок не прочитан, и показывает, как прислать цифры."""
    # В чате Совета обсуждают дела дома и фотографии там свои — не мешаем
    if message.chat.id == config.council_chat_id:
        return

    is_private = message.chat.type == "private"
    is_admin = message.from_user.id in config.admin_ids

    logger.info("Фото от %s (%s) в чате %s — разбор не поддерживается",
                message.from_user.full_name, message.from_user.id,
                message.chat.title or "личка")

    if is_private:
        await message.answer(CHAIRMAN_TEXT if is_admin else RESIDENT_TEXT)
        return

    # В чате сообщение могли уже удалить — ответ «в никуда» бота не роняет
    try:
        await message.reply(CHAT_TEXT)
    except TelegramAPIError as exc:
        logger.warning("Не удалось ответить на фото в чате «%s»: %s",
                       message.chat.title, exc)
