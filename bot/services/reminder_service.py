"""Автоматические напоминания о передаче показаний (Этап 7).

Схема напоминаний по числам месяца задается в .env (REMINDER_DAYS,
по умолчанию 17, 23, 25). Напоминание получают только зарегистрированные
жители тех квартир, что еще не сдали показания за текущий период. Как только
квартира передала показания — напоминания для нее прекращаются.
"""
import sqlite3
from dataclasses import dataclass

from bot.services.reading_service import current_period
from database import repository


@dataclass
class ReminderTarget:
    tg_id: int
    apartment_number: str
    full_name: str


REMINDER_TEXT = (
    "🔔 Напоминание: пора передать показания приборов учета за {period}.\n\n"
    "Отправьте их в общий чат по шаблону или через бота (кнопка "
    "«🏠 Передать показания»). Спасибо!"
)


def pending_targets(conn: sqlite3.Connection, period: str | None = None) -> list[ReminderTarget]:
    """Кому отправить напоминание: зарегистрированные жители-должники."""
    period = period or current_period()
    targets = []
    for row in repository.debtors(conn, period):
        if row["tg_id"] is not None:
            targets.append(ReminderTarget(row["tg_id"], row["number"], row["full_name"]))
    return targets


def debtors_text(conn: sqlite3.Connection, period: str, period_name: str) -> str:
    """Список должников по передаче показаний для председателя (Этап 6)."""
    rows = repository.debtors(conn, period)
    if not rows:
        return f"✅ За {period_name} показания сдали все квартиры."
    lines = [f"🔴 Не сдали показания за {period_name} ({len(rows)}):", ""]
    for row in rows:
        who = row["full_name"] if row["tg_id"] else "не зарегистрирован в боте"
        lines.append(f"кв. {row['number']} — {who}")
    return "\n".join(lines)
