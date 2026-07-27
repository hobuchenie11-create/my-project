"""Служебные команды, доступные в любом чате."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    """Показывает ID текущего чата — нужен для настройки GROUP_CHAT_ID в .env."""
    await message.reply(
        f"ID этого чата: <code>{message.chat.id}</code>\n\n"
        "Впишите это число в файл .env в строку GROUP_CHAT_ID, "
        "чтобы бот собирал показания именно из этого чата."
    )
