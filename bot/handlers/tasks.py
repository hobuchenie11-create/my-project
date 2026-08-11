"""Меню задач председателя. Доступно только администраторам из ADMIN_IDS."""
import asyncio
import logging
from datetime import date

from aiogram import F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.config import config
from bot.keyboards.admin_menu import admin_menu
from bot.keyboards.tasks import (BTN_COUNCIL, BTN_IMPORT_PLAN, BTN_MONTH_PLAN,
                                 BTN_NEW_TASK, BTN_ONE_OFF, BTN_TASKS,
                                 BTN_TASKS_BACK, BTN_URGENT, BTN_VERIFICATION,
                                 BTN_YEAR_PLAN, categories_keyboard,
                                 council_confirm, council_selection,
                                 meter_actions, task_actions, tasks_menu)
from bot.services import task_service, verification_service
from bot.states.tasks import (CompleteTask, CouncilDigest, MeterInterval,
                              NewTask, Verification)
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
        verification_service.ensure_house_meters(conn)
        verification_service.sync_verification_tasks(conn)
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


@router.message(F.text == BTN_ONE_OFF)
async def show_one_off(message: Message) -> None:
    """Разовые задачи председателя — с кнопками управления у каждой."""
    conn = repository.connect()
    try:
        text = task_service.one_off_text(conn)
        rows = repository.one_off_tasks(conn)
    finally:
        conn.close()

    if not rows:
        await message.answer(text)
        return

    await message.answer("📌 <b>Мои задачи</b>")
    today = date.today()
    for row in rows:
        await message.answer(
            f"{task_service.task_line(row, today)}\n"
            f"<i>{task_service.category_label(row['category'])}</i>",
            reply_markup=task_actions(row["id"], row["status"]))


@router.message(F.text == BTN_VERIFICATION)
async def show_verification(message: Message) -> None:
    """Общедомовые приборы и сроки их поверки."""
    conn = repository.connect()
    try:
        verification_service.ensure_house_meters(conn)
        verification_service.sync_verification_tasks(conn)
        rows = repository.house_meters(conn)
    finally:
        conn.close()

    await message.answer(
        "🔧 <b>Поверка общедомовых приборов</b>\n\n"
        "Срок следующей поверки считается сам: дата последней поверки плюс "
        "межповерочный интервал. За полгода до срока появится задача.")

    today = date.today()
    for row in rows:
        v = verification_service.view(row, today)
        lines = [f"{v.mark} <b>{row['name']}</b>"]
        lines.append(f"Последняя поверка: "
                     f"{verification_service._fmt(row['last_verified'])}")
        if v.next_due:
            lines.append(f"Следующая: {verification_service._fmt(v.next_due)} "
                         f"({v.status_text})")
        else:
            lines.append("<i>Внесите дату последней поверки — "
                         "и срок посчитается автоматически.</i>")
        lines.append(f"Интервал: {row['interval_years']} г.")
        if row["serial"]:
            lines.append(f"Заводской №: {row['serial']}")
        await message.answer("\n".join(lines), reply_markup=meter_actions(row["id"]))


@router.callback_query(F.data.startswith("meter:"))
async def meter_action(callback: CallbackQuery, state: FSMContext) -> None:
    _, meter_id_raw, action = callback.data.split(":")
    meter_id = int(meter_id_raw)

    conn = repository.connect()
    try:
        meter = repository.get_house_meter(conn, meter_id)
    finally:
        conn.close()
    if meter is None:
        await callback.answer("Прибор не найден")
        return

    await state.update_data(meter_id=meter_id, meter_name=meter["name"])
    if action == "verify":
        await state.set_state(Verification.verified_at)
        await callback.message.answer(
            f"📅 <b>{meter['name']}</b>\nКогда проведена поверка? "
            "Отправьте дату в виде 15.09.2026 (или «сегодня»).")
    else:
        await state.set_state(MeterInterval.years)
        await callback.message.answer(
            f"⚙️ <b>{meter['name']}</b>\nМежповерочный интервал сейчас "
            f"{meter['interval_years']} г. Введите новый в годах (например: 4).")
    await callback.answer()


