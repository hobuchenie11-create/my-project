"""Создание схемы БД и первичное заполнение реестра квартир.

Запускается автоматически при старте бота, можно запустить и вручную:
    python -m database.init_db
"""
import sqlite3
from pathlib import Path

from bot.config import config
from database import repository
from database.models import NONRESIDENTIAL_METERS, RESIDENTIAL_METERS


def init_db(db_path: Path | str | None = None,
            apartments_count: int | None = None,
            nonresidential_count: int | None = None) -> None:
    apartments_count = apartments_count or config.apartments_count
    nonresidential_count = (nonresidential_count
                            if nonresidential_count is not None
                            else config.nonresidential_count)

    conn = repository.connect(db_path)
    try:
        repository.create_schema(conn)
        _seed_apartments(conn, apartments_count, nonresidential_count)
        conn.commit()
    finally:
        conn.close()


def _seed_apartments(conn: sqlite3.Connection, apartments_count: int,
                     nonresidential_count: int) -> None:
    for i in range(1, apartments_count + 1):
        apt_id = repository.upsert_apartment(conn, str(i), "residential", i)
        for kind in RESIDENTIAL_METERS:
            repository.ensure_meter(conn, apt_id, kind)

    for i in range(1, nonresidential_count + 1):
        number = f"Нежилое помещение №{i}"
        apt_id = repository.upsert_apartment(conn, number, "nonresidential",
                                             apartments_count + i)
        for kind in NONRESIDENTIAL_METERS:
            repository.ensure_meter(conn, apt_id, kind)


if __name__ == "__main__":
    init_db()
    print(f"База данных готова: {config.db_path}")
