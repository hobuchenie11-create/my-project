"""Автоматические напоминания о передаче показаний (Этап 7).

Числа месяца и час задаются в .env (REMINDER_DAYS, REMINDER_HOUR).
Напоминание получают только зарегистрированные у Домоведа жители тех
квартир, что ещё не сдали показания за текущий период: как только квартира
передала показания, напоминания для неё прекращаются.
"""
import sqlite3
from dataclasses import dataclass

from bot.config import config
from bot.services.reading_service import current_period
from database import repository


@dataclass
class ReminderTarget:
    tg_id: int
    apartment_number: str
    full_name: str


# Текст напоминания задан председателем. Довод про ОДН здесь главный:
# непереданные показания раскидываются на весь дом, и жителю важно знать,
# что это стоит денег лично ему.
REMINDER_TEXT = (
    "Здравствуйте! Напоминаю, что пора передать показания приборов учёта "
    "за {period}.\n\n"
    "Своевременная передача показаний минимизирует начисления по ОДН.\n\n"
    "Передать можно прямо здесь — кнопка «🏠 Передать показания» — "
    "или сообщением в чате дома.\n\n"
    "Заранее благодарю всех, кто успевает до {deadline}: именно по этим "
    "показаниям составляется ведомость дома."
)


def deadline_text() -> str:
    """«20 числа, 13:00» — последний срок для ведомости этого месяца."""
    return (f"{config.statement_day} числа, "
            f"{config.readings_deadline_hour}:00")


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