@router.message(Verification.verified_at)
async def verification_date(message: Message, state: FSMContext) -> None:
    parsed = _parse_date(message.text)
    if parsed is None:
        await message.answer("Не разобрал дату. Пример: 15.09.2026 "
                             "или напишите «сегодня».")
        return
    await state.update_data(verified_at=parsed.isoformat())
    await state.set_state(Verification.document)
    await message.answer("Номер акта или свидетельства о поверке? "
                         "Отправьте номер или «пропустить».")


@router.message(Verification.document)
async def verification_document(message: Message, state: FSMContext) -> None:
    document = (message.text or "").strip()
    if document.lower() in ("пропустить", "-", "нет"):
        document = ""
    data = await state.get_data()
    await state.clear()

    verified_at = date.fromisoformat(data["verified_at"])
    conn = repository.connect()
    try:
        following = verification_service.register_verification(
            conn, data["meter_id"], verified_at, document)
        verification_service.sync_verification_tasks(conn)
    finally:
        conn.close()

    await message.answer(
        f"✅ Поверка записана: <b>{data['meter_name']}</b>\n"
        f"Проведена: {verified_at.strftime('%d.%m.%Y')}\n"
        f"Следующая поверка: <b>{following.strftime('%d.%m.%Y')}</b>"
        + (f"\nДокумент: {document}" if document else "")
        + "\n\nСрок посчитан автоматически — напомню заранее.",
        reply_markup=tasks_menu())


@router.message(MeterInterval.years)
async def meter_interval(message: Message, state: FSMContext) -> None:
    text = (message.text or "").strip()
    if not text.isdigit() or not 1 <= int(text) <= 20:
        await message.answer("Введите интервал в годах числом, например: 4")
        return
    years = int(text)
    data = await state.get_data()
    await state.clear()

    conn = repository.connect()
    try:
        repository.update_house_meter(conn, data["meter_id"], interval_years=years)
        meter = repository.get_house_meter(conn, data["meter_id"])
        following = verification_service.next_due(meter["last_verified"], years)
        verification_service.sync_verification_tasks(conn)
    finally:
        conn.close()

    answer = (f"⚙️ <b>{data['meter_name']}</b>\n"
              f"Межповерочный интервал: {years} г.")
    if following:
        answer += f"\nСледующая поверка: <b>{following.strftime('%d.%m.%Y')}</b>"
    await message.answer(answer, reply_markup=tasks_menu())


def _parse_date(text: str | None) -> date | None:
    value = (text or "").strip().lower()
    if value in ("сегодня", "today"):
        return date.today()
    try:
        day, month, year = value.replace("/", ".").split(".")
        return date(int(year), int(month), int(day))
    except (ValueError, TypeError):
        return None


@router.message(F.text == BTN_COUNCIL)
async def start_council_digest(message: Message, state: FSMContext) -> None:
    """Совету уходит не весь план, а только отмеченные председателем задачи."""
    conn = repository.connect()
    try:
        rows = task_service.council_candidates(conn)
    finally:
        conn.close()

    if not rows:
        await message.answer(
            "Пока нечего сообщать Совету: разовых задач нет.\n\n"
            "Задачи ставятся кнопкой ➕ Новая задача — они и будут "
            "предлагаться для сводки.")
        return

    await state.set_state(CouncilDigest.choosing)
    await state.update_data(selected=[])
    await message.answer(
        "📤 <b>Сводка для Совета дома</b>\n\n"
        "Отметьте задачи, о которых сообщаем Совету, — уйдут только они. "
        "Ежемесячный регламент (выписки, квитанции, абонентские платы) "
        "в список не попадает.\n\n"
        "Потом «👁 Показать сводку» — увидите текст перед отправкой.",
        reply_markup=council_selection(rows, set()))


