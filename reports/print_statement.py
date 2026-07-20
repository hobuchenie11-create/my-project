"""Текстовая (печатная) версия ведомости для быстрого просмотра в консоли.

Запуск: python -m reports.print_statement [ГГГГ-ММ]
"""
import sys

from bot.services.reading_service import current_period, period_title
from bot.services.report_service import STATEMENT_COLUMNS, build_statement
from database import repository


def print_statement(period: str | None = None) -> None:
    period = period or current_period()
    conn = repository.connect()
    try:
        statement = build_statement(conn, period)
    finally:
        conn.close()

    print(f"Ведомость передачи показаний за {period_title(period)}\n")
    rows = [STATEMENT_COLUMNS] + [
        [str(c) for c in row.as_cells()] for row in statement.rows
    ]
    widths = [max(len(r[i]) for r in rows) for i in range(len(STATEMENT_COLUMNS))]
    for r in rows:
        print(" | ".join(c.ljust(w) for c, w in zip(r, widths)))
    print(f"\nСдали показания: {statement.submitted_count} из {statement.total_count}")


if __name__ == "__main__":
    print_statement(sys.argv[1] if len(sys.argv) > 1 else None)
