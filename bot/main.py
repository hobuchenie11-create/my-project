"""Сборка и запуск Telegram-бота DH OS."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from bot.config import config
from bot.handlers import (admin, common, faq, group, manual, oek, readings,
                          registration, reports, start, tasks)
from bot.keepawake import keep_awake
from bot.proxy import make_session
from bot.scheduler import run_scheduler
from bot.utils.logger import setup_logging
from database import repository
from database.init_db import init_db

logger = logging.getLogger(__name__)


def _apply_registry_if_present() -> None:
    """Если есть заполненный справочник квартир — применяем его к реестру."""
    from excel.import_registry import REGISTRY_PATH, import_registry
    if REGISTRY_PATH.exists():
        count = import_registry(REGISTRY_PATH)
        logger.info("Справочник квартир применен: %s квартир", count)


def _load_memos() -> None:
    """Памятки Домоведа из content/faq/ — перечитываются при каждом запуске."""
    from bot.services.faq_service import load_memos
    conn = repository.connect()
    try:
        count = load_memos(conn)
    finally:
        conn.close()
    logger.info("Памятки загружены: %s", count)


def _log_chats() -> None:
    """Показывает при запуске, какие чаты подключены — видно сразу в терминале."""
    logger.info("Чат дома (показания): %s",
                config.group_chat_id or "не подключен — GROUP_CHAT_ID пуст")
    logger.info("Чат Совета дома (сводка): %s",
                config.council_chat_id
                or "не подключен — COUNCIL_CHAT_ID пуст, сводка придёт вам в личку")
    if (config.council_chat_id
            and config.council_chat_id == config.group_chat_id):
        logger.warning("COUNCIL_CHAT_ID совпадает с GROUP_CHAT_ID: сводка уйдёт "
                       "в чат показаний. Укажите ID чата Совета (/chatid в нём).")


async def main() -> None:
    setup_logging()

    if not config.bot_token:
        raise SystemExit(
            "Не задан BOT_TOKEN. Скопируйте .env.example в .env и укажите токен бота."
        )

    init_db()
    _apply_registry_if_present()
    logger.info("База данных готова: %s", config.db_path)
    _load_memos()

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
    # Раньше tasks: тот забирает любой присланный документ как правки годового
    # плана, а .xls от ресурсника — это шаблон реестра ОЭК
    dp.include_router(oek.router)
    dp.include_router(tasks.router)
    dp.include_router(admin.router)
    dp.include_router(registration.router)
    dp.include_router(readings.router)
    dp.include_router(reports.router)
    dp.include_router(faq.router)
    dp.include_router(start.router)
    dp.include_router(group.router)
    # Последним: ручной ввод показаний председателем в личке —
    # сюда попадает только текст, который не разобрали остальные
    dp.include_router(manual.router)

    # Сбрасываем возможный вебхук — иначе getUpdates выдает Conflict.
    # Накопившиеся сообщения НЕ отбрасываем: пока бот был выключен, жители
    # могли присылать показания — Telegram хранит их около суток, и после
    # запуска бот их обработает.
    await bot.delete_webhook(drop_pending_updates=False)

    await bot.set_my_commands([
        BotCommand(command="start", description="Запуск / главное меню"),
        BotCommand(command="chatid", description="ID этого чата (для .env)"),
    ])

    _log_chats()

    # Режим приватности: с ним бот в группе видит только команды, и показания
    # из чата до него не доходят. В логе это должно быть видно сразу.
    me = await bot.get_me()
    if not me.can_read_all_group_messages:
        logger.warning(
            "Бот НЕ видит обычные сообщения в группах (режим приватности "
            "включён). Показания из чата дома приниматься не будут. "
            "@BotFather → Bot Settings → Group Privacy → Turn off, затем "
            "удалить бота из чата и добавить заново.")

    # Пока бот работает, ноутбук не должен засыпать — иначе показания,
    # присланные днём, повиснут в очереди Telegram до пробуждения.
    keep_awake()

    # Календарные задачи: напоминания и ведомость непередавших
    asyncio.create_task(run_scheduler(bot))

    logger.info("DH OS запущен")
    await dp.start_polling(bot)
