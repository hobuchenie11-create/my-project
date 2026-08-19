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
from bot.services.batch_service import import_batch
from bot.services.parser import parse_message, split_messages
from bot.services.reading_service import (current_period, is_late, receipt_text,
                                          save_parsed_readings)
from bot.texts import late_submission_text
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


async def _react_ok(message: Message) -> bool:
    """Тихая отметка в чате, что показание принято (без текстового сообщения)."""
    try:
        await message.bot.set_message_reaction(
            chat_id=message.chat.id, message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji="👍")])
        return True
    except TelegramAPIError as exc:
        # Реакции в чате могут быть запрещены настройками группы. Показания
        # при этом записаны — но в чате не видно ни одной отметки, и со
        # стороны это выглядит как «бот перестал работать».
        logger.warning("Не удалось поставить 👍 в чате «%s»: %s. Показания "
                       "записаны, но отметки в чате не будет.",
                       message.chat.title, exc)
        return False


@router.message(F.text)
async def handle_group_message(message: Message) -> None:
    # В чате Совета дома показания не собираем — там обсуждения, а не цифры
    if message.chat.id == config.council_chat_id:
        return

    if config.group_chat_id and message.chat.id != config.group_chat_id:
        # Чужой чат — либо и правда чужой, либо ID чата дома изменился
        # (так бывает, когда группу повышают до супергруппы). Молчать об этом
        # нельзя: со стороны выглядит как «бот перестал видеть показания».
        if message.chat.id not in _hinted_chats:
            _hinted_chats.add(message.chat.id)
            logger.warning(
                "Сообщение из чата «%s» (ID %s) пропущено: в .env указан "
                "GROUP_CHAT_ID=%s. Если показания шлют именно сюда — впишите "
                "в .env этот ID и перезапустите бота.",
                message.chat.title, message.chat.id, config.group_chat_id)
        return

    # Пока GROUP_CHAT_ID не задан — подсказываем его в терминале (без сообщений в чат)
    if config.group_chat_id is None and message.chat.id not in _hinted_chats:
        _hinted_chats.add(message.chat.id)
        logger.info("Чат «%s»: GROUP_CHAT_ID=%s (впишите в .env, чтобы собирать "
                    "показания только отсюда)", message.chat.title, message.chat.id)

    # В чат вставили несколько сообщений сразу (перенос из WhatsApp).
    # Разбирать их как одно нельзя: показания всех квартир ушли бы в первую.
    blocks = split_messages(message.text)
    if len(blocks) > 1:
        await _handle_batch(message, blocks)
        return

    parsed = parse_message(message.text)
    if parsed.is_empty and not parsed.apartment_number:
        return  # обычное сообщение в чате — не мешаем

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)

        apartment = None
        if parsed.apartment_number:
            apartment = repository.get_apartment_by_number(conn, parsed.apartment_number)
        elif parsed.apartment_unreadable:
            # Номер квартиры назвали, но прочитать не смогли. Подставить
            # квартиру отправителя нельзя: показания уйдут не туда.
            pass
        elif user and user["apartment_id"]:
            apartment = repository.get_apartment_by_id(conn, user["apartment_id"])

        if apartment is None:
            if parsed.is_empty:
                return
            if parsed.apartment_unreadable:
                await _guidance(
                    message, "Вижу показания, но не разобрал номер квартиры. "
                             "Пришлите ещё раз, указав его в первой строке — "
                             "например «Кв. 29». Показания не записаны.")
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

    # Видно прямо в терминале: что пришло из чата и чем закончилось
    logger.info("Чат: %s — записано показаний %s%s", apartment["number"],
                len(outcome.saved),
                f", отклонено {len(outcome.errors)}" if outcome.errors else "")

    problems = list(outcome.warnings) + list(outcome.errors)
    if parsed.ignored:
        problems.append("Не учитывается: " + ", ".join(parsed.ignored))
    problems_text = "\n".join(f"⚠️ {p}" for p in problems)

    # Отметка в чате, что показания приняты
    if outcome.anything_saved:
        await _confirm_in_chat(message, apartment)

    # Подтверждение — в личку жителю
    dm_text = receipt + ("\n\n" + problems_text if problems else "")
    if outcome.anything_saved and is_late():
        dm_text += "\n\n" + late_submission_text()
    delivered = await _dm(message, dm_text)

    # В чат пишем только если в личку не дошло И есть о чём предупредить
    if not delivered and problems:
        await message.reply(problems_text + _START_HINT)


async def _confirm_in_chat(message: Message, apartment) -> None:
    """Подтверждение приёма в чате — способом из CHAT_CONFIRM.

    Реакции в группе можно запретить настройками, и тогда единственный
    видимый признак приёма пропадает. Поэтому по умолчанию (`auto`) при
    неудачной реакции бот отвечает короткой строкой.
    """
    mode = config.chat_confirm
    if mode == "off":
        return

    if mode in ("auto", "reaction") and await _react_ok(message):
        return
    if mode == "reaction":
        return

    await message.reply(f"✅ {apartment['number']}: показания приняты")


async def _handle_batch(message: Message, blocks: list[str]) -> None:
    """Пачка сообщений в чате. Разносит её только председатель.

    У жителя такое сообщение — это показания за несколько квартир сразу;
    записывать чужие с его слов нельзя, поэтому просим прислать по одной.
    """
    if message.from_user.id not in config.admin_ids:
        await _guidance(
            message, "Вижу показания сразу по нескольким квартирам. "
                     "Пришлите, пожалуйста, показания только по своей "
                     "квартире — отдельным сообщением.")
        return

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
        result = import_batch(conn, blocks, user["id"] if user else None,
                              tg_id=message.from_user.id)
    finally:
        conn.close()

    logger.info("Пачка из чата: сообщений %s, записано показаний %s",
                result.messages, result.saved)
    if not await _dm(message, result.text()):
        await message.reply(result.text())


async def _guidance(message: Message, text: str) -> None:
    """Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её увидеть)."""
    if not await _dm(message, text):
        await message.reply(text + _START_HINT)
