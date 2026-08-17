"""Служебные команды, доступные в любом чате."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.config import config

router = Router()


@router.message(Command("chatid"))
async def cmd_chatid(message: Message) -> None:
    """Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env.

    Команды доходят до бота даже при включённом режиме приватности, поэтому
    здесь же проверяем, видит ли он обычные сообщения: если нет, показания
    из чата до него просто не долетают.
    """
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

    lines = [f"ID этого чата: <code>{chat_id}</code>", "", role]

    if message.chat.type in ("group", "supergroup"):
        me = await message.bot.get_me()
        if me.can_read_all_group_messages:
            lines.append("")
            lines.append("👀 Обычные сообщения в этом чате бот видит — "
                         "показания будут разбираться.")
        else:
            lines.append("")
            lines.append(
                "⚠️ <b>Бот не видит обычные сообщения чата</b> — включён режим "
                "приватности, до него доходят только команды. Показания "
                "из чата приниматься не будут.\n"
                "Как исправить: @BotFather → /mybots → выбрать бота → "
                "Bot Settings → Group Privacy → <b>Turn off</b>. "
                "Затем удалить бота из чата и добавить заново — иначе "
                "настройка не применится.")

    await message.reply("\n".join(lines))
