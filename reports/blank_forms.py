"""Бумажные бланки для передачи показаний.

Из кода:  generate_blank_forms()  ->  путь к .xlsx
Вручную:  python -m reports.blank_forms [ГГГГ-ММ] [номера квартир через запятую]
"""
import sys
from pathlib import Path

from bot.config import config
from bot.services.reading_service import current_period, period_title
from database import repository
from excel.blanks import generate_blanks


def generate_blank_forms(period: str | None = None,
                         numbers: list[str] | None = None) -> Path:
    period = period or current_period()
    conn = repository.connect()
    try:
        suffix = "_vybor" if numbers else ""
        out_path = config.reports_dir / f"blanki_{period}{suffix}.xlsx"
        generate_blanks(conn, out_path, period_title(period), numbers=numbers)
    finally:
        conn.close()
    return out_path


if __name__ == "__main__":
    period_arg = sys.argv[1] if len(sys.argv) > 1 else None
    numbers_arg = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    print(f"Бланки сохранены: {generate_blank_forms(period_arg, numbers_arg)}")
