"""Проверка: под каким именем бот сейчас представлен в Telegram.

Имя, логин и аватар хранятся в Telegram, а не в проекте — бот запрашивает их
при обращении. Эта команда показывает, что Telegram отдаёт прямо сейчас,
чтобы убедиться, что переименование применилось.

Запуск:  python -m bot.whoami
"""
import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import config
from bot.proxy import make_session


async def show() -> None:
    if not config.bot_token:
        raise SystemExit("Не задан BOT_TOKEN — заполните файл .env")

    bot = Bot(token=config.bot_token, session=make_session(config.proxy_url),
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    try:
        me = await bot.get_me()
        description = await bot.get_my_description()
        short = await bot.get_my_short_description()
        commands = await bot.get_my_commands()

        print("=== Бот в Telegram ===")
        print(f"Имя:            {me.full_name}")
        print(f"Логин:          @{me.username}")
        print(f"Ссылка:         https://t.me/{me.username}")
        print(f"ID бота:        {me.id}")
        print(f"Видит сообщения в группах: "
              f"{'да' if me.can_read_all_group_messages else 'нет (включите Group Privacy → Turn off)'}")
        print()
        print(f"Описание:       {description.description or '(пусто)'}")
        print(f"Кратко о боте:  {short.short_description or '(пусто)'}")
        print(f"Команды:        "
              f"{', '.join('/' + c.command for c in commands) or '(нет)'}")
        print()
        print("Аватар в этой проверке не показывается — посмотрите его "
              "в Telegram, открыв бота.")
        print()
        print("Имя, аватар и описание берутся из Telegram при каждом обращении, "
              "поэтому в проекте ничего менять не нужно.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(show())