@router.callback_query(CouncilDigest.choosing, F.data.startswith("council:"))
async def council_choose(callback: CallbackQuery, state: FSMContext) -> None:
    action = callback.data.split(":")[1]
    data = await state.get_data()
    selected = set(data.get("selected", []))

    conn = repository.connect()
    try:
        rows = task_service.council_candidates(conn)
        if action == "toggle":
            task_id = int(callback.data.split(":")[2])
            selected.symmetric_difference_update({task_id})
        elif action == "all":
            selected = {r["id"] for r in rows}
        elif action == "none":
            selected = set()
        elif action == "cancel":
            await state.clear()
            await callback.message.edit_text("Отправка сводки отменена.")
            await callback.answer()
            return
        elif action == "preview":
            if not selected:
                await callback.answer("Сначала отметьте хотя бы одну задачу",
                                      show_alert=True)
                return
            order = [r["id"] for r in rows if r["id"] in selected]
            digest = task_service.council_digest(conn, task_ids=order)
        else:
            await callback.answer()
            return
    finally:
        conn.close()

    await state.update_data(selected=sorted(selected))

    if action == "preview":
        await state.set_state(CouncilDigest.confirming)
        await callback.message.edit_text(
            f"Так сводка придёт Совету дома:\n\n{digest}",
            reply_markup=council_confirm())
        await callback.answer()
        return

    await callback.message.edit_reply_markup(
        reply_markup=council_selection(rows, selected))
    await callback.answer()


@router.callback_query(CouncilDigest.confirming, F.data.startswith("council:"))
async def council_confirmation(callback: CallbackQuery,
                               state: FSMContext) -> None:
    action = callback.data.split(":")[1]
    data = await state.get_data()
    selected = set(data.get("selected", []))

    if action == "cancel":
        await state.clear()
        await callback.message.edit_text("Отправка сводки отменена. "
                                         "Совету ничего не ушло.")
        await callback.answer()
        return

    conn = repository.connect()
    try:
        rows = task_service.council_candidates(conn)
        if action == "back":
            await state.set_state(CouncilDigest.choosing)
            await callback.message.edit_text(
                "Отметьте задачи для Совета дома:",
                reply_markup=council_selection(rows, selected))
            await callback.answer()
            return

        order = [r["id"] for r in rows if r["id"] in selected]
        digest = task_service.council_digest(conn, task_ids=order)
    finally:
        conn.close()

    if action != "send":
        await callback.answer()
        return

    await state.clear()
    await _deliver_digest(callback.message, digest, len(order))
    await callback.answer("Отправлено")


@router.callback_query(F.data.startswith("council:"))
async def council_stale(callback: CallbackQuery) -> None:
    """Кнопки из старого сообщения: список уже не тот — предлагаем начать заново."""
    await callback.answer("Этот список устарел. Нажмите «📤 Сводка для Совета "
                          "дома» ещё раз.", show_alert=True)


def _tasks_word(count: int) -> str:
    """«1 задача», «2 задачи», «5 задач»."""
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} задача"
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return f"{count} задачи"
    return f"{count} задач"


async def _deliver_digest(message: Message, digest: str, count: int) -> None:
    """Отправляет сводку в чат Совета дома — и никогда в чат показаний."""
    if config.council_chat_id:
        try:
            await message.bot.send_message(config.council_chat_id, digest)
            await message.answer(
                f"📤 Сводка отправлена в чат Совета дома ({_tasks_word(count)}).",
                reply_markup=tasks_menu())
            return
        except TelegramAPIError as exc:
            await message.answer(
                f"Не удалось отправить в чат Совета дома ({exc}).\n"
                "Проверьте, что бот добавлен в этот чат и не заблокирован. "
                "Вот текст — можно переслать вручную:")
    else:
        await message.answer(
            "Чат Совета дома не подключён.\n\n"
            "Как подключить: добавьте бота в чат Совета, отправьте там "
            "команду /chatid и впишите полученное число в файл .env в строку "
            "<code>COUNCIL_CHAT_ID</code>, затем перезапустите бота.\n\n"
            "Пока вот текст сводки — перешлите Совету вручную:")
    await message.answer(digest, reply_markup=tasks_menu())


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
                 "Помесячно, со сроками, статусами и суммами оплат.\n\n"
                 "Правки в файле сохраняются в боте: отредактируйте, "
                 "нажмите «📥 Загрузить правки» и пришлите файл обратно."))


