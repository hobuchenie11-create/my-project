"""Прием показаний из общего чата дома.

Бот разбирает сообщения вида:

    Кв. 12
    Свет: 15230
    ХВС кухня: 123,45
    ...

и записывает показания. Если в сообщении нет номера квартиры, берется
квартира отправителя (если он зарегистрирован в боте).
"""
from aiogram import F, Router
from aiogram.types import Message

from bot.config import config
from bot.services.parser import parse_message
from bot.services.reading_service import current_period, save_reading
from database import repository
from database.models import METER_KINDS

router = Router()
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


@router.message(F.text)
async def handle_group_message(message: Message) -> None:
    if config.group_chat_id and message.chat.id != config.group_chat_id:
        return

    parsed = parse_message(message.text)
    if parsed.is_empty:
        return  # обычное сообщение в чате, показаний нет — не мешаем

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)

        apartment = None
        if parsed.apartment_number:
            apartment = repository.get_apartment_by_number(conn, parsed.apartment_number)
        elif user and user["apartment_id"]:
            apartment = conn.execute(
                "SELECT * FROM apartments WHERE id = ?", (user["apartment_id"],)
            ).fetchone()

        if apartment is None:
            await message.reply(
                "Не понял, к какой квартире относятся показания. "
                "Добавьте в сообщение строку «Кв. <номер>» или зарегистрируйтесь "
                "в личных сообщениях бота."
            )
            return

        accepted: list[str] = []
        problems: list[str] = list(parsed.errors)
        for kind, value in parsed.values.items():
            result = save_reading(conn, apartment["id"], kind, value,
                                  user["id"] if user else None, source="chat")
            if result.ok:
                accepted.append(f"{METER_KINDS[kind]}: {value:g}")
                if result.warning:
                    problems.append(f"{METER_KINDS[kind]}: {result.warning}")
            else:
                problems.append(f"{METER_KINDS[kind]}: {result.error}")

        repository.log_event(conn, message.from_user.id, "reading_chat",
                             f"{apartment['number']}: принято {len(accepted)} "
                             f"за {current_period()}")
    finally:
        conn.close()

    display = (apartment["number"] if apartment["type"] == "nonresidential"
               else f"кв. {apartment['number']}")
    lines = []
    if accepted:
        lines.append(f"✅ {display} — показания записаны:")
        lines.extend(accepted)
    if problems:
        lines.append("")
        lines.extend(f"⚠️ {p}" for p in problems)
    await message.reply("\n".join(lines))
