"""Фоновый планировщик DH OS.

Отвечает за автоматические действия по календарю:
  • напоминания жителям, не сдавшим показания, — в дни из REMINDER_DAYS
    в REMINDER_HOUR часов (по умолчанию 15, 17 и 19 числа в 10:00);
  • напоминание в чат дома — в дни CHAT_REMINDER_DAYS в CHAT_REMINDER_HOUR
    (17–20 числа в 10:00): для жителей, не зарегистрированных в боте;
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
from bot.services.reminder_service import pending_targets, reminder_text
from bot.texts import collection_closed_text, collection_reminder_text
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


def _release(key: str) -> None:
    """Вернуть задачу дня в очередь: сделать её не вышло, попробуем ещё раз."""
    conn = repository.connect()
    try:
        repository.release_scheduled_task(conn, key)
    finally:
        conn.close()
    logger.warning("Задача «%s» не выполнена — попробую на следующем круге", key)


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

    # Час важен: без него первое срабатывание в эти сутки будило жителей ночью
    if (now.day in config.reminder_days and now.hour >= config.reminder_hour
            and _claim(f"reminders:{today}")):
        if not await send_reminders(bot):
            # Никому не дошло, хотя адресаты были, — связи нет. Отметку
            # снимаем, иначе день сгорит: следующий тик попробует снова.
            _release(f"reminders:{today}")

    # Напоминание в чат дома: жителям без бота иначе не сказать
    if (now.day in config.chat_reminder_days
            and now.hour >= config.chat_reminder_hour
            and _claim(f"chat_reminder:{today}")):
        if not await send_chat_reminder(bot):
            _release(f"chat_reminder:{today}")

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

    # Реестр на сверку председателю — утром того дня, когда он уйдёт в ОЭК
    if (now.day == config.oek_mail_day and now.hour >= config.oek_review_hour
            and _claim(f"oekreview:{today}")):
        if not await send_oek_review(bot):
            _release(f"oekreview:{today}")

    # Отправка реестра ресурснику почтой — 21 числа в 20:00
    if (now.day == config.oek_mail_day and now.hour >= config.oek_mail_hour
            and _claim(f"oekmail:{today}")):
        if not await mail_oek_registry(bot):
            _release(f"oekmail:{today}")

    # Объявление жителям — отдельно от ведомости и позже неё
    if (now.day == config.announce_day and now.hour >= config.announce_hour
            and _claim(f"announce:{today}")):
        await announce_collection_closed(bot)

    # Задачи председателя: напоминания раз в день
    if now.hour >= config.tasks_reminder_hour and _claim(f"tasks:{today}"):
        await send_task_reminders(bot)


async def send_reminders(bot: Bot) -> list[str]:
    """Напоминания жителям, не сдавшим показания. Возвращает номера квартир.

    Не число, а список: председателю важно видеть, кому именно ушло —
    зарегистрированных жителей пока единицы, и каждый на счету.
    """
    period = current_period()
    text = reminder_text(period)
    conn = repository.connect()
    try:
        targets = pending_targets(conn, period)
    finally:
        conn.close()

    if not targets:
        logger.info("Напоминания за %s: некому — все сдали показания", period)
        return ["некому"]      # работа сделана, повторять на этих сутках нечего

    sent = []
    for target in targets:
        try:
            await bot.send_message(target.tg_id, text)
            sent.append(target.apartment_number)
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить напоминание кв. %s: %s",
                           target.apartment_number, exc)
    logger.info("Напоминания за %s отправлены: %s", period,
                ", ".join(f"кв. {n}" for n in sent) or "ни одного")
    return sent


async def send_chat_reminder(bot: Bot) -> bool:
    """Напоминание о сборе показаний в чат дома.

    Зарегистрированным жителям бот пишет лично, но их пока единицы —
    остальные восемьдесят квартир читают только общий чат.
    """
    if not config.group_chat_id:
        logger.info("Чат дома не подключён — напоминание в чат не отправлено")
        return False
    try:
        await bot.send_message(config.group_chat_id, collection_reminder_text())
    except TelegramAPIError as exc:
        logger.warning("Не удалось отправить напоминание в чат дома: %s", exc)
        return False
    logger.info("Напоминание о сборе показаний отправлено в чат дома")
    return True


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
        await deliver_oek_registry(bot, admin_id, result, period_title(period),
                                   period)
    logger.info("Реестр ОЭК сформирован: %s (заполнено %s из %s)",
                result.path, len(result.filled), result.rows_total)


def oek_sent_key(period: str) -> str:
    """Отметка «реестр за период уже ушёл в ОЭК» — одна на все пути отправки."""
    return f"oek_sent:{period}"


def oek_hold_key(period: str) -> str:
    """Отметка «председатель отложила отправку» — вечером не отправляем."""
    return f"oek_hold:{period}"


def _done(key: str) -> bool:
    conn = repository.connect()
    try:
        return repository.scheduled_task_done(conn, key)
    finally:
        conn.close()


async def send_oek_review(bot: Bot) -> bool:
    """Реестр председателю на сверку — за часы до автоматической отправки.

    Письмо ресурснику не отзовёшь, а ошибка в показаниях всплывает через
    месяц, когда расход окажется отрицательным. Поэтому между «файл готов»
    и «файл ушёл» стоит день, а в этом сообщении — кнопка «отложить».
    """
    from excel.oek_registry import OekFormatError
    from reports.oek_registry import NoTemplateError, generate_oek_registry

    from bot.keyboards.admin_menu import oek_review
    from bot.services import mail_service

    period = current_period()
    if _done(oek_sent_key(period)):
        logger.info("Реестр ОЭК за %s уже отправлен — сверка не нужна", period)
        return True

    try:
        result = generate_oek_registry(period)
    except (NoTemplateError, OekFormatError) as exc:
        logger.warning("Реестр ОЭК к сверке не готов: %s", exc)
        await _tell_admins(bot, f"📨 Реестр ОЭК не сформирован.\n\n{exc}")
        return True                      # дело не в связи, повтор не поможет

    where = (", ".join(config.mail_to) if mail_service.is_configured()
             else "почта не настроена — отправлю только по кнопке")
    text = (
        f"📨 <b>Реестр ОЭК на сверку</b> — {period_title(period)}\n\n"
        f"{result.summary(period_title(period))}\n\n"
        f"Файл: <b>{result.path.name}</b> (имя ресурсника сохранено)\n"
        f"Сегодня в {config.oek_mail_hour:02d}:00 уйдёт на {where}.\n\n"
        "Если в показаниях ошибка — нажмите «⏸ Отложить отправку», "
        "исправьте и отправьте кнопкой, когда будете готовы."
    )

    ok = False
    for admin_id in config.admin_ids:
        try:
            await bot.send_document(admin_id, FSInputFile(result.path),
                                    caption=f"📨 Реестр ОЭК на сверку — "
                                            f"{period_title(period)}",
                                    reply_markup=oek_review(period))
            await bot.send_message(admin_id, text)
            ok = True
        except TelegramAPIError as exc:
            logger.warning("Не удалось прислать реестр на сверку %s: %s",
                           admin_id, exc)
    return ok


async def mail_oek_registry(bot: Bot) -> bool:
    """Отправляет реестр ресурснику по почте — по расписанию.

    Молча не отправляет в двух случаях: реестр уже ушёл (кнопкой) или
    председатель отложила отправку. Про оба случая пишет ей, иначе вечер
    выглядит одинаково — тишина.
    """
    from excel.oek_registry import OekFormatError
    from reports.oek_registry import NoTemplateError, generate_oek_registry

    from bot.services import mail_service

    period = current_period()
    if _done(oek_sent_key(period)):
        logger.info("Реестр ОЭК за %s уже отправлен — повтор не нужен", period)
        return True
    if _done(oek_hold_key(period)):
        await _tell_admins(
            bot, "⏸ Отправка реестра в ОЭК отложена — автоматически его "
                 "не отправляю. Когда проверите, нажмите «📧 Отправить "
                 "в ОЭК» под файлом.")
        return True
    if not mail_service.is_configured():
        await _tell_admins(
            bot, "📧 Реестр ОЭК не отправлен: почта не настроена. "
                 "Заполните в .env SMTP_USER, SMTP_PASSWORD и MAIL_TO.")
        return True

    try:
        result = generate_oek_registry(period)
    except (NoTemplateError, OekFormatError) as exc:
        logger.warning("Реестр ОЭК не сформирован: %s", exc)
        await _tell_admins(bot, f"📨 Реестр ОЭК не отправлен.\n\n{exc}")
        return True

    try:
        recipients = await asyncio.to_thread(
            mail_service.send, oek_mail_subject(period),
            oek_mail_body(period), result.path)
    except Exception as exc:                   # noqa: BLE001 — причина в тексте
        logger.exception("Не удалось отправить реестр ОЭК почтой")
        await _tell_admins(
            bot, f"📧 Реестр ОЭК не отправлен: {exc}\n\n"
                 "Проверю ещё раз на следующем круге. Файл готов — его можно "
                 "отправить кнопкой «📧 Отправить в ОЭК».")
        return False                           # связь могла моргнуть — повторим

    _claim(oek_sent_key(period))
    await _tell_admins(
        bot, f"📧 Реестр ОЭК за {period_title(period)} отправлен: "
             f"{', '.join(recipients)}.\nФайл: <b>{result.path.name}</b>")
    logger.info("Реестр ОЭК за %s отправлен на %s", period, recipients)
    return True


def oek_mail_subject(period: str) -> str:
    from bot.texts import HOUSE_ADDRESS
    return (f"Реестр показаний электроэнергии, {HOUSE_ADDRESS}, "
            f"{period_title(period)}")


def oek_mail_body(period: str) -> str:
    from bot.texts import HOUSE_ADDRESS, HOUSE_SHORT
    return ("Здравствуйте!\n\n"
            "Направляю реестр показаний приборов учёта электроэнергии "
            f"за {period_title(period)} по адресу: {HOUSE_ADDRESS}.\n\n"
            "Файл заполнен в присланной вами форме: имя файла и листы не "
            "изменялись, строки и столбцы не добавлялись, формулы не "
            "использовались.\n\n"
            "С уважением,\n"
            f"Председатель МКД {HOUSE_SHORT}")


async def _tell_admins(bot: Bot, text: str) -> None:
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, text)
        except TelegramAPIError as exc:
            logger.warning("Не удалось написать админу %s: %s", admin_id, exc)


async def deliver_oek_registry(bot: Bot, chat_id: int, result,
                               period_name: str, period: str = "") -> bool:
    """Отправляет файл реестра с отчётом. Общая для планировщика и кнопки."""
    period = period or current_period()
    summary = result.summary(period_name)
    # Подпись к документу в Telegram — не длиннее 1024 знаков. Если список
    # непередавших длинный, отправляем отчёт отдельным сообщением.
    caption, tail = (summary, "") if len(summary) <= CAPTION_LIMIT else (
        f"📨 <b>Реестр ОЭК</b> — {period_name}\n\n"
        f"Заполнено показаний: {len(result.filled)} из {result.rows_total}",
        summary)
    from bot.keyboards.admin_menu import oek_send_mail
    from bot.services import mail_service

    # Кнопку показываем, только если почта настроена: иначе она обещает
    # то, чего бот сделать не сможет
    keyboard = oek_send_mail(period) if mail_service.is_configured() else None
    try:
        await bot.send_document(chat_id, FSInputFile(result.path),
                                caption=caption, reply_markup=keyboard)
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
    """Напоминания председателю по задачам: пора начинать, срок, просрочка.

    Каждая задача уходит своим сообщением с кнопками: одним списком
    напоминание читается, но отметить выполненное в нём невозможно —
    кнопки живут при конкретной задаче.
    """
    from bot.keyboards.tasks import task_actions
    from bot.services import task_service, verification_service

    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)      # цикл всегда заполнен вперёд
        verification_service.ensure_house_meters(conn)
        verification_service.sync_verification_tasks(conn)
        reminders = task_service.reminders_with_rows(conn)
        # sqlite3.Row живёт вместе с соединением — забираем нужное сразу
        reminders = [(row["id"], row["status"], text)
                     for row, text in reminders]
    finally:
        conn.close()

    if not reminders:
        return 0

    sent = 0
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id, f"🗂 <b>Задачи на сегодня: {len(reminders)}</b>")
            for task_id, status, text in reminders:
                await bot.send_message(admin_id, text,
                                       reply_markup=task_actions(task_id, status))
            sent += 1
        except TelegramAPIError as exc:
            logger.warning("Не удалось отправить напоминание по задачам %s: %s",
                           admin_id, exc)
    return sent


# Обратная совместимость с прежним названием
run_reminder_scheduler = run_scheduler
