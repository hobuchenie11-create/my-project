"""Фоновый планировщик DH OS.

Отвечает за автоматические действия по календарю:
  • напоминания должникам в дни из REMINDER_DAYS (по умолчанию 17, 23, 25);
  • ведомость непередавших — в DEBTORS_DAY в DEBTORS_HOUR часов
    (по умолчанию 20 числа в 09:00) отправляется председателю.
"""
import asyncio
import logging
from datetime import date, datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile

from bot.config import config
from bot.services.reading_service import current_period, period_title
from bot.services.reminder_service import REMINDER_TEXT, pending_targets
from database import repository

logger = logging.getLogger(__name__)

CHECK_INTERVAL_SECONDS = 600  # проверяем календарь каждые 10 минут


async def run_scheduler(bot: Bot) -> None:
    """Бесконечный цикл: выполняет задачи дня не более одного раза за сутки."""
    done: set[str] = set()  # ключи вида 'reminders:2026-07-17'
    while True:
        try:
            await _tick(bot, datetime.now(), done)
        except Exception:  # noqa: BLE001 - планировщик не должен падать
            logger.exception("Ошибка в планировщике")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _tick(bot: Bot, now: datetime, done: set[str]) -> None:
    today = now.date().isoformat()

    if now.day in config.reminder_days:
        key = f"reminders:{today}"
        if key not in done:
            sent = await send_reminders(bot)
            done.add(key)
            logger.info("Напоминания отправлены: %s жителям", sent)

    if now.day == config.debtors_day and now.hour >= config.debtors_hour:
        key = f"debtors:{today}"
        if key not in done:
            await send_debtors_statement(bot)
            done.add(key)

    if now.day == config.statement_day and now.hour >= config.statement_hour:
        key = f"statement:{today}"
        if key not in done:
            await send_monthly_statement(bot)
            done.add(key)

    # Задачи председателя: напоминания раз в день
    if now.hour >= config.tasks_reminder_hour:
        key = f"tasks:{today}"
        if key not in done:
            await send_task_reminders(bot)
            done.add(key)


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


async def send_debtors_statement(bot: Bot) -> int:
    """Сформировать ведомость непередавших и отправить её председателям."""
    from reports.debtors_statement import generate_debtors_statement

    period = current_period()
    path, count = generate_debtors_statement(period)
    caption = (f"📕 Ведомость непередавших показания — {period_title(period)}\n"
               f"Не передали: {count}")
    for admin_id in config.admin_ids:
        try:
            await bot.send_document(admin_id, FSInputFile(path), caption=caption)
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить ведомость админу %s: %s", admin_id, exc)
    logger.info("Ведомость непередавших сформирована: %s (должников: %s)", path, count)
    return count


async def send_monthly_statement(bot: Bot) -> None:
    """Сформировать ведомость со всеми собранными показаниями и отправить её."""
    from reports.monthly_statement import generate_statement

    period = current_period()
    path = generate_statement(period)
    conn = repository.connect()
    try:
        submitted = len(repository.apartments_submitted(conn, period))
        total = len(repository.list_apartments(conn))
    finally:
        conn.close()

    caption = (f"📄 Ведомость передачи показаний — {period_title(period)}\n"
               f"Собрано: {submitted} из {total}.\n"
               "Показания, переданные после срока, попадут в следующий "
               "расчётный период (в ведомости они с пометкой).")
    for admin_id in config.admin_ids:
        try:
            await bot.send_document(admin_id, FSInputFile(path), caption=caption)
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить ведомость админу %s: %s", admin_id, exc)
    logger.info("Ведомость сформирована: %s (собрано %s из %s)", path, submitted, total)


async def send_task_reminders(bot: Bot) -> int:
    """Напоминания председателю по задачам: пора начинать, срок, просрочка."""
    from bot.services import task_service

    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)      # цикл всегда заполнен вперёд
        messages = task_service.reminders_for_today(conn)
    finally:
        conn.close()

    if not messages:
        return 0

    text = "🗂 <b>Задачи на сегодня</b>\n\n" + "\n\n".join(messages)
    sent = 0
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text)
            sent += 1
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить напоминание по задачам %s: %s",
                           admin_id, exc)
    return sent


# Обратная совместимость с прежним названием
run_reminder_scheduler = run_scheduler
