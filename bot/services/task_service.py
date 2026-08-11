"""Задачи председателя: годовой цикл, статусы, напоминания, сводки.

Регулярные задачи описаны шаблонами (DEFAULT_TASK_TEMPLATES). Из каждого
шаблона на каждый месяц создаётся своя задача со сроком, статусом и историей.
Задачи создаются заранее на несколько месяцев вперёд, поэтому цикл сам
продолжается в следующем году — ничего пересоздавать вручную не нужно.
"""
import calendar
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from database import repository
from database.models import (DEFAULT_TASK_TEMPLATES, TASK_CATEGORIES,
                             TASK_OPEN_STATUSES, TASK_PRIORITIES, TASK_SOON_DAYS,
                             TASK_STATUSES)

# На сколько месяцев вперёд держим созданные задачи
MONTHS_AHEAD = 3

MONTHS_RU = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль",
             "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]


def ensure_templates(conn: sqlite3.Connection) -> None:
    """Заводит шаблоны регулярных задач (при первом запуске и после обновлений)."""
    for order, tpl in enumerate(DEFAULT_TASK_TEMPLATES, start=1):
        repository.upsert_task_template(
            conn, tpl["code"], tpl["title"], tpl["description"], tpl["category"],
            tpl["day_start"], tpl["day_end"], tpl["needs_amount"], order,
            amount_field=tpl.get("amount_field", "amount"),
            priority=tpl.get("priority", "normal"))
    # уточнения регламента подхватывают и уже созданные задачи
    repository.sync_tasks_with_templates(conn)


def _month_period(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _shift_month(d: date, months: int) -> date:
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, 1)


def _clamp_day(year: int, month: int, day: int) -> date:
    """День месяца с учётом коротких месяцев (30 февраля не бывает)."""
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def generate_tasks(conn: sqlite3.Connection, today: date | None = None,
                   months_ahead: int = MONTHS_AHEAD) -> int:
    """Создаёт задачи из шаблонов на текущий и ближайшие месяцы.

    Уже созданные не трогает, поэтому вызывать можно сколько угодно раз —
    например, при каждом запуске бота.
    """
    today = today or date.today()
    ensure_templates(conn)
    templates = repository.active_task_templates(conn)

    created = 0
    for offset in range(months_ahead + 1):
        first = _shift_month(today.replace(day=1), offset)
        period = _month_period(first)
        for tpl in templates:
            if repository.task_exists(conn, tpl["id"], period):
                continue
            start = _clamp_day(first.year, first.month, tpl["day_start"])
            due = _clamp_day(first.year, first.month, tpl["day_end"])
            repository.create_task(
                conn, tpl["title"],
                template_id=tpl["id"], period=period,
                description=tpl["description"], category=tpl["category"],
                priority=tpl["priority"], status="new", assignee=tpl["assignee"],
                start_date=start.isoformat(), due_date=due.isoformat(),
                source="regular")
            created += 1
    return created


def generate_year(conn: sqlite3.Connection, year: int) -> int:
    """Разворачивает годовой план: задачи из шаблонов на все 12 месяцев."""
    ensure_templates(conn)
    templates = repository.active_task_templates(conn)
    created = 0
    for month in range(1, 13):
        period = f"{year:04d}-{month:02d}"
        for tpl in templates:
            if repository.task_exists(conn, tpl["id"], period):
                continue
            start = _clamp_day(year, month, tpl["day_start"])
            due = _clamp_day(year, month, tpl["day_end"])
            repository.create_task(
                conn, tpl["title"],
                template_id=tpl["id"], period=period,
                description=tpl["description"], category=tpl["category"],
                priority=tpl["priority"], status="new", assignee=tpl["assignee"],
                start_date=start.isoformat(), due_date=due.isoformat(),
                source="regular")
            created += 1
    return created


# ---------------------------------------------------------------------------
# Состояние задачи
# ---------------------------------------------------------------------------

@dataclass
class TaskView:
    row: sqlite3.Row
    today: date

    @property
    def is_open(self) -> bool:
        return self.row["status"] in TASK_OPEN_STATUSES

    @property
    def due(self) -> date | None:
        return date.fromisoformat(self.row["due_date"]) if self.row["due_date"] else None

    @property
    def start(self) -> date | None:
        return (date.fromisoformat(self.row["start_date"])
                if self.row["start_date"] else None)

    @property
    def days_left(self) -> int | None:
        return (self.due - self.today).days if self.due else None

    @property
    def is_overdue(self) -> bool:
        return bool(self.is_open and self.due and self.due < self.today)

    @property
    def is_active_now(self) -> bool:
        """Окно выполнения уже открылось и ещё не закрыто."""
        if not self.is_open:
            return False
        if self.start and self.today < self.start:
            return False
        return not self.is_overdue

    @property
    def is_soon(self) -> bool:
        """До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться."""
        return bool(self.is_active_now and self.days_left is not None
                    and 0 <= self.days_left <= TASK_SOON_DAYS)

    @property
    def mark(self) -> str:
        if self.row["status"] == "done":
            return "✅"
        if self.row["status"] == "cancelled":
            return "🚫"
        if self.is_overdue:
            return "🔴"
        if self.is_soon:
            return "🟠"          # срок на носу
        if self.is_active_now:
            return "🟡"
        return "⚪"


