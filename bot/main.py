"""Сборка и запуск Telegram-бота DH OS."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import config
from bot.handlers import admin, common, group, readings, registration, reports, start
from bot.proxy import make_session
from bot.scheduler import run_reminder_scheduler
from bot.utils.logger import setup_logging
from database.init_db import init_db

logger = logging.getLogger(__name__)


def _apply_registry_if_present() -> None:
    """Если есть заполненный справочник квартир — применяем его к реестру."""
    from excel.import_registry import REGISTRY_PATH, import_registry
    if REGISTRY_PATH.exists():
        count = import_registry(REGISTRY_PATH)
        logger.info("Справочник квартир применен: %s квартир", count)


async def main() -> None:
    setup_logging()

    if not config.bot_token:
        raise SystemExit(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен бота."
        )

    init_db()
    _apply_registry_if_present()
    logger.info("База данных готова: %s", config.db_path)

    # Если задан PROXY_URL — весь трафик бота идет через прокси (например,
    # локальный порт Nekobox), т.к. Python сам системный VPN не использует.
    session = make_session(config.proxy_url)
    if config.proxy_url:
        logger.info("Бот подключается через прокси: %s", config.proxy_url)

    bot = Bot(token=config.bot_token, session=session,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Порядок важен: FSM-сценарии раньше общих обработчиков меню
    dp.include_router(common.router)
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(readings.router)
    dp.include_router(reports.router)
    dp.include_router(start.router)
    dp.include_router(group.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск / главное меню"),
    ])

    # Фоновая рассылка напоминаний (Этап 7)
    asyncio.create_task(run_reminder_scheduler(bot))

    logger.info("DH OS запущен")
    await dp.start_polling(bot)