# ---------------------------------------------------------------------------
# Обратная загрузка: правки из Excel возвращаются в базу
# ---------------------------------------------------------------------------

@router.message(F.text == BTN_IMPORT_PLAN)
async def import_plan_hint(message: Message) -> None:
    await message.answer(
        "📥 <b>Загрузка правок из Excel</b>\n\n"
        "Пришлите сюда файл годового плана — тот, что бот выгрузил, "
        "с вашими изменениями. Я перенесу их в базу:\n"
        "• «Годовой план» — статусы, суммы, даты оплат, комментарии;\n"
        "• «Мои задачи» — правки и новые строки (их бот заведёт как задачи);\n"
        "• «Поверка приборов» — даты поверки и интервалы.\n\n"
        "Пустая ячейка означает «не менять» — так случайное стирание "
        "не удалит данные. Скрытый столбец «ID» удалять нельзя: по нему "
        "строка находит свою задачу.")


@router.message(F.document)
async def import_plan_file(message: Message) -> None:
    """Присланный xlsx — это правки годового плана: переносим их в базу."""
    from excel.tasks_import import import_year_plan

    name = message.document.file_name or ""
    if not name.lower().endswith((".xlsx", ".xlsm")):
        await message.answer("Жду файл Excel (.xlsx) — годовой план задач.")
        return

    inbox = config.reports_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    path = inbox / f"{date.today().isoformat()}_{name}"
    await message.bot.download(message.document, destination=path)

    def run_import():
        # Своё подключение: соединение SQLite нельзя делить между потоками
        conn = repository.connect()
        try:
            return import_year_plan(conn, path, message.from_user.id)
        finally:
            conn.close()

    try:
        result = await asyncio.to_thread(run_import)
    except Exception as exc:                       # noqa: BLE001 — покажем причину
        logger.exception("Не удалось загрузить правки из %s", path)
        await message.answer(f"Не удалось прочитать файл: {exc}\n\n"
                             "Пришлите книгу, выгруженную ботом "
                             "(🗂 Задачи → 📊 Годовой план).")
        return

    await message.answer(f"📥 <b>Правки загружены</b>\n\n{result.text()}",
                         reply_markup=tasks_menu())


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
            field = template["amount_field"] or "amount"
            kind = "аренды" if field == "amount" else "оплаты коммунальных услуг"
            await state.update_data(task_id=task_id, title=task["title"],
                                    amount_field=field)
            await state.set_state(CompleteTask.amount)
            await callback.message.answer(
                f"💰 <b>{task['title']}</b>\nВведите сумму {kind} в рублях "
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
        field = data.get("amount_field", "amount")
        task_service.complete_task(conn, data["task_id"], message.from_user.id,
                                   amount=data["amount"], paid_at=paid.isoformat(),
                                   amount_field=field)
    finally:
        conn.close()

    label = "Аренда" if field == "amount" else "Оплата коммунальных услуг"
    await message.answer(
        f"✅ <b>{data['title']}</b> — выполнено.\n"
        f"{label}: {data['amount']:g} ₽\n"
        f"Дата: {paid.strftime('%d.%m.%Y')}",
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
            period=due[:7] if due else "")
        repository.log_task_event(conn, task_id, message.from_user.id,
                                  "created", data["title"])
        row = repository.get_task(conn, task_id)
        line = task_service.task_line(row)
    finally:
        conn.close()

    await message.answer(f"➕ Задача добавлена:\n{line}",
                         reply_markup=tasks_menu())
