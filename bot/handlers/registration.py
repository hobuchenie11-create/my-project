"""Сценарий регистрации жителя: квартира -> имя -> подтверждение.

Спрашиваем только имя. Фамилия и отчество для работы системы не нужны:
показания привязаны к квартире, а имя служит лишь обращением в ответах
председателю. Просить лишние персональные данные там, где они ни на что
не влияют, значит собирать то, что придётся хранить и защищать.
"""
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from bot.config import config
from bot.keyboards.menu import main_menu
from bot.services.apartment_service import find_apartment
from bot.states.registration import Registration
from database import repository

router = Router()
router.message.filter(F.chat.type == "private")

CONFIRM_KB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="✅ Все верно"), KeyboardButton(text="🔁 Заново")]],
    resize_keyboard=True,
)


@router.message(Registration.apartment)
async def process_apartment(message: Message, state: FSMContext) -> None:
    number = (message.text or "").strip()
    conn = repository.connect()
    try:
        apartment = find_apartment(conn, number)
    finally:
        conn.close()

    if apartment is None:
        await message.answer(
            "Такой квартиры нет в реестре. Введите номер квартиры цифрами, "
            "например: 12"
        )
        return

    await state.update_data(apartment_id=apartment["id"], apartment_number=apartment["number"])
    await message.answer("Как к вам обращаться? Достаточно имени — "
                         "например, «Елена».")
    await state.set_state(Registration.name)


@router.message(Registration.name)
async def process_name(message: Message, state: FSMContext) -> None:
    name = (message.text or "").strip()
    if len(name) < 2:
        await message.answer("Пожалуйста, напишите имя — хотя бы две буквы.")
        return
    await state.update_data(name=name)
    data = await state.get_data()
    await message.answer(
        f"Проверьте данные:\n\nКвартира: {data['apartment_number']}\n"
        f"Имя: {name}\n\nВсе верно?",
        reply_markup=CONFIRM_KB,
    )
    await state.set_state(Registration.confirm)


@router.message(Registration.confirm, F.text == "✅ Все верно")
async def confirm_registration(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    is_admin = message.from_user.id in config.admin_ids
    conn = repository.connect()
    try:
        repository.create_user(conn, message.from_user.id, data["name"],
                               data["apartment_id"],
                               role="admin" if is_admin else "resident",
                               username=message.from_user.username or "")
        repository.log_event(conn, message.from_user.id, "registration",
                             f"кв. {data['apartment_number']}, {data['name']}")
    finally:
        conn.close()
    await state.clear()
    await message.answer(
        "✅ Регистрация завершена! Теперь можно передавать показания.",
        reply_markup=main_menu(is_admin),
    )


@router.message(Registration.confirm)
async def restart_registration(message: Message, state: FSMContext) -> None:
    await state.set_state(Registration.apartment)
    await message.answer("Хорошо, начнем заново. Введите номер вашей квартиры:",
                         reply_markup=ReplyKeyboardRemove())
