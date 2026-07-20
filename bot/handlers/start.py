"""Команда /start и справка."""
from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.config import config
from bot.keyboards.menu import BTN_HELP, main_menu
from bot.states.registration import Registration
from database import repository

router = Router()
router.message.filter(F.chat.type == "private")

HELP_TEXT = (
    "ℹ️ <b>DH OS — Дом в гармонии</b>\n\n"
    "Бот принимает показания приборов учета воды и электроэнергии.\n\n"
    "🏠 <b>Передать показания</b> — бот по очереди спросит показания "
    "каждого прибора вашей квартиры.\n"
    "📄 <b>Мои последние показания</b> — что записано сейчас.\n"
    "📊 <b>История передач</b> — журнал ваших передач.\n\n"
    f"Показания принимаются с {config.readings_day_start} по "
    f"{config.readings_day_end} число каждого месяца.\n\n"
    "Показания также можно отправить в общий чат дома в формате:\n"
    "<code>Кв. 12\n"
    "Свет: 15230\n"
    "ХВС кухня: 123,45\n"
    "ХВС санузел: 89,1\n"
    "ГВС кухня: 44,2\n"
    "ГВС ванна: 51,0</code>"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
    finally:
        conn.close()

    is_admin = message.from_user.id in config.admin_ids
    if user:
        await message.answer(
            f"С возвращением, {user['full_name']}! Выберите действие:",
            reply_markup=main_menu(is_admin),
        )
        return

    await message.answer(
        "👋 Здравствуйте! Это DH OS — система учета показаний нашего дома.\n\n"
        "Давайте зарегистрируемся. Введите номер вашей квартиры:"
    )
    await state.set_state(Registration.apartment)


@router.message(F.text == BTN_HELP)
async def show_help(message: Message) -> None:
    await message.answer(HELP_TEXT)
