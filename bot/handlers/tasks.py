"""Меню задач председателя. Доступно только администраторам из ADMIN_IDS."""
import logging
from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import config
from bot.keyboards.admin_menu import admin_menu
from bot.keyboards.tasks import (BTN_COUNCIL, BTN_MONTH_PLAN, BTN_NEW_TASK,
                                 BTN_TASKS, BTN_TASKS_BACK, BTN_URGENT,
                                 BTN_YEAR_PLAN, categories_keyboard,
                                 task_actions, tasks_menu)
from bot.services import task_service
from bot.states.tasks import CompleteTask, NewTask
from database import repository
from database.models import TASK_CATEGORIES

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == "private", F.from_user.id.in_(config.admin_ids))
router.callback_query.filter(F.from_user.id.in_(config.admin_ids))


def _period_now() -> str:
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"


@router.message(F.text == BTN_TASKS)
async def open_tasks_menu(message: Message) -> None:
    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)      # держим цикл заполненным вперёд
        text = task_service.urgent_text(conn)
    finally:
        conn.close()
    await message.answer(f"🗂 <b>Задачи председателя</b>\n\n{text}",
                         reply_markup=tasks_menu())


@router.message(F.text == BTN_TASKS_BACK)
async def back_to_admin(message: Message) -> None:
    await message.answer("🛠 Меню председателя:", reply_markup=admin_menu())


@router.message(F.text == BTN_MONTH_PLAN)
async def show_month_plan(message: Message) -> None:
    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)
        await message.answer(task_service.month_plan_text(conn, _period_now()))
    finally:
        conn.close()


@router.message(F.text == BTN_URGENT)
async def show_urgent(message: Message) -> None:
    """Каждую открытую задачу отправляем отдельно — с кнопками управления."""
    conn = repository.connect()
    try:
        task_service.generate_tasks(conn)
        rows = repository.open_tasks(conn)
    finally:
        conn.close()

    today = date.today()
    actionable = [r for r in rows
                  if task_service.view(r, today).is_overdue
                  or task_service.view(r, today).is_active_now]
    if not actionable:
        await message.answer("✅ Просроченных и текущих задач нет.")
        return

    for row in actionable:
        await message.answer(
            f"{task_service.task_line(row, today)}\n"
            f"<i>{task_service.category_label(row['category'])}</i>"
            + (f"\n{row['description']}" if row["description"] else ""),
            reply_markup=task_actions(row["id"], row["status"]))


@router.message(F.text == BTN_COUNCIL)
async def send_council_digest(message: Message) -> None:
    conn = repository.connect()
    try:
        digest = task_service.council_digest(conn)
    finally:
        conn.close()

    if config.group_chat_id:
        try:
            await message.bot.send_message(config.group_chat_id, digest)
            await message.answer("📤 Сводка отправлена в чат дома.")
            return
        except TelegramAPIError as exc:
            await message.answer(f"Не удалось отправить в чат ({exc}). "
                                 "Вот текст — можно переслать вручную:")
    else:
        await message.answer("Чат не подключён. Вот текст сводки — перешлите "
                             "Совету дома:")
    await message.answer(digest)


@router.message(F.text == BTN_YEAR_PLAN)
async def send_year_plan(message: Message) -> None:
    from excel.tasks_export import export_year_plan
    year = date.today().year
    conn = repository.connect()
    try:
        task_service.generate_year(conn, year)
        path = export_year_plan(conn, year)
    finally:
        conn.close()
    await message.answer_document(
        FSInputFile(path),
        caption=(f"📊 Годовой план задач на {year} год\n"
                 "Помесячно, со сроками, статусами и суммами оплат."))


# ---------------------------------------------------------------------------
# Управление статусом
# ---------------------------------------------------------------------------

