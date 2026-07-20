"""Сборка и запуск Telegram-бота DH OS."""
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import config
from bot.handlers import admin, group, readings, registration, reports, start
from bot.utils.logger import setup_logging
from database.init_db import init_db

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()

    if not config.bot_token:
        raise SystemExit(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен бота."
        )

    init_db()
    logger.info("База данных готова: %s", config.db_path)

    bot = Bot(token=config.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Порядок важен: FSM-сценарии раньше общих обработчиков меню
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(readings.router)
    dp.include_router(reports.router)
    dp.include_router(start.router)
    dp.include_router(group.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск / главное меню"),
    ])

    logger.info("DH OS запущен")
    await dp.start_polling(bot)
