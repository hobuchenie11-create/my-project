"""Фоновый планировщик: рассылка напоминаний в назначенные дни месяца."""
import asyncio
import logging
from datetime import date

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.config import config
from bot.services.reading_service import current_period, period_title
from bot.services.reminder_service import REMINDER_TEXT, pending_targets
from database import repository

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 3600  # раз в час проверяем, наступил ли день напоминания


async def run_reminder_scheduler(bot: Bot) -> None:
    """Бесконечный цикл: в дни из REMINDER_DAYS отправляет напоминания один раз."""
    already_sent_on: set[str] = set()  # ключи вида '2026-07-17', чтобы не дублировать
    while True:
        today = date.today()
        key = today.isoformat()
        if today.day in config.reminder_days and key not in already_sent_on:
            try:
                sent = await send_reminders(bot)
                logger.info("Напоминания отправлены: %s жителям", sent)
            except Exception:  # noqa: BLE001 - планировщик не должен падать
                logger.exception("Ошибка при рассылке напоминаний")
            already_sent_on.add(key)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def send_reminders(bot: Bot) -> int:
    """Разослать напоминания должникам за текущий период. Возвращает число отправленных."""
    period = current_period()
    text = REMINDER_TEXT.format(period=period_title(period))
    conn = repository.connect()
    try:
        targets = pending_targets(conn, period)
    finally:
        conn.close()

    sent = 0
    for target in targets:
        try:
            await bot.send_message(target.tg_id, text)
            sent += 1
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить напоминание кв. %s: %s",
                           target.apartment_number, exc)
    return sent
