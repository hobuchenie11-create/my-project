"""Фото бумажного бланка: полуавтомат вместо распознавания.

Жители заполняют бумажный бланк, председатель их фотографирует. Цифры с
фотографии бот не распознаёт — рукописные показания читаются ненадёжно, а
ошибка в одной цифре уходит в ведомость и в реестр ОЭК и находится только
через месяц, когда расход окажется отрицательным.

Поэтому работа устроена так: бот принимает снимок, спрашивает номер
квартиры и готовит форму под её приборы с прошлыми показаниями рядом.
Председатель переписывает цифры — проверку берёт на себя бот.

Раньше обработчика для фотографий не было вовсе: снимок не подходил ни
под один фильтр, и бот молчал. Со стороны это неотличимо от «принял».

Отдельный роутер, а не строчка в manual.py, потому что подключать его
надо раньше модуля задач: тот забирает любой присланный документ как
правки годового плана, а фотография, отправленная «файлом», приходит
именно документом.
"""
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.services import blank_service
from bot.services.parser import parse_message
from bot.states.photos import BlankPhoto
from database import repository

logger = logging.getLogger(__name__)

router = Router()

# Фото, отправленное «без сжатия», приходит документом с таким типом
IMAGE_MIME_PREFIX = "image/"

CANCEL_WORDS = ("отмена", "❌ отмена", "-", "нет")

ASK_NUMBER = (
    "📷 <b>Бланк принят.</b> Цифры с фотографии я не читаю — перепишем их "
    "вместе, так надёжнее.\n\n"
    "По какой квартире бланк? Отправьте номер: <code>54</code>.\n"
    "Или «отмена», если снимок не про показания."
)

RESIDENT_TEXT = (
    "📷 Фото я не читаю — показания с него не записаны.\n\n"
    "Пришлите, пожалуйста, цифры текстом:\n\n"
    "<code>Кв. 34\nЭл.эн 16553\nХвс 267\nГвс 215</code>\n\n"
    "Если счётчиков воды четыре, пишите по местам: «Хвс кухня», "
    "«Хвс санузел», «Гвс кухня», «Гвс санузел»."
)

NEWCOMER_TEXT = (
    "📷 Сюда документ присылать не нужно — копию выписки из ЕГРН отправьте "
    "председателю напрямую.\n\n"
    "А мы продолжим: допишите ответ на мой вопрос текстом."
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


def _number_from(text: str) -> str | None:
    """Номер помещения из текста: «54», «кв. 54», «нежилое 1»."""
    text = (text or "").strip()
    if text.isdigit():
        return text
    return parse_message(text).apartment_number


async def _send_form(message: Message, number: str) -> bool:
    """Готовит форму под бланк. False — помещение не нашли."""
    conn = repository.connect()
    try:
        apartment = repository.get_apartment_by_number(conn, number)
        if apartment is None:
            return False
        text = blank_service.form_text(conn, apartment)
    finally:
        conn.close()

    await message.answer(text)
    return True


@router.message(F.photo)
@router.message(F.document, _is_image_document)
async def handle_photo(message: Message, state: FSMContext) -> None:
    """Снимок бланка от председателя — полуавтомат; от жителя — объяснение."""
    # В чате Совета обсуждают дела дома и фотографии там свои — не мешаем
    if message.chat.id == config.council_chat_id:
        return

    is_private = message.chat.type == "private"
    is_admin = message.from_user.id in config.admin_ids

    logger.info("Фото от %s (%s), чат %s", message.from_user.full_name,
                message.from_user.id, message.chat.title or "личка")

    if not is_private:
        # В чате сообщение могли уже удалить — ответ «в никуда» бота не роняет
        try:
            await message.reply(CHAT_TEXT)
        except TelegramAPIError as exc:
            logger.warning("Не удалось ответить на фото в чате «%s»: %s",
                           message.chat.title, exc)
        return

    if not is_admin:
        # Житель оформляется как новый собственник и по привычке шлёт
        # выписку боту: про показания ему отвечать не о чем
        current = await state.get_state()
        if current and current.startswith("Newcomer:"):
            await message.answer(NEWCOMER_TEXT)
            return
        await message.answer(RESIDENT_TEXT)
        return

    # Номер бывает подписан прямо к снимку — тогда спрашивать незачем
    number = _number_from(message.caption or "")
    if number and await _send_form(message, number):
        return

    await state.set_state(BlankPhoto.number)
    await message.answer(ASK_NUMBER)


@router.message(BlankPhoto.number, F.text)
async def blank_apartment_number(message: Message, state: FSMContext) -> None:
    """Номер квартиры к присланному бланку — в ответ уходит форма."""
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await state.clear()
        await message.answer("Хорошо, бланк отложила.")
        return

    # Вместо номера сразу переписали показания — записываем их как обычно
    if not parse_message(text).is_empty:
        await state.clear()
        from bot.handlers.manual import manual_readings
        await manual_readings(message)
        return

    number = _number_from(text)
    if number is None or not await _send_form(message, number):
        await message.answer(
            f"Не нашла помещение «{text}». Пришлите номер ещё раз "
            "или «отмена».")
        return

    await state.clear()
