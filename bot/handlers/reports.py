"""Просмотр своих показаний и истории передач."""
from aiogram import F, Router
from aiogram.types import Message

from bot.keyboards.menu import BTN_HISTORY, BTN_LAST
from bot.services.reading_service import history_text, my_last_readings_text
from database import repository

router = Router()
router.message.filter(F.chat.type == "private")


async def _get_user(message: Message):
    conn = repository.connect()
    try:
        user = repository.get_user_by_tg(conn, message.from_user.id)
    finally:
        conn.close()
    if user is None:
        await message.answer("Сначала нужно зарегистрироваться — отправьте /start")
    return user


@router.message(F.text == BTN_LAST)
async def show_last(message: Message) -> None:
    user = await _get_user(message)
    if user is None:
        return
    conn = repository.connect()
    try:
        await message.answer(my_last_readings_text(conn, user["apartment_id"]))
    finally:
        conn.close()


@router.message(F.text == BTN_HISTORY)
async def show_history(message: Message) -> None:
    user = await _get_user(message)
    if user is None:
        return
    conn = repository.connect()
    try:
        await message.answer(history_text(conn, user["apartment_id"]))
    finally:
        conn.close()
