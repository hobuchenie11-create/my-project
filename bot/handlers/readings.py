"""Передача показаний: бот по очереди опрашивает приборы квартиры."""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.keyboards.menu import BTN_SUBMIT, cancel_keyboard, main_menu
from bot.services.reading_service import (current_period, receipt_text,
                                          save_reading, unit_for)
from bot.services.validation import parse_value
from bot.states.readings import SubmitReadings
from database import repository
from database.models import METER_KINDS

router = Router()
router.message.filter(F.chat.type == "private")


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


@router.message(SubmitReadings.value)
async def process_value(message: Message, state: FSMContext) -> None:
    value = parse_value(message.text or "")
    if value is None:
        await message.answer("Не похоже на показание. Введите число, например: 1234 или 56,78")
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
