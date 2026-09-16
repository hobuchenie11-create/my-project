"""Починка данных, записанных со сбоем в прежних версиях.

Запускается при каждом старте бота — сразу после создания схемы. Всё
здесь обязано быть безопасным при повторном запуске: чинится только то,
что действительно испорчено, а исправное не трогается.

Пока причина одна: дата, введённая как «30.09.26», разбиралась как 30
сентября 26 года. В плане это выглядело как «просрочено на 730471 дн.».
Разбор даты исправлен (bot/utils/dates.py), но записанные строки надо
привести в порядок — иначе задачи так и останутся висеть просроченными.
"""
import logging
import sqlite3

from bot.utils.dates import looks_broken, repair_year

logger = logging.getLogger(__name__)

# Где лежат даты, которые вводит человек. Столбцы с датой, которую
# проставляет сам бот (created_at, done_at), сюда не входят: испортить
# их вводом нельзя.
DATE_COLUMNS = (
    ("tasks", "due_date"),
    ("tasks", "start_date"),
    ("tasks", "paid_at"),
    ("tasks", "utility_paid_at"),
    ("house_meters", "last_verified"),
    ("verifications", "verified_at"),
    ("verifications", "next_due"),
)


def repair_broken_years(conn: sqlite3.Connection) -> int:
    """Исправляет даты вида «0026-09-30» на «2026-09-30». Возвращает счёт."""
    fixed = 0
    for table, column in DATE_COLUMNS:
        try:
            rows = conn.execute(
                f"SELECT id, {column} AS value FROM {table} "
                f"WHERE {column} != '' AND {column} < '1000-01-01'").fetchall()
        except sqlite3.OperationalError:      # таблицы ещё нет — чинить нечего
            continue

        for row in rows:
            if not looks_broken(row["value"]):
                continue
            conn.execute(f"UPDATE {table} SET {column} = ? WHERE id = ?",
                         (repair_year(row["value"]), row["id"]))
            fixed += 1
            logger.info("Исправлен год: %s.%s #%s — %s -> %s", table, column,
                        row["id"], row["value"], repair_year(row["value"]))

    if fixed:
        # period у задачи — «YYYY-MM» из срока, его тоже надо подтянуть
        conn.execute("UPDATE tasks SET period = substr(due_date, 1, 7) "
                     "WHERE due_date != '' AND period < '1000-01'")
        conn.commit()
        logger.info("Починено дат с неверным годом: %s", fixed)
    return fixed
