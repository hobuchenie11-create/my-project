"""Служебные команды, доступные в любом чате."""
from aiogram import Router
from aiogram.exceptions import TelegramAPIError
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
        lines.append("")
        lines.append(await _visibility_note(message))

    await message.reply("\n".join(lines))


async def _visibility_note(message: Message) -> str:
    """Видит ли бот обычные сообщения именно в этом чате.

    Одного `can_read_all_group_messages` мало: это глобальная настройка из
    @BotFather, а к чату режим приватности применяется в момент добавления
    бота. Если приватность выключили уже после — в этом чате бот по-прежнему
    видит только команды. Права администратора снимают ограничение всегда.
    """
    me = await message.bot.get_me()
    try:
        member = await message.bot.get_chat_member(message.chat.id, me.id)
        status = member.status
    except TelegramAPIError:
        status = ""

    if status in ("administrator", "creator"):
        return ("👀 Бот — администратор чата, значит видит все сообщения. "
                "Показания будут разбираться.")

    fix = ("<b>Как исправить (любой способ):</b>\n"
           "• сделать бота администратором чата — самый быстрый, права "
           "модератора ему не нужны;\n"
           "• либо удалить бота из чата и добавить заново.")

    if me.can_read_all_group_messages:
        return ("⚠️ <b>Приватность выключена, но в этом чате может не "
                "действовать.</b> Режим приватности применяется к чату при "
                "добавлении бота: если его выключили позже, здесь бот "
                "по-прежнему видит только команды — а показания не видит.\n"
                f"{fix}\n\n"
                "Проверка: отправьте в чат любое сообщение с показаниями и "
                "посмотрите терминал — там должна появиться строка "
                "«Чат: … — записано показаний …».")

    return ("⚠️ <b>Бот не видит обычные сообщения чата</b> — включён режим "
            "приватности, до него доходят только команды.\n"
            "@BotFather → /mybots → выбрать бота → Bot Settings → "
            "Group Privacy → <b>Turn off</b>, затем:\n" + fix)
