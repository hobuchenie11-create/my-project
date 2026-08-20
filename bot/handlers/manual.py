"""Показания текстом в личном чате с ботом — без диалога по кнопке.

Житель копирует готовое сообщение (из чата дома, из WhatsApp) и вставляет
боту — записываем в его квартиру. Председатель тем же способом передаёт
нежилые помещения и общедомовой прибор («Нежилое 1», «Общедомовой») и может
внести показания за любую квартиру, если житель передал их по телефону.

Роутер подключается последним, поэтому кнопки меню и диалоги (новая задача,
поверка, суммы) разбираются раньше и сюда не попадают: здесь оказывается
только свободный текст, который больше никто не обработал.
"""
import logging

from aiogram import F, Router
from aiogram.types import Message

from bot.config import config
from bot.services.batch_service import import_batch
from bot.services.parser import parse_message, split_messages
from bot.services.reading_service import (current_period, is_late, receipt_text,
                                          save_parsed_readings)
from bot.texts import late_submission_text
from database import repository

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")


@router.message(F.text)
async def manual_readings(message: Message) -> None:
    is_admin = message.from_user.id in config.admin_ids

    # Председатель вставил пачку сообщений из чата WhatsApp — разносим все
    if is_admin:
        blocks = split_messages(message.text)
        if len(blocks) > 1:
            await _import_batch(message, blocks)
            return

    parsed = parse_message(message.text)

    if parsed.is_empty and not parsed.apartment_number:
        # Не показания — значит вопрос. Ищем ответ в памятках Домоведа.
        await _answer_as_question(message)
        return

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
        apartment = _resolve(conn, parsed, user, is_admin)

        if isinstance(apartment, str):          # не помещение, а объяснение
            await message.answer(apartment)
            return

        if parsed.is_empty:
            await message.answer(
                "Помещение понял, а показания — нет. Напишите прибор и число: "
                "«Эл.эн 12345», «Хвс 56».")
            return

        # Правку принимаем только от председателя: житель, ошибившийся в
        # цифре, обращается к ней — так исправление всегда видно одному
        # человеку, который потом сверяет ведомость
        correction = parsed.is_correction and is_admin
        if parsed.is_correction and not is_admin:
            await message.answer(
                "Исправить уже принятое показание может только председатель — "
                "напишите ей, пожалуйста, и она внесёт правку.")
            return

        source = "admin" if is_admin else "bot"
        outcome = save_parsed_readings(conn, apartment, parsed,
                                       user["id"] if user else None,
                                       source=source, correction=correction)
        repository.log_event(conn, message.from_user.id,
                             "reading_correction" if correction else f"reading_{source}",
                             f"{apartment['number']}: принято "
                             f"{len(outcome.saved)} за {current_period()}")
        text = (receipt_text(conn, apartment, outcome.saved,
                             replaced=outcome.replaced)
                if outcome.anything_saved else "Показания не записаны.")
    finally:
        conn.close()

    logger.info("Личка: %s — записано показаний %s", apartment["number"],
                len(outcome.saved))

    problems = list(outcome.warnings) + list(outcome.errors)
    if parsed.ignored:
        problems.append("Не учитывается: " + ", ".join(parsed.ignored))
    if problems:
        text += "\n\n" + "\n".join(f"⚠️ {p}" for p in problems)
    if outcome.anything_saved and is_late() and not correction:
        text += "\n\n" + late_submission_text()
    await message.answer(text)


async def _import_batch(message: Message, blocks: list[str]) -> None:
    """Разносит вставленную пачку сообщений и отвечает одной сводкой."""
    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
        result = import_batch(conn, blocks, user["id"] if user else None,
                              tg_id=message.from_user.id)
    finally:
        conn.close()

    logger.info("Пачка: сообщений %s, записано показаний %s",
                result.messages, result.saved)
    await message.answer(result.text())


async def _answer_as_question(message: Message) -> None:
    """Свободный текст, не похожий на показания, — вопрос к Домоведу."""
    from bot.handlers.faq import answer_question

    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
        apartment = ""
        if user and user["apartment_id"]:
            row = repository.get_apartment_by_id(conn, user["apartment_id"])
            apartment = row["number"] if row else ""
    finally:
        conn.close()

    await answer_question(message, message.from_user.id, apartment)


def _resolve(conn, parsed, user, is_admin):
    """Помещение, в которое пойдут показания, либо текст с объяснением.

    Житель может передать только за свою квартиру: номер из сообщения для
    него — повод перепроверить, а не записать соседу. Председатель передаёт
    за любое помещение, включая нежилые и общедомовой прибор.
    """
    if is_admin:
        if parsed.apartment_number is None:
            return ("Не понял, к какому помещению относятся показания. Укажите "
                    "в первой строке номер: «Кв. 15», «Нежилое 1» "
                    "или «Общедомовой».")
        apartment = repository.get_apartment_by_number(
            conn, parsed.apartment_number)
        if apartment is None:
            return (f"В реестре нет помещения «{parsed.apartment_number}». "
                    "Проверьте номер.")
        return apartment

    if user is None or not user["apartment_id"]:
        return ("Похоже на показания, но я не знаю вашей квартиры. "
                "Отправьте /start и зарегистрируйтесь — это один раз.")

    apartment = repository.get_apartment_by_id(conn, user["apartment_id"])
    if (parsed.apartment_number
            and parsed.apartment_number != apartment["number"]):
        return (f"В сообщении указана {parsed.apartment_number}, а вы "
                f"зарегистрированы как кв. {apartment['number']}. "
                "Показания принимаются только по своей квартире — "
                "если номер квартиры изменился, сообщите председателю.")
    return apartment
