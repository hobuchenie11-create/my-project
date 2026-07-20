"""Сохранение и просмотр показаний."""
import sqlite3
from datetime import date

from bot.services.validation import CheckResult, check_reading
from database import repository
from database.models import DEFAULT_UNIT, METER_KINDS, METER_UNITS


def current_period(today: date | None = None) -> str:
    today = today or date.today()
    return f"{today.year:04d}-{today.month:02d}"


def period_title(period: str) -> str:
    months = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль",
              "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    year, month = period.split("-")
    return f"{months[int(month) - 1]} {year}"


def unit_for(kind: str) -> str:
    return METER_UNITS.get(kind, DEFAULT_UNIT)


def save_reading(conn: sqlite3.Connection, apartment_id: int, kind: str, value: float,
                 user_id: int | None, source: str = "bot",
                 period: str | None = None) -> CheckResult:
    """Проверяет и сохраняет одно показание. Возвращает результат проверки."""
    meter = repository.get_meter(conn, apartment_id, kind)
    if meter is None:
        return CheckResult(ok=False, error=f"У помещения нет прибора «{METER_KINDS[kind]}»")

    last = repository.last_reading(conn, meter["id"])
    result = check_reading(kind, value, last["value"] if last else None)
    if result.ok:
        repository.add_reading(conn, meter["id"], user_id,
                               period or current_period(), value, source)
    return result


def last_reading_value(conn: sqlite3.Connection, apartment_id: int, kind: str) -> float | None:
    meter = repository.get_meter(conn, apartment_id, kind)
    if meter is None:
        return None
    last = repository.last_reading(conn, meter["id"])
    return last["value"] if last else None


def my_last_readings_text(conn: sqlite3.Connection, apartment_id: int) -> str:
    lines = ["📄 Последние показания:", ""]
    found = False
    for meter in repository.meters_for_apartment(conn, apartment_id):
        last = repository.last_reading(conn, meter["id"])
        if last:
            found = True
            lines.append(f"{METER_KINDS[meter['kind']]}: {last['value']:g} "
                         f"{unit_for(meter['kind'])} (за {last['period']})")
        else:
            lines.append(f"{METER_KINDS[meter['kind']]}: показаний еще нет")
    if not found:
        return "Показания еще не передавались."
    return "\n".join(lines)


def history_text(conn: sqlite3.Connection, apartment_id: int) -> str:
    rows = repository.readings_history_for_apartment(conn, apartment_id)
    if not rows:
        return "История пуста — показания еще не передавались."
    lines = ["📊 История передач (последние записи):", ""]
    for row in rows:
        lines.append(f"{row['created_at'][:16]} · {row['period']} · "
                     f"{METER_KINDS[row['kind']]}: {row['value']:g}")
    return "\n".join(lines)
