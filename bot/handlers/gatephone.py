"""Заявка на перепрограммирование номера в воротах.

Номер меняют не только новосёлы: сменил оператора, потерял симку, записали
телефон жены вместо своего. Раньше это решалось письмом председателю в
любое время суток и в любой форме — половина заявок без квартиры, половина
без ФИО, и на каждую приходилось переспрашивать.

Теперь житель нажимает кнопку в меню (или под памяткой про GSM-модуль), бот
спрашивает три вещи — на кого оформлен номер, квартира, новый номер — и
передаёт заявку председателю одним сообщением. В любой день: программирует
всё равно человек, но заявка уже собрана и ничего не потеряно.
"""
import logging
import re

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.config import config
from bot.handlers.faq import send_memo_by_code
from bot.keyboards.menu import BTN_GATE_PHONE, main_menu
from bot.services.apartment_service import find_apartment
from bot.states.gatephone import GatePhone
from database import repository

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private")

CANCEL_WORDS = ("отмена", "❌ отмена", "стоп", "не сейчас", "позже")

# В номере телефона цифр не меньше десяти: «89021234567», «+7 902 123-45-67».
# Меньше — это обрывок, и записывать его в ворота бессмысленно
_DIGITS_RE = re.compile(r"\d")
MIN_PHONE_DIGITS = 10

INTRO = (
    "📱 <b>Заявка на смену номера в воротах</b>\n\n"
    "Задам три вопроса — и передам заявку председателю. Программирует "
    "номер она, заявку можно оставить в любой день.\n\n"
    "<b>Вопрос 1 из 3.</b> На кого оформлен номер? Напишите ФИО.\n\n"
    "Чтобы выйти, отправьте «отмена»."
)


async def _begin(message: Message, state: FSMContext) -> None:
    await state.set_state(GatePhone.name)
    await message.answer(INTRO)


@router.message(F.text == BTN_GATE_PHONE)
async def start_from_menu(message: Message, state: FSMContext) -> None:
    await _begin(message, state)


@router.callback_query(F.data == "start:gatephone")
async def start_from_memo(callback: CallbackQuery, state: FSMContext) -> None:
    """Кнопка под памяткой про GSM-модуль."""
    await _begin(callback.message, state)
    await callback.answer()


@router.message(GatePhone.name, F.text)
async def take_name(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return
    if len(text) < 5:
        await message.answer(
            "Напишите ФИО полностью — например: "
            "<code>Иванова Мария Петровна</code>")
        return

    await state.update_data(name=text)
    await state.set_state(GatePhone.apartment)
    await message.answer(
        "<b>Вопрос 2 из 3.</b> Номер вашей квартиры — цифрами: "
        "<code>15</code>.")


@router.message(GatePhone.apartment, F.text)
async def take_apartment(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return

    conn = repository.connect()
    try:
        apartment = find_apartment(conn, text)
    finally:
        conn.close()

    if apartment is None:
        await message.answer(
            "Такой квартиры нет в реестре дома. Напишите номер цифрами — "
            "например, <code>15</code>.")
        return

    await state.update_data(apartment=apartment["number"])
    await state.set_state(GatePhone.phone)
    await message.answer(
        "<b>Вопрос 3 из 3.</b> Новый номер телефона, который нужно "
        "записать в ворота:\n\n<code>+7 902 123-45-67</code>\n\n"
        "Именно с этого номера вы будете звонить на ворота.")


@router.message(GatePhone.phone, F.text)
async def take_phone(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if text.lower() in CANCEL_WORDS:
        await _cancel(message, state)
        return
    if len(_DIGITS_RE.findall(text)) < MIN_PHONE_DIGITS:
        await message.answer(
            "Это не похоже на номер телефона. Напишите его полностью, "
            "с кодом оператора: <code>+7 902 123-45-67</code>")
        return

    data = await state.get_data()
    await state.clear()
    await _hand_over(message, data, text)

    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "✅ <b>Заявка передана председателю.</b>\n\n"
        f"Кому: {data.get('name', '—')}\n"
        f"Квартира: {data.get('apartment', '—')}\n"
        f"Новый номер: {text}\n\n"
        "Номер запишут в оба модуля ворот и сообщат вам. Не забудьте "
        "пополнить счёт каждого номера ворот на 10 ₽ — памятка ниже 👇",
        reply_markup=main_menu(is_admin))
    await send_memo_by_code(message, "gsm-modul")


async def _cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    is_admin = message.from_user.id in config.admin_ids
    await message.answer(
        "Хорошо, заявку отменила. Вернуться можно в любой момент — "
        f"кнопка «{BTN_GATE_PHONE}» в меню.",
        reply_markup=main_menu(is_admin))


async def _hand_over(message: Message, data: dict, phone: str) -> None:
    """Передаёт заявку председателю и пишет её в журнал.

    В журнал — в любом случае: если личка председателя недоступна (бот у неё
    не запущен, нет связи), заявка не должна пропасть бесследно.
    """
    user = message.from_user
    summary = (
        "📱 <b>Заявка: сменить номер в воротах</b>\n\n"
        f"Квартира: <b>{data.get('apartment', '—')}</b>\n"
        f"Номер оформлен на: {data.get('name', '—')}\n"
        f"Новый номер: <b>{phone}</b>\n\n"
        f"Telegram: {user.full_name}"
        + (f" (@{user.username})" if user.username else "")
    )

    conn = repository.connect()
    try:
        repository.log_event(
            conn, user.id, "gatephone",
            f"кв. {data.get('apartment', '?')}: {data.get('name', '')}; "
            f"новый номер: {phone}")
    finally:
        conn.close()
    logger.info("Заявка на смену номера в воротах: кв. %s",
                data.get("apartment"))

    for admin_id in config.admin_ids:
        await _send(message.bot, admin_id, summary)


async def _send(bot: Bot, chat_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id, text)
        return True
    except TelegramAPIError as exc:
        logger.warning("Не удалось передать председателю %s заявку на смену "
                       "номера: %s", chat_id, exc)
        return False