def view(row: sqlite3.Row, today: date | None = None) -> TaskView:
    return TaskView(row, today or date.today())


def status_label(status: str) -> str:
    return TASK_STATUSES.get(status, status)


def category_label(category: str) -> str:
    return TASK_CATEGORIES.get(category, category)


def priority_label(priority: str) -> str:
    return TASK_PRIORITIES.get(priority, priority)


def period_title(period: str) -> str:
    year, month = period.split("-")
    return f"{MONTHS_RU[int(month) - 1]} {year}"


def _fmt_date(value: str) -> str:
    if not value:
        return ""
    y, m, d = value.split("-")
    return f"{d}.{m}"


def task_line(row: sqlite3.Row, today: date | None = None) -> str:
    """Одна строка задачи для списка в боте."""
    v = view(row, today)
    parts = [f"{v.mark} <b>{row['title']}</b>"]
    if row["due_date"]:
        parts.append(f"до {_fmt_date(row['due_date'])}")
    if v.is_overdue:
        parts.append(f"просрочено на {abs(v.days_left)} дн.")
    elif v.is_open and v.days_left is not None and v.days_left <= TASK_SOON_DAYS:
        parts.append("сегодня последний день" if v.days_left == 0
                     else f"осталось {v.days_left} дн.")
    if row["amount"] is not None:
        parts.append(f"аренда {row['amount']:g} ₽"
                     + (f" от {_fmt_date(row['paid_at'])}" if row["paid_at"] else ""))
    if row["utility_amount"] is not None:
        parts.append(f"коммуналка {row['utility_amount']:g} ₽"
                     + (f" от {_fmt_date(row['utility_paid_at'])}"
                        if row["utility_paid_at"] else ""))
    return " · ".join(parts)


# ---------------------------------------------------------------------------
# Списки и сводки
# ---------------------------------------------------------------------------

def month_plan_text(conn: sqlite3.Connection, period: str,
                    today: date | None = None) -> str:
    rows = repository.tasks_for_period(conn, period)
    if not rows:
        return f"На {period_title(period)} задач нет."
    lines = [f"📅 <b>План на {period_title(period)}</b>", ""]
    done = sum(1 for r in rows if r["status"] == "done")
    for row in rows:
        lines.append(task_line(row, today))
        lines.append(f"    <i>{category_label(row['category'])}</i>")
    lines.append("")
    lines.append(f"Выполнено: {done} из {len(rows)}")
    return "\n".join(lines)


def urgent_text(conn: sqlite3.Connection, today: date | None = None) -> str:
    """Просроченные и текущие задачи — то, чем заняться сейчас."""
    today = today or date.today()
    rows = repository.open_tasks(conn)
    overdue = [r for r in rows if view(r, today).is_overdue]
    active = [r for r in rows if view(r, today).is_active_now]
    soon = [r for r in rows
            if view(r, today).start and view(r, today).start > today
            and (view(r, today).start - today).days <= 7]

    if not (overdue or active or soon):
        return "✅ Просроченных и текущих задач нет."

    lines = []
    if overdue:
        lines += ["🔴 <b>Просрочено</b>", ""]
        lines += [task_line(r, today) for r in overdue] + [""]
    if active:
        lines += ["🟡 <b>Сейчас в работе</b>", ""]
        lines += [task_line(r, today) for r in active] + [""]
    if soon:
        lines += ["⚪ <b>Скоро начнётся</b>", ""]
        lines += [f"{r['title']} — с {_fmt_date(r['start_date'])}" for r in soon]
    return "\n".join(lines).strip()


def one_off_text(conn: sqlite3.Connection, today: date | None = None) -> str:
    """Разовые задачи председателя — то, что он планирует сам."""
    today = today or date.today()
    rows = repository.one_off_tasks(conn)
    if not rows:
        return ("📌 Разовых задач нет.\n\n"
                "Нажмите «➕ Новая задача», чтобы запланировать своё дело — "
                "срок бот будет отсчитывать сам.")
    lines = ["📌 <b>Мои задачи</b>", ""]
    for row in rows:
        lines.append(task_line(row, today))
        lines.append(f"    <i>{category_label(row['category'])}</i>")
    return "\n".join(lines)


def council_candidates(conn: sqlite3.Connection,
                       today: date | None = None) -> list[sqlite3.Row]:
    """Задачи, которые есть смысл предложить Совету дома.

    Совету рассказывают о разовых делах — ремонт, благоустройство, документы,
    а не о ежемесячном регламенте (выписки, квитанции, абонентские платы).
    Поэтому предлагаются разовые задачи: открытые и закрытые в этом месяце.
    """
    today = today or date.today()
    month_start = today.replace(day=1).isoformat()
    return [
        r for r in repository.one_off_tasks_all(conn)
        if r["status"] in TASK_OPEN_STATUSES
        or (r["status"] == "done" and r["done_at"] >= month_start)
    ]


