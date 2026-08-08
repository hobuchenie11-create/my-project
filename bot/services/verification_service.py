"""Поверка общедомовых приборов учёта (тепло, ГВС, ХВС).

У каждого прибора свой межповерочный интервал (по умолчанию 4 года) и своя
дата последней поверки. Срок следующей поверки считается автоматически:

    следующая поверка = дата последней поверки + интервал

За VERIFICATION_LEAD_DAYS дней до срока в задачах председателя появляется
задача «Поверка …» — поверку нужно успеть организовать (заявка, доступ, акт).
Когда поверка проведена и внесена новая дата, срок пересчитывается сам, и
через интервал задача появится снова.
"""
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta

from database import repository
from database.models import (DEFAULT_HOUSE_METERS, TASK_SOON_DAYS,
                             VERIFICATION_INTERVAL_YEARS, VERIFICATION_LEAD_DAYS)


def ensure_house_meters(conn: sqlite3.Connection) -> None:
    """Заводит общедомовые приборы (без дат — их вносит председатель)."""
    for order, meter in enumerate(DEFAULT_HOUSE_METERS, start=1):
        repository.ensure_house_meter(conn, meter["code"], meter["name"], order,
                                      VERIFICATION_INTERVAL_YEARS)


def add_years(d: date, years: int) -> date:
    """Дата через N лет. 29 февраля переносится на 28-е."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return d.replace(year=d.year + years, day=28)


def next_due(last_verified: str, interval_years: int) -> date | None:
    """Срок следующей поверки. None, если дата последней ещё не внесена."""
    if not last_verified:
        return None
    return add_years(date.fromisoformat(last_verified), interval_years)


@dataclass
class MeterView:
    row: sqlite3.Row
    today: date

    @property
    def next_due(self) -> date | None:
        return next_due(self.row["last_verified"], self.row["interval_years"])

    @property
    def days_left(self) -> int | None:
        return (self.next_due - self.today).days if self.next_due else None

    @property
    def is_overdue(self) -> bool:
        return bool(self.next_due and self.next_due < self.today)

    @property
    def is_due_soon(self) -> bool:
        """Срок поверки в пределах периода подготовки."""
        left = self.days_left
        return bool(left is not None and 0 <= left <= VERIFICATION_LEAD_DAYS)

    @property
    def mark(self) -> str:
        if self.next_due is None:
            return "⚪"          # дата поверки ещё не внесена
        if self.is_overdue:
            return "🔴"
        if self.days_left is not None and self.days_left <= TASK_SOON_DAYS:
            return "🟠"
        if self.is_due_soon:
            return "🟡"
        return "✅"

    @property
    def status_text(self) -> str:
        if self.next_due is None:
            return "дата поверки не внесена"
        if self.is_overdue:
            return f"просрочена на {abs(self.days_left)} дн."
        if self.days_left == 0:
            return "срок сегодня"
        if self.is_due_soon:
            return f"через {self.days_left} дн."
        years = self.days_left // 365
        return f"через {years} г." if years else f"через {self.days_left} дн."


def view(row: sqlite3.Row, today: date | None = None) -> MeterView:
    return MeterView(row, today or date.today())


def _fmt(value: str | date | None) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        value = date.fromisoformat(value)
    return value.strftime("%d.%m.%Y")


def meters_text(conn: sqlite3.Connection, today: date | None = None) -> str:
    """Список общедомовых приборов со сроками поверки."""
    today = today or date.today()
    rows = repository.house_meters(conn)
    if not rows:
        return "Общедомовые приборы не заведены."

    lines = ["🔧 <b>Поверка общедомовых приборов</b>", ""]
    for row in rows:
        v = view(row, today)
        lines.append(f"{v.mark} <b>{row['name']}</b>")
        details = [f"поверен: {_fmt(row['last_verified'])}"]
        if v.next_due:
            details.append(f"следующая: {_fmt(v.next_due)} ({v.status_text})")
        else:
            details.append("внесите дату последней поверки")
        details.append(f"интервал: {row['interval_years']} г.")
        if row["serial"]:
            details.append(f"№ {row['serial']}")
        lines.append("    " + " · ".join(details))
    lines.append("")
    lines.append("Сроки пересчитываются автоматически после внесения поверки.")
    return "\n".join(lines)


def sync_verification_tasks(conn: sqlite3.Connection,
                            today: date | None = None) -> int:
    """Заводит задачи по приборам, у которых приближается срок поверки.

    Задача создаётся за VERIFICATION_LEAD_DAYS дней: окно выполнения — от этой
    даты до дня поверки, дальше она считается просроченной.
    """
    today = today or date.today()
    created = 0
    for row in repository.house_meters(conn):
        v = view(row, today)
        due = v.next_due
        if due is None:
            continue
        start = due - timedelta(days=VERIFICATION_LEAD_DAYS)
        if today < start:
            continue                       # ещё рано заводить задачу
        if repository.verification_task(conn, row["id"], due.isoformat()):
            continue                       # задача уже есть
        repository.create_task(
            conn, f"Поверка: {row['name']}",
            house_meter_id=row["id"],
            description=(f"Организовать поверку общедомового прибора. "
                         f"Срок — до {_fmt(due)}. Интервал "
                         f"{row['interval_years']} г."),
            category="verification", priority="high", status="new",
            start_date=start.isoformat(), due_date=due.isoformat(),
            period=due.strftime("%Y-%m"), source="verification")
        created += 1
    return created


def register_verification(conn: sqlite3.Connection, house_meter_id: int,
                          verified_at: date, document: str = "",
                          note: str = "") -> date:
    """Записывает проведённую поверку и пересчитывает следующий срок."""
    meter = repository.get_house_meter(conn, house_meter_id)
    following = add_years(verified_at, meter["interval_years"])
    repository.update_house_meter(conn, house_meter_id,
                                  last_verified=verified_at.isoformat())
    repository.add_verification(conn, house_meter_id, verified_at.isoformat(),
                                following.isoformat(), document, note)
    return following
