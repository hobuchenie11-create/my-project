"""Передача показаний: бот по очереди опрашивает приборы квартиры."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.keyboards.menu import BTN_SUBMIT, cancel_keyboard, main_menu
from bot.services.parser import parse_message
from bot.services.reading_service import (current_period, is_late, receipt_text,
                                          save_parsed_readings, save_reading,
                                          unit_for)
from bot.texts import late_submission_text
from bot.services.validation import parse_value
from bot.states.readings import SubmitReadings
from database import repository
from database.models import METER_KINDS

router = Router()
router.message.filter(F.chat.type == "private")


# Слова, по которым видно, что человек спрашивает, а не диктует показание
_QUESTION_WORDS = ("как", "где", "когда", "почему", "зачем", "что", "кто",
                   "куда", "можно", "нужно", "подскажите", "помогите",
                   "не работает", "сломал", "не могу")


def _looks_like_question(text: str) -> bool:
    lowered = text.strip().lower()
    if "?" in lowered:
        return True
    if len(lowered.split()) < 2:
        return False
    return any(lowered.startswith(w) or f" {w} " in lowered
               for w in _QUESTION_WORDS)


async def _ask_next_meter(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    queue: list[str] = data["queue"]
    if not queue:
        await _finish(message, state)
        return

    kind = queue[0]
    conn = repository.connect()
    try:
        meter = repository.get_meter(conn, data["apartment_id"], kind)
        last = repository.last_reading(conn, meter["id"]) if meter else None
    finally:
        conn.close()

    hint = f" (предыдущее: {last['value']:g})" if last else ""
    await message.answer(
        f"Введите показание — <b>{METER_KINDS[kind]}</b>, {unit_for(kind)}{hint}:",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(SubmitReadings.value)


async def _finish(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    saved: dict[str, float] = data.get("saved", {})
    warnings: list[str] = data.get("warnings", [])
    apartment_id = data["apartment_id"]
    await state.clear()

    conn = repository.connect()
    try:
        apartment = repository.get_apartment_by_id(conn, apartment_id)
        text = receipt_text(conn, apartment, saved)
    finally:
        conn.close()
    if warnings:
        text += "\n\n" + "\n".join(f"⚠️ {w}" for w in warnings)
    if saved and is_late():
        text += "\n\n" + late_submission_text()

    is_admin = message.from_user.id in config.admin_ids
    await message.answer(text, reply_markup=main_menu(is_admin))


@router.message(F.text == BTN_SUBMIT)
async def start_submission(message: Message, state: FSMContext) -> None:
    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
        if user is None:
            await message.answer("Сначала нужно зарегистрироваться — отправьте /start")
            return
        meters = repository.meters_for_apartment(conn, user["apartment_id"])
    finally:
        conn.close()

    if not meters:
        await message.answer("Для вашей квартиры не заведены приборы учета. "
                             "Обратитесь к председателю.")
        return

    await state.update_data(
        apartment_id=user["apartment_id"],
        user_id=user["id"],
        queue=[m["kind"] for m in meters],
        saved={},
        warnings=[],
    )
    await _ask_next_meter(message, state)


@router.message(SubmitReadings.value, F.text == "❌ Отмена")
async def cancel_submission(message: Message, state: FSMContext) -> None:
    await state.clear()
    is_admin = message.from_user.id in config.admin_ids
    await message.answer("Передача показаний отменена.", reply_markup=main_menu(is_admin))


async def _try_whole_message(message: Message, state: FSMContext) -> bool:
    """Вставили сообщение целиком вместо одного числа — разбираем его.

    Жители копируют готовый текст (из WhatsApp, из чата дома) и вставляют
    в диалог. Отвечать «не похоже на показание» на такое — терять переданные
    показания, поэтому пробуем прочитать сообщение как обычно.
    """
    parsed = parse_message(message.text or "")
    if parsed.is_empty:
        return False

    data = await state.get_data()
    is_admin = message.from_user.id in config.admin_ids
    conn = repository.connect()
    try:
        apartment = repository.get_apartment_by_id(conn, data["apartment_id"])

        # Председатель переносит показания за жителей, поэтому её квартиру
        # молча подставлять нельзя: без номера в тексте показания соседа
        # ушли бы в её собственную строку.
        if is_admin and parsed.apartment_number is None:
            await message.answer(
                f"В тексте нет номера квартиры, а сейчас открыт ввод по "
                f"кв. {apartment['number']} — вашей.\n\n"
                "Если это показания жителя, нажмите «❌ Отмена» и пришлите "
                "текст с номером в первой строке: «Кв. 15».\n"
                "Если это ваши показания — допишите «Кв. "
                f"{apartment['number']}» первой строкой.")
            return True

        # Вставили показания за другую квартиру — записывать их сюда нельзя
        if (parsed.apartment_number
                and parsed.apartment_number != apartment["number"]):
            await message.answer(
                f"В сообщении указана {parsed.apartment_number}, а сейчас "
                f"вводим показания по кв. {apartment['number']}.\n\n"
                "Нажмите «❌ Отмена» и пришлите этот текст обычным сообщением — "
                "бот запишет его в нужную квартиру.")
            return True

        outcome = save_parsed_readings(conn, apartment, parsed,
                                       data.get("user_id"), source="bot")
        text = (receipt_text(conn, apartment, outcome.saved)
                if outcome.anything_saved else "Показания не записаны.")
    finally:
        conn.close()

    await state.clear()
    problems = list(outcome.warnings) + list(outcome.errors)
    if problems:
        text += "\n\n" + "\n".join(f"⚠️ {p}" for p in problems)
    if outcome.anything_saved and is_late():
        text += "\n\n" + late_submission_text()

    is_admin = message.from_user.id in config.admin_ids
    await message.answer(text, reply_markup=main_menu(is_admin))
    return True


@router.message(SubmitReadings.value)
async def process_value(message: Message, state: FSMContext) -> None:
    text = message.text or ""
    value = parse_value(text)
    if value is None and await _try_whole_message(message, state):
        return
    if value is None:
        # Житель посреди передачи показаний задал вопрос — не оставляем его
        # в тупике, а объясняем, как выйти из диалога.
        if _looks_like_question(text):
            await message.answer(
                "Похоже, это вопрос, а сейчас идёт передача показаний.\n\n"
                "Нажмите «❌ Отмена», чтобы выйти и задать вопрос, — "
                "введённые показания уже сохранены. "
                "Или введите показание числом, и продолжим.")
        else:
            await message.answer("Не похоже на показание. Введите число, "
                                 "например: 1234 или 56,78")
        return

    data = await state.get_data()
    kind = data["queue"][0]

    conn = repository.connect()
    try:
        result = save_reading(conn, data["apartment_id"], kind, value,
                              data["user_id"], source="bot")
        if result.ok:
            repository.log_event(conn, message.from_user.id, "reading",
                                 f"{kind}={value:g} за {current_period()}")
    finally:
        conn.close()

    if not result.ok:
        await message.answer(f"❗ {result.error}\n\nВведите показание еще раз:")
        return

    saved = data["saved"]
    saved[kind] = value
    warnings = data["warnings"]
    if result.warning:
        warnings.append(f"{METER_KINDS[kind]}: {result.warning}")

    await state.update_data(queue=data["queue"][1:], saved=saved, warnings=warnings)
    await _ask_next_meter(message, state)
