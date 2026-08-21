"""Фоновый планировщик DH OS.

Отвечает за автоматические действия по календарю:
  • напоминания должникам в дни из REMINDER_DAYS (по умолчанию 17, 23, 25);
  • ведомость непередавших — в DEBTORS_DAY в DEBTORS_HOUR часов
    (по умолчанию 20 числа в 09:00) отправляется председателю;
  • итоговая ведомость — в STATEMENT_DAY в STATEMENT_HOUR (20 числа в 14:00),
    уходит председателю;
  • реестр ОЭК — в OEK_DAY в OEK_HOUR:OEK_MINUTE (20 числа в 14:30): шаблон
    ресурсника, заполненный теми же показаниями, что ушли в ведомости;
  • объявление в чат дома, что сбор завершён (показания всё ещё принимаются,
    но будут учтены в следующем периоде) — в ANNOUNCE_DAY в ANNOUNCE_HOUR
    (20 числа в 18:00), когда чат читают.

Каждая задача выполняется не более одного раза в сутки, и отметка об этом
лежит в базе: бота перезапускают среди дня, а рассылка от этого повторяться
не должна.
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
from bot.texts import collection_closed_text
from database import repository

logger = logging.getLogger(__name__)

# Проверяем календарь раз в минуту: реестр ОЭК уходит в 14:30, и при шаге
# в 10 минут он мог опоздать почти на десять — тик стоит дёшево, задачи
# всё равно выполняются не чаще раза в сутки.
CHECK_INTERVAL_SECONDS = 60

CAPTION_LIMIT = 1000  # у Telegram подпись к документу — до 1024 знаков


async def run_scheduler(bot: Bot) -> None:
    """Бесконечный цикл: выполняет задачи дня не более одного раза за сутки."""
    while True:
        try:
            await _tick(bot, datetime.now())
        except Exception:  # noqa: BLE001 - планировщик не должен падать
            logger.exception("Ошибка в планировщике")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


def _claim(key: str) -> bool:
    """Занять задачу дня. False — её уже выполнили (в том числе до перезапуска).

    Отметка лежит в базе: бота перезапускают по нескольку раз в день, и
    отметка «в памяти процесса» после каждого перезапуска обнулялась —
    объявление о завершении сбора уходило в чат заново.
    """
    conn = repository.connect()
    try:
        return repository.claim_scheduled_task(conn, key)
    finally:
        conn.close()


async def _tick(bot: Bot, now: datetime) -> None:
    today = now.date().isoformat()

    if now.day in config.reminder_days and _claim(f"reminders:{today}"):
        sent = await send_reminders(bot)
        logger.info("Напоминания отправлены: %s жителям", sent)

    if (now.day == config.debtors_day and now.hour >= config.debtors_hour
            and _claim(f"debtors:{today}")):
        await send_debtors_statement(bot)

    if (now.day == config.statement_day and now.hour >= config.statement_hour
            and _claim(f"statement:{today}")):
        await send_monthly_statement(bot)

    # Реестр ОЭК — через полчаса после ведомости, той же цифрой
    if (now.day == config.oek_day
            and (now.hour, now.minute) >= (config.oek_hour, config.oek_minute)
            and _claim(f"oek:{today}")):
        await send_oek_registry(bot)

    # Объявление жителям — отдельно от ведомости и позже неё
    if (now.day == config.announce_day and now.hour >= config.announce_hour
            and _claim(f"announce:{today}")):
        await announce_collection_closed(bot)

    # Задачи председателя: напоминания раз в день
    if now.hour >= config.tasks_reminder_hour and _claim(f"tasks:{today}"):
        await send_task_reminders(bot)


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


async def send_oek_registry(bot: Bot) -> None:
    """Заполнить шаблон ОЭК показаниями за период и отправить председателю.

    Шаблон присылает ресурсник, форма у него меняется — поэтому ошибку разбора
    не глотаем, а пишем председателю: без файла он узнал бы об этом только
    когда реестр уже пора сдавать.
    """
    from excel.oek_registry import OekFormatError
    from reports.oek_registry import NoTemplateError, generate_oek_registry

    period = current_period()
    try:
        result = generate_oek_registry(period)
    except (NoTemplateError, OekFormatError) as exc:
        logger.warning("Реестр ОЭК не сформирован: %s", exc)
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id, f"📨 Реестр ОЭК не сформирован.\n\n{exc}")
            except TelegramAPIError as api_exc:
                logger.warning("Не удалось предупредить админа %s: %s",
                               admin_id, api_exc)
        return

    for admin_id in config.admin_ids:
        await deliver_oek_registry(bot, admin_id, result, period_title(period))
    logger.info("Реестр ОЭК сформирован: %s (заполнено %s из %s)",
                result.path, len(result.filled), result.rows_total)


async def deliver_oek_registry(bot: Bot, chat_id: int, result,
                               period_name: str) -> bool:
    """Отправляет файл реестра с отчётом. Общая для планировщика и кнопки."""
    summary = result.summary(period_name)
    # Подпись к документу в Telegram — не длиннее 1024 знаков. Если список
    # непередавших длинный, отправляем отчёт отдельным сообщением.
    caption, tail = (summary, "") if len(summary) <= CAPTION_LIMIT else (
        f"📨 <b>Реестр ОЭК</b> — {period_name}\n\n"
        f"Заполнено показаний: {len(result.filled)} из {result.rows_total}",
        summary)
    try:
        await bot.send_document(chat_id, FSInputFile(result.path), caption=caption)
        if tail:
            await bot.send_message(chat_id, tail)
    except TelegramAPIError as exc:
        logger.warning("Не удалось отправить реестр ОЭК в чат %s: %s", chat_id, exc)
        return False
    return True


async def announce_collection_closed(bot: Bot) -> bool:
    """Сообщение в чат дома: сбор закрыт, но показания всё ещё принимаются."""
    if not config.group_chat_id:
        logger.info("Чат дома не подключён — сообщение о закрытии сбора "
                    "не отправлено")
        return False
    try:
        await bot.send_message(config.group_chat_id, collection_closed_text())
    except TelegramAPIError as exc:
        logger.warning("Не удалось сообщить в чат о закрытии сбора: %s", exc)
        return False
    logger.info("В чат дома отправлено сообщение о завершении сбора")
    return True


async def send_task_reminders(bot: Bot) -> int:
    """Напоминания председателю по задачам: пора начинать, срок, просрочка."""
    from bot.services import task_service, verification_service

    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)      # цикл всегда заполнен вперёд
        verification_service.ensure_house_meters(conn)
        verification_service.sync_verification_tasks(conn)
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
