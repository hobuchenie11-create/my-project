"""Прием показаний из общего чата дома.

Бот разбирает сообщения по шаблонам жителей (см. bot/services/parser.py):

    Кв. 12
    Эл.эн 15230
    хвс (кухня) 123,45
    ...

и записывает показания. Если в сообщении нет номера квартиры, берется
квартира отправителя (если он зарегистрирован в боте).
"""
from aiogram import F, Router
from aiogram.types import Message

from bot.config import config
from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, receipt_text,
                                          save_parsed_readings)
from database import repository

router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(F.text)
async def handle_group_message(message: Message) -> None:
    if config.group_chat_id and message.chat.id != config.group_chat_id:
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
        elif user and user["apartment_id"]:
            apartment = repository.get_apartment_by_id(conn, user["apartment_id"])

        if apartment is None:
            if parsed.is_empty:
                return
            await message.reply(
                "Не понял, к какой квартире относятся показания. Укажите в первой "
                "строке «Кв. <номер>»."
            )
            return

        if parsed.is_empty:
            await message.reply(
                "Вижу номер квартиры, но не разобрал показания. Пришлите по шаблону, "
                "например: «Эл.эн 15230», «хвс кухня 123,45»."
            )
            return

        outcome = save_parsed_readings(conn, apartment, parsed,
                                       user["id"] if user else None, source="chat")
        repository.log_event(conn, message.from_user.id, "reading_chat",
                             f"{apartment['number']}: принято {len(outcome.saved)} "
                             f"за {current_period()}")
        reply = _build_reply(conn, apartment, outcome, parsed)
    finally:
        conn.close()

    await message.reply(reply)


def _build_reply(conn, apartment, outcome, parsed) -> str:
    if outcome.anything_saved:
        text = receipt_text(conn, apartment, outcome.saved)
    else:
        text = "Показания не записаны."
    extras = list(outcome.warnings) + list(outcome.errors)
    if parsed.ignored:
        extras.append("Не учитывается: " + ", ".join(parsed.ignored))
    if extras:
        text += "\n\n" + "\n".join(f"⚠️ {e}" for e in extras)
    return text
