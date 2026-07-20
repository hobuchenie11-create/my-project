"""Загрузка реестра квартир из data/apartments.xlsx.

Формат файла (первая строка — заголовки):
    Номер | Тип | Примечание
Тип: «жилое» или «нежилое» (по умолчанию — жилое).

Создать шаблон файла:      python -m excel.import_registry --template
Импортировать реестр в БД: python -m excel.import_registry
"""
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook

from bot.config import config
from database import repository
from database.models import NONRESIDENTIAL_METERS, RESIDENTIAL_METERS

REGISTRY_PATH = config.data_dir / "apartments.xlsx"


def generate_template(path: Path = REGISTRY_PATH) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Реестр"
    ws.append(["Номер", "Тип", "Примечание"])
    for i in range(1, config.apartments_count + 1):
        ws.append([str(i), "жилое", ""])
    for i in range(1, config.nonresidential_count + 1):
        ws.append([f"Нежилое помещение №{i}", "нежилое", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


def import_registry(path: Path = REGISTRY_PATH) -> int:
    wb = load_workbook(path, read_only=True)
    ws = wb.active
    conn = repository.connect()
    count = 0
    try:
        repository.create_schema(conn)
        for order, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=1):
            if not row or row[0] is None:
                continue
            number = str(row[0]).strip()
            type_raw = str(row[1] or "жилое").strip().lower()
            note = str(row[2] or "").strip()
            type_ = "nonresidential" if type_raw.startswith("нежил") else "residential"
            apt_id = repository.upsert_apartment(conn, number, type_, order, note)
            kinds = RESIDENTIAL_METERS if type_ == "residential" else NONRESIDENTIAL_METERS
            for kind in kinds:
                repository.ensure_meter(conn, apt_id, kind)
            count += 1
        conn.commit()
    finally:
        conn.close()
    return count


if __name__ == "__main__":
    if "--template" in sys.argv:
        print(f"Шаблон реестра создан: {generate_template()}")
    else:
        print(f"Импортировано помещений: {import_registry()}")