@router.callback_query(F.data.startswith("task:"))
async def change_task_status(callback: CallbackQuery, state: FSMContext) -> None:
    _, task_id_raw, action = callback.data.split(":")
    task_id = int(task_id_raw)

    conn = repository.connect()
    try:
        task = repository.get_task(conn, task_id)
        if task is None:
            await callback.answer("Задача не найдена")
            return
        template = None
        if task["template_id"]:
            template = conn.execute(
                "SELECT * FROM task_templates WHERE id = ?",
                (task["template_id"],)).fetchone()

        # Задача с суммой (оплата) — спросим сумму и дату
        if action == "done" and template and template["needs_amount"]:
            await state.update_data(task_id=task_id, title=task["title"])
            await state.set_state(CompleteTask.amount)
            await callback.message.answer(
                f"💰 <b>{task['title']}</b>\nВведите сумму оплаты в рублях "
                "(например: 4520,30):")
            await callback.answer()
            return

        task_service.set_status(conn, task_id, action, callback.from_user.id)
        updated = repository.get_task(conn, task_id)
        line = task_service.task_line(updated)
    finally:
        conn.close()

    await callback.message.edit_text(
        f"{line}\n<i>{task_service.status_label(action)}</i>",
        reply_markup=task_actions(task_id, action)
        if action in ("new", "in_progress", "waiting") else None)
    await callback.answer(task_service.status_label(action))


@router.message(CompleteTask.amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    from bot.services.validation import parse_value
    amount = parse_value(message.text or "")
    if amount is None:
        await message.answer("Не похоже на сумму. Введите число, например 4520,30")
        return
    await state.update_data(amount=amount)
    await state.set_state(CompleteTask.paid_at)
    today = date.today().strftime("%d.%m.%Y")
    await message.answer(f"📅 Дата оплаты? Отправьте «сегодня» ({today}) "
                         "или дату в виде 15.09.2026")


@router.message(CompleteTask.paid_at)
async def process_paid_at(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().lower()
    if text in ("сегодня", "today"):
        paid = date.today()
    else:
        try:
            day, month, year = text.replace("/", ".").split(".")
            paid = date(int(year), int(month), int(day))
        except (ValueError, TypeError):
            await message.answer("Не разобрал дату. Пример: 15.09.2026 "
                                 "или напишите «сегодня».")
            return

    data = await state.get_data()
    await state.clear()

    conn = repository.connect()
    try:
        task_service.complete_task(conn, data["task_id"], message.from_user.id,
                                   amount=data["amount"], paid_at=paid.isoformat())
    finally:
        conn.close()

    await message.answer(
        f"✅ <b>{data['title']}</b> — выполнено.\n"
        f"Сумма: {data['amount']:g} ₽\n"
        f"Дата оплаты: {paid.strftime('%d.%m.%Y')}",
        reply_markup=tasks_menu())


# ---------------------------------------------------------------------------
# Новая разовая задача
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_NEW_TASK)
async def new_task_start(message: Message, state: FSMContext) -> None:
    await state.set_state(NewTask.title)
    await message.answer("Что нужно сделать? Напишите коротко одной строкой.")


@router.message(NewTask.title)
async def new_task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if len(title) < 3:
        await message.answer("Слишком коротко — опишите задачу яснее.")
        return
    await state.update_data(title=title)
    await state.set_state(NewTask.category)
    await message.answer("Выберите категорию:",
                         reply_markup=categories_keyboard(TASK_CATEGORIES))


@router.callback_query(NewTask.category, F.data.startswith("newtask:cat:"))
async def new_task_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":")[-1]
    await state.update_data(category=category)
    await state.set_state(NewTask.due_date)
    await callback.message.answer(
        "До какого числа? Отправьте дату в виде 30.09.2026 "
        "или «без срока».")
    await callback.answer()


@router.message(NewTask.due_date)
async def new_task_due(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip().lower()
    due = ""
    if text not in ("без срока", "нет", "-"):
        try:
            day, month, year = text.replace("/", ".").split(".")
            due = date(int(year), int(month), int(day)).isoformat()
        except (ValueError, TypeError):
            await message.answer("Не разобрал дату. Пример: 30.09.2026 "
                                 "или напишите «без срока».")
            return

    data = await state.get_data()
    await state.clear()

    conn = repository.connect()
    try:
        task_id = repository.create_task(
            conn, data["title"], category=data["category"], priority="normal",
            status="new", due_date=due, source="chairman",
            period=_period_now() if due else "")
        repository.log_task_event(conn, task_id, message.from_user.id,
                                  "created", data["title"])
        row = repository.get_task(conn, task_id)
        line = task_service.task_line(row)
    finally:
        conn.close()

    await message.answer(f"➕ Задача добавлена:\n{line}",
                         reply_markup=tasks_menu())
