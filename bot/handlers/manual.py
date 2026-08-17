"""Ручной ввод показаний председателем — в личном чате с ботом.

Нежилые помещения и общедомовой прибор передаёт не житель, а председатель.
Отдельного диалога для них не нужно: пишем боту в личку тем же текстом, что
жители пишут в чат, — «Нежилое 1 / Эл.эн 1234 / Хвс 56 / Гвс 78».

Роутер подключается последним, поэтому кнопки меню и диалоги (новая задача,
поверка, суммы) разбираются раньше и сюда не попадают: здесь оказывается
только свободный текст, который больше никто не обработал.
"""
import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.config import config
from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, receipt_text,
                                          save_parsed_readings)
from database import repository

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private",
                      F.from_user.id.in_(config.admin_ids))


@router.message(F.text)
async def manual_readings(message: Message) -> None:
    parsed = parse_message(message.text)
    if parsed.is_empty and not parsed.apartment_number:
        return                      # обычное сообщение, не показания

    if parsed.apartment_number is None:
        await message.answer(
            "Не понял, к какому помещению относятся показания. Укажите "
            "в первой строке номер: «Кв. 15», «Нежилое 1» или «Общедомовой».")
        return

    conn = repository.connect()
    try:
        apartment = repository.get_apartment_by_number(
            conn, parsed.apartment_number)
        if apartment is None:
            await message.answer(
                f"В реестре нет помещения «{parsed.apartment_number}». "
                "Проверьте номер.")
            return

        if parsed.is_empty:
            await message.answer(
                "Помещение понял, а показания — нет. Напишите прибор и число: "
                "«Эл.эн 12345», «Хвс 56».")
            return

        user = repository.get_user_by_tg(conn, message.from_user.id)
        outcome = save_parsed_readings(conn, apartment, parsed,
                                       user["id"] if user else None,
                                       source="admin")
        repository.log_event(conn, message.from_user.id, "reading_admin",
                             f"{apartment['number']}: принято "
                             f"{len(outcome.saved)} за {current_period()}")
        text = (receipt_text(conn, apartment, outcome.saved)
                if outcome.anything_saved else "Показания не записаны.")
    finally:
        conn.close()

    problems = list(outcome.warnings) + list(outcome.errors)
    if parsed.ignored:
        problems.append("Не учитывается: " + ", ".join(parsed.ignored))
    if problems:
        text += "\n\n" + "\n".join(f"⚠️ {p}" for p in problems)
    await message.answer(text)
