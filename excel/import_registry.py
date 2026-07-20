"""Загрузка реестра квартир из data/apartments.xlsx.

Формат файла (первая строка — заголовки):
    Номер | Тип | Комнат | Примечание

Тип:    «жилое» или «нежилое» (по умолчанию — жилое).
Комнат: число комнат. 1-2 → один ХВС и один ГВС (compact);
        3 и больше → раздельный учет ХВС/ГВС по кухне и санузлу (full).
        Можно вместо числа написать «compact»/«full» напрямую.

Создать шаблон файла:      python -m excel.import_registry --template
Импортировать реестр в БД: python -m excel.import_registry
"""
import sys
from pathlib import Path

from openpyxl import Workbook, load_workbook

from bot.config import config
from database import repository
from database.models import LAYOUT_METERS, NONRESIDENTIAL_METERS

REGISTRY_PATH = config.data_dir / "apartments.xlsx"


def _layout_from_cell(value) -> str:
    text = str(value or "").strip().lower()
    if text in ("compact", "full"):
        return text
    digits = "".join(c for c in text if c.isdigit())
    if digits and int(digits) <= 2:
        return "compact"
    return "full"


def generate_template(path: Path = REGISTRY_PATH) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Реестр"
    ws.append(["Номер", "Тип", "Комнат", "Примечание"])
    for i in range(1, config.apartments_count + 1):
        ws.append([str(i), "жилое", 3, ""])
    for i in range(1, config.nonresidential_count + 1):
        ws.append([f"Нежилое помещение №{i}", "нежилое", "", ""])
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
            rooms = row[2] if len(row) > 2 else None
            note = str(row[3] or "").strip() if len(row) > 3 else ""

            if type_raw.startswith("нежил"):
                type_, layout, kinds = "nonresidential", "compact", NONRESIDENTIAL_METERS
            else:
                type_ = "residential"
                layout = _layout_from_cell(rooms)
                kinds = LAYOUT_METERS[layout]

            apt_id = repository.upsert_apartment(conn, number, type_, order, note, layout)
            repository.set_meters(conn, apt_id, kinds)
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
