"""Меню председателя: реестр, ведомость, статистика, пользователи, бэкап."""
from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import FSInputFile, Message

from bot.config import config
from bot.keyboards.admin_menu import (BTN_ADMIN, BTN_BACK, BTN_BACKUP, BTN_DEBTORS,
                                      BTN_CHAT_REMINDER, BTN_DEBTORS_DOC,
                                      BTN_INVITE, BTN_REGISTRY,
                                      BTN_REMIND, BTN_SETTINGS, BTN_STATEMENT,
                                      BTN_STATS, BTN_USERS, BTN_WORKBOOK, admin_menu)
from bot.keyboards.menu import main_menu
from bot.scheduler import send_reminders
from bot.services.apartment_service import registry_summary
from bot.services.reading_service import current_period, period_title
from bot.services.reminder_service import debtors_text
from bot.services.report_service import stats_text
from bot.texts import collection_reminder_text, welcome_residents_text
from database import repository
from database.backup import make_backup
from reports.monthly_statement import generate_statement

router = Router()
router.message.filter(F.chat.type == "private",
                      F.from_user.id.in_(config.admin_ids))


@router.message(F.text == BTN_ADMIN)
async def open_admin_menu(message: Message) -> None:
    await message.answer("🛠 Меню председателя:", reply_markup=admin_menu())


@router.message(F.text == BTN_BACK)
async def back_to_main(message: Message) -> None:
    await message.answer("Главное меню:", reply_markup=main_menu(is_admin=True))


@router.message(F.text == BTN_REGISTRY)
async def show_registry(message: Message) -> None:
    conn = repository.connect()
    try:
        await message.answer(registry_summary(conn, current_period()))
    finally:
        conn.close()


@router.message(F.text == BTN_STATEMENT)
async def send_statement(message: Message) -> None:
    period = current_period()
    path = generate_statement(period)
    await message.answer_document(
        FSInputFile(path),
        caption=f"📄 Ведомость передачи показаний за {period_title(period)}",
    )


@router.message(F.text == BTN_WORKBOOK)
async def send_workbook(message: Message) -> None:
    from excel.workbook import generate_workbook
    period = current_period()
    await message.answer("Собираю книгу…")
    path = generate_workbook(period)
    await message.answer_document(
        FSInputFile(path),
        caption=("📗 DH OS — Модуль «Сбор показаний»\n"
                 f"Данные на {period_title(period)}.\n\n"
                 "Листы: Реестр квартир · Переданные показания · "
                 "Текущие показания · Контроль передачи · Настройки"),
    )


@router.message(F.text == BTN_STATS)
async def show_stats(message: Message) -> None:
    period = current_period()
    conn = repository.connect()
    try:
        await message.answer(stats_text(conn, period, period_title(period)))
    finally:
        conn.close()


@router.message(F.text == BTN_DEBTORS)
async def show_debtors(message: Message) -> None:
    period = current_period()
    conn = repository.connect()
    try:
        await message.answer(debtors_text(conn, period, period_title(period)))
    finally:
        conn.close()


@router.message(F.text == BTN_DEBTORS_DOC)
async def send_debtors_doc(message: Message) -> None:
    from reports.debtors_statement import generate_debtors_statement
    period = current_period()
    path, count = generate_debtors_statement(period)
    await message.answer_document(
        FSInputFile(path),
        caption=(f"📕 Ведомость непередавших показания — {period_title(period)}\n"
                 f"Не передали: {count}"),
    )


@router.message(F.text == BTN_REMIND)
async def remind_debtors(message: Message) -> None:
    sent = await send_reminders(message.bot)
    if sent:
        await message.answer(f"🔔 Напоминания отправлены: {sent}.")
    else:
        await message.answer("Напоминать некому — либо все сдали, либо должники "
                             "не зарегистрированы в боте.")


@router.message(F.text == BTN_INVITE)
async def send_invite(message: Message) -> None:
    me = await message.bot.get_me()
    text = welcome_residents_text(me.username)
    if config.group_chat_id:
        try:
            await message.bot.send_message(config.group_chat_id, text)
            await message.answer("📣 Памятка отправлена в общий чат. Рекомендую "
                                 "закрепить её в чате (в Telegram: удерживать сообщение "
                                 "→ «Закрепить»).")
            return
        except TelegramAPIError as exc:
            await message.answer(f"Не удалось отправить в чат ({exc}). "
                                 "Вот текст — скопируйте и отправьте в чат вручную:")
    else:
        await message.answer("Общий чат не подключён (GROUP_CHAT_ID пуст). "
                             "Вот готовый текст — скопируйте и отправьте в чат:")
    await message.answer(text)


@router.message(F.text == BTN_CHAT_REMINDER)
async def send_chat_reminder(message: Message) -> None:
    """Короткое напоминание о сроке сбора — в общий чат дома."""
    text = collection_reminder_text()
    if config.group_chat_id:
        try:
            await message.bot.send_message(config.group_chat_id, text)
            await message.answer("🔔 Напоминание отправлено в общий чат дома.")
            return
        except TelegramAPIError as exc:
            await message.answer(f"Не удалось отправить в чат ({exc}). "
                                 "Вот текст — скопируйте и отправьте вручную:")
    else:
        await message.answer("Общий чат не подключён (GROUP_CHAT_ID пуст). "
                             "Вот готовый текст — скопируйте и отправьте в чат:")
    await message.answer(text)


@router.message(F.text == BTN_USERS)
async def show_users(message: Message) -> None:
    conn = repository.connect()
    try:
        users = repository.list_users(conn)
    finally:
        conn.close()
    if not users:
        await message.answer("Пока никто не зарегистрировался.")
        return
    lines = ["👥 Зарегистрированные пользователи:", ""]
    for u in users:
        apt = u["apartment_number"] or "—"
        role = " (админ)" if u["role"] == "admin" else ""
        lines.append(f"кв. {apt} — {u['full_name']}{role}")
    await message.answer("\n".join(lines))


@router.message(F.text == BTN_SETTINGS)
async def show_settings(message: Message) -> None:
    await message.answer(
        "⚙ Настройки (файл .env):\n\n"
        f"Квартир: {config.apartments_count}\n"
        f"Нежилых помещений: {config.nonresidential_count}\n"
        f"Прием показаний: с {config.readings_day_start} по {config.readings_day_end} число\n"
        f"Чат дома (показания): {config.group_chat_id or 'не подключен'}\n"
        f"Чат Совета дома (сводка): {config.council_chat_id or 'не подключен'}\n"
        f"Администраторы: {', '.join(map(str, config.admin_ids)) or 'не заданы'}"
    )


@router.message(F.text == BTN_BACKUP)
async def send_backup(message: Message) -> None:
    path = make_backup()
    conn = repository.connect()
    try:
        repository.log_event(conn, message.from_user.id, "backup", str(path))
    finally:
        conn.close()
    await message.answer_document(FSInputFile(path),
                                  caption=f"💾 Резервная копия базы: {path.name}")