def council_digest(conn: sqlite3.Connection, today: date | None = None,
                   task_ids: list[int] | None = None) -> str:
    """Информационная сводка для Совета дома.

    Только заголовки, сроки и статусы — внутренние описания, суммы и
    комментарии в неё не попадают. Если передан `task_ids`, в сводку идут
    только выбранные председателем задачи.
    """
    today = today or date.today()
    if task_ids is not None:
        chosen = [repository.get_task(conn, task_id) for task_id in task_ids]
        rows = [r for r in chosen if r is not None]
        in_work = [r for r in rows if r["status"] in TASK_OPEN_STATUSES
                   and r["status"] != "waiting"]
        waiting = [r for r in rows if r["status"] == "waiting"]
        done_recent = [r for r in rows if r["status"] == "done"]
        return _digest_text(today, in_work, waiting, done_recent)

    rows = repository.open_tasks(conn)
    in_work = [r for r in rows if r["status"] == "in_progress"]
    waiting = [r for r in rows if r["status"] == "waiting"]

    month_start = today.replace(day=1)
    done_recent = [
        r for r in repository.tasks_for_period(conn, _month_period(today))
        if r["status"] == "done" and r["done_at"] >= month_start.isoformat()
    ]
    return _digest_text(today, in_work, waiting, done_recent)


def _digest_text(today: date, in_work: list, waiting: list,
                 done_recent: list) -> str:
    """Собирает текст сводки из трёх групп задач."""
    lines = [f"📋 <b>Совет дома — сводка по задачам на "
             f"{today.strftime('%d.%m.%Y')}</b>", ""]
    if in_work:
        lines.append(f"🔧 <b>В работе ({len(in_work)})</b>")
        for r in in_work:
            due = f" — до {_fmt_date(r['due_date'])}" if r["due_date"] else ""
            who = f", {r['assignee']}" if r["assignee"] else ""
            lines.append(f"• {r['title']}{due}{who}")
        lines.append("")
    if waiting:
        lines.append(f"⏳ <b>Ожидают решения ({len(waiting)})</b>")
        lines += [f"• {r['title']}" for r in waiting]
        lines.append("")
    if done_recent:
        lines.append(f"✅ <b>Выполнено в этом месяце ({len(done_recent)})</b>")
        lines += [f"• {r['title']}" for r in done_recent]
        lines.append("")
    if len(lines) <= 2:
        lines.append("Открытых задач нет.")
    lines.append("Вопросы — председателю.")
    return "\n".join(lines)


def reminders_for_today(conn: sqlite3.Connection,
                        today: date | None = None) -> list[str]:
    """Тексты напоминаний председателю на сегодня."""
    today = today or date.today()
    messages = []
    for row in repository.open_tasks(conn):
        v = view(row, today)
        if v.is_overdue:
            messages.append(
                f"🔴 <b>Просрочено:</b> {row['title']}\n"
                f"Срок был {_fmt_date(row['due_date'])} "
                f"({abs(v.days_left)} дн. назад).")
        elif v.start == today:
            messages.append(
                f"🟡 <b>Пора начинать:</b> {row['title']}\n"
                f"Срок — до {_fmt_date(row['due_date'])}.")
        elif v.is_soon:
            when = ("сегодня последний день" if v.days_left == 0
                    else "завтра" if v.days_left == 1
                    else f"осталось {v.days_left} дн.")
            urgent = "❗ " if row["priority"] == "high" else ""
            messages.append(
                f"🟠 {urgent}<b>Скоро срок:</b> {row['title']} — {when} "
                f"(до {_fmt_date(row['due_date'])}).")
    return messages


def complete_task(conn: sqlite3.Connection, task_id: int, tg_id: int | None,
                  amount: float | None = None, paid_at: str | None = None,
                  amount_field: str = "amount") -> None:
    """Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка."""
    date_field = "paid_at" if amount_field == "amount" else "utility_paid_at"
    fields = {"status": "done", "done_at": date.today().isoformat()}
    if amount is not None:
        fields[amount_field] = amount
    if paid_at:
        fields[date_field] = paid_at
    repository.update_task(conn, task_id, **fields)

    kind = "аренда" if amount_field == "amount" else "коммуналка"
    details = "выполнена"
    if amount is not None:
        details += f", {kind} {amount:g} ₽"
    if paid_at:
        details += f", дата {paid_at}"
    repository.log_task_event(conn, task_id, tg_id, "status", details)


def set_status(conn: sqlite3.Connection, task_id: int, status: str,
               tg_id: int | None) -> None:
    fields = {"status": status}
    if status == "done":
        fields["done_at"] = date.today().isoformat()
    repository.update_task(conn, task_id, **fields)
    repository.log_task_event(conn, task_id, tg_id, "status",
                              status_label(status))
