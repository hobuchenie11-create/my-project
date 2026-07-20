"""Формирование месячной ведомости в Excel.

Из кода:  generate_statement(period)  ->  путь к .xlsx
Вручную:  python -m reports.monthly_statement [ГГГГ-ММ]
"""
import sys
from pathlib import Path

from bot.config import config
from bot.services.reading_service import current_period, period_title
from bot.services.report_service import build_statement
from database import repository
from excel.export import export_statement


def generate_statement(period: str | None = None) -> Path:
    period = period or current_period()
    conn = repository.connect()
    try:
        statement = build_statement(conn, period)
        out_path = config.reports_dir / f"vedomost_{period}.xlsx"
        export_statement(statement, period_title(period), out_path)
        repository.save_report(conn, period, str(out_path))
    finally:
        conn.close()
    return out_path


if __name__ == "__main__":
    period_arg = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"Ведомость сохранена: {generate_statement(period_arg)}")
