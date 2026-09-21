"""Автоматические напоминания о передаче показаний (Этап 7).

Числа месяца и час задаются в .env (REMINDER_DAYS, REMINDER_HOUR).
Напоминание получают только зарегистрированные у Домоведа жители тех
квартир, что ещё не сдали показания за текущий период: как только квартира
передала показания, напоминания для неё прекращаются.
"""
import sqlite3
from dataclasses import dataclass
from datetime import date

from bot.config import config
from bot.services.reading_service import current_period, period_title
from bot.texts import collection_window
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


# После 20 числа прежний текст обманывает: он зовёт успеть к сроку, которого
# уже нет. Тем, кто не передал, важно другое — что сделать сейчас, чтобы
# показания всё-таки попали в текущий расчёт.
LATE_REMINDER_TEXT = (
    "Здравствуйте! Показания за {period} уже переданы ресурсоснабжающим "
    "организациям — ведомость по дому сформирована {statement_day} числа.\n\n"
    "Если вы ещё не передали свои, пришлите их сейчас: бот примет, но "
    "в расчёт они попадут <b>в следующем месяце</b>.\n\n"
    "💡 Чтобы показания учли в текущем расчёте, передайте их напрямую "
    "ресурсоснабжающей организации — там принимают <b>до 25 числа</b>:\n"
    "• при оплате квитанции;\n"
    "• через личный кабинет на сайте.\n\n"
    "В следующем месяце передайте, пожалуйста, {window} — так показания "
    "попадут в ведомость дома без хлопот. Спасибо!"
)


def deadline_text() -> str:
    """«20 числа, 12:00» — последний срок для ведомости этого месяца."""
    return (f"{config.readings_day_end} числа, "
            f"{config.readings_deadline_hour}:00")


def reminder_text(period: str, today: date | None = None) -> str:
    """Текст напоминания: до срока — зовём передать, после — объясняем, как быть.

    Дни напоминаний идут и после 20 числа (23 и 25): показания к тому времени
    уже ушли ресурсникам, и звать «успеть до 20 числа» поздно и неправдиво.
    """
    today = today or date.today()
    if today.day <= config.statement_day:
        return REMINDER_TEXT.format(period=period_title(period),
                                    deadline=deadline_text())
    return LATE_REMINDER_TEXT.format(
        period=period_title(period), statement_day=config.statement_day,
        window=collection_window())


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
