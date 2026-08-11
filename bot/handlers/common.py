"""Служебные команды, доступные в любом чате."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import config

router = Router()


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    """Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env."""
    chat_id = message.chat.id

    if chat_id == config.group_chat_id:
        role = ("✅ Этот чат уже подключён как <b>чат дома</b> "
                "(GROUP_CHAT_ID) — отсюда бот собирает показания.")
    elif chat_id == config.council_chat_id:
        role = ("✅ Этот чат уже подключён как <b>чат Совета дома</b> "
                "(COUNCIL_CHAT_ID) — сюда уходит сводка по задачам.")
    elif message.chat.type == "private":
        role = ("Это личный чат. ID группового чата узнавайте той же командой, "
                "отправив её в самом чате.")
    else:
        role = ("Впишите это число в файл .env — и перезапустите бота:\n"
                "• <code>GROUP_CHAT_ID</code> — если это чат дома, "
                "откуда собираются показания;\n"
                "• <code>COUNCIL_CHAT_ID</code> — если это чат Совета дома, "
                "куда уходит сводка по задачам.")

    await message.reply(f"ID этого чата: <code>{chat_id}</code>\n\n{role}")
