"""Бумажные бланки для передачи показаний.

Бланки не привязаны к месяцу: период житель вписывает сам, поэтому их можно
напечатать пачкой вперёд и раздать.

Из кода:  generate_blank_forms()  ->  путь к .xlsx
Вручную:  python -m reports.blank_forms [номера квартир через запятую]
"""
import sys
from pathlib import Path

from bot.config import config
from database import repository
from excel.blanks import generate_blanks


def generate_blank_forms(numbers: list[str] | None = None) -> Path:
    conn = repository.connect()
    try:
        suffix = "_vybor" if numbers else ""
        out_path = config.reports_dir / f"blanki{suffix}.xlsx"
        generate_blanks(conn, out_path, numbers=numbers)
    finally:
        conn.close()
    return out_path


if __name__ == "__main__":
    numbers_arg = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    print(f"Бланки сохранены: {generate_blank_forms(numbers_arg)}")
