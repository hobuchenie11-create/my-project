"""Создание схемы БД и первичное заполнение реестра квартир.

Запускается автоматически при старте бота, можно запустить и вручную:
    python -m database.init_db

Здесь создается базовый реестр из одинаковых квартир (по одному счетчику
ХВС и ГВС). Реальные данные по количеству счетчиков применяются отдельно —
импортом справочника data/apartments.xlsx (см. excel/import_registry.py),
который бот выполняет при старте, если файл есть.
"""
import sqlite3
from pathlib import Path

from bot.config import config
from database import repository
from database.models import (DEFAULT_CWS_COUNT, DEFAULT_HWS_COUNT,
                             NONRESIDENTIAL_METERS, apartment_meters, layout_label)


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
        _seed_residential(conn, apartments_count)
        _seed_nonresidential(conn, apartments_count, nonresidential_count)
        conn.commit()
    finally:
        conn.close()


def _seed_residential(conn: sqlite3.Connection, apartments_count: int) -> None:
    default_meters = apartment_meters(DEFAULT_CWS_COUNT, DEFAULT_HWS_COUNT)
    default_label = layout_label(DEFAULT_CWS_COUNT, DEFAULT_HWS_COUNT)
    for i in range(1, apartments_count + 1):
        apt_id = repository.upsert_apartment(conn, str(i), "residential", i,
                                             layout=default_label)
        repository.set_meters(conn, apt_id, default_meters)


def _seed_nonresidential(conn: sqlite3.Connection, apartments_count: int,
                         nonresidential_count: int) -> None:
    for i in range(1, nonresidential_count + 1):
        number = f"Нежилое помещение №{i}"
        apt_id = repository.upsert_apartment(conn, number, "nonresidential",
                                             apartments_count + i, layout="нежилое")
        repository.set_meters(conn, apt_id, NONRESIDENTIAL_METERS)


if __name__ == "__main__":
    init_db()
    print(f"База данных готова: {config.db_path}")
