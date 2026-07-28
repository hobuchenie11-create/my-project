"""Прием показаний из общего чата дома.

Бот разбирает сообщения по шаблонам жителей (см. bot/services/parser.py):

    Кв. 12
    Эл.эн 15230
    хвс (кухня) 123,45
    ...

Подтверждение о приёме бот присылает жителю в личные сообщения, а в общем
чате лишь ставит тихую отметку 👍, чтобы не засорять чат. Текст в чат
попадает только при проблеме, когда в личку написать не удалось (например,
житель ещё ни разу не запускал бота командой /start).
"""
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message, ReactionTypeEmoji

from bot.config import config
from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, receipt_text,
                                          save_parsed_readings)
from database import repository

logger = logging.getLogger(__name__)
router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))

# Чтобы не засорять лог, ID чата подсказываем один раз за запуск
_hinted_chats: set[int] = set()

_START_HINT = "\n\n(Чтобы получать подтверждения лично, напишите боту в личку — команда /start.)"


async def _dm(message: Message, text: str) -> bool:
    """Пробует отправить сообщение отправителю в личку. True, если получилось."""
    try:
        await message.bot.send_message(message.from_user.id, text)
        return True
    except TelegramAPIError:
        return False  # житель не запускал бота в личке — написать нельзя


async def _react_ok(message: Message) -> None:
    """Тихая отметка в чате, что показание принято (без текстового сообщения)."""
    try:
        await message.bot.set_message_reaction(
            chat_id=message.chat.id, message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji="👍")])
    except TelegramAPIError:
        pass  # в чате запрещены реакции — не критично


@router.message(F.text)
async def handle_group_message(message: Message) -> None:
    if config.group_chat_id and message.chat.id != config.group_chat_id:
        return

    # Пока GROUP_CHAT_ID не задан — подсказываем его в терминале (без сообщений в чат)
    if config.group_chat_id is None and message.chat.id not in _hinted_chats:
        _hinted_chats.add(message.chat.id)
        logger.info("Чат «%s»: GROUP_CHAT_ID=%s (впишите в .env, чтобы собирать "
                    "показания только отсюда)", message.chat.title, message.chat.id)

    parsed = parse_message(message.text)
    if parsed.is_empty and not parsed.apartment_number:
        return  # обычное сообщение в чате — не мешаем

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)

        apartment = None
        if parsed.apartment_number:
            apartment = repository.get_apartment_by_number(conn, parsed.apartment_number)
        elif user and user["apartment_id"]:
            apartment = repository.get_apartment_by_id(conn, user["apartment_id"])

        if apartment is None:
            if parsed.is_empty:
                return
            await _guidance(message, "Не понял, к какой квартире относятся показания. "
                                     "Укажите в первой строке «Кв. <номер>».")
            return

        if parsed.is_empty:
            await _guidance(message, "Вижу номер квартиры, но не разобрал показания. "
                                     "Пришлите по шаблону, например: «Эл.эн 15230», "
                                     "«хвс кухня 123,45».")
            return

        outcome = save_parsed_readings(conn, apartment, parsed,
                                       user["id"] if user else None, source="chat")
        repository.log_event(conn, message.from_user.id, "reading_chat",
                             f"{apartment['number']}: принято {len(outcome.saved)} "
                             f"за {current_period()}")

        receipt = (receipt_text(conn, apartment, outcome.saved)
                   if outcome.anything_saved else "Показания не записаны.")
    finally:
        conn.close()

    problems = list(outcome.warnings) + list(outcome.errors)
    if parsed.ignored:
        problems.append("Не учитывается: " + ", ".join(parsed.ignored))
    problems_text = "\n".join(f"⚠️ {p}" for p in problems)

    # Тихая отметка в чате, если что-то записали
    if outcome.anything_saved:
        await _react_ok(message)

    # Подтверждение — в личку жителю
    dm_text = receipt + ("\n\n" + problems_text if problems else "")
    delivered = await _dm(message, dm_text)

    # В чат пишем только если в личку не дошло И есть о чём предупредить
    if not delivered and problems:
        await message.reply(problems_text + _START_HINT)


async def _guidance(message: Message, text: str) -> None:
    """Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её увидеть)."""
    if not await _dm(message, text):
        await message.reply(text + _START_HINT)
