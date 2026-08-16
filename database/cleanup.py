"""Удаление тестовых показаний из базы.

При запуске системы показания вводили наугад, чтобы проверить бота. Теперь
они мешают: бот считает их предыдущими, ругается на «необычно большой расход»
и отклоняет настоящие показания как «меньше предыдущего».

Команда сначала показывает, что именно будет удалено, и ничего не трогает,
пока не указан `--yes`. Перед удалением делается резервная копия базы.

Примеры:
    python -m database.cleanup                          # что вообще есть в базе
    python -m database.cleanup --before 15.08.2026      # что удалится (пробный прогон)
    python -m database.cleanup --before 15.08.2026 --yes  # удалить
    python -m database.cleanup --apartment 1 --yes      # всё по квартире 1
    python -m database.cleanup --period 2026-07 --yes   # всё за июль
"""
import argparse
from datetime import datetime

from database import repository
from database.backup import make_backup
from database.models import METER_KINDS


def _parse_date(text: str) -> str:
    """«15.08.2026» или «2026-08-15» -> «2026-08-15 00:00:00» для сравнения."""
    value = text.strip().replace("/", ".")
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d 00:00:00")
        except ValueError:
            continue
    raise SystemExit(f"Не понял дату «{text}». Пример: 15.08.2026")


def describe(rows) -> str:
    """Список показаний по квартирам — чтобы видеть, что удаляем."""
    if not rows:
        return "Под фильтр ничего не попало."

    by_apartment: dict[str, list] = {}
    for row in rows:
        by_apartment.setdefault(row["apartment_number"], []).append(row)

    lines = []
    for number, items in by_apartment.items():
        lines.append(f"\nКв. {number} ({len(items)}):")
        for row in items:
            kind = METER_KINDS.get(row["kind"], row["kind"])
            lines.append(f"   {row['created_at'][:16]}  {kind:<15} "
                         f"{row['value']:>10g}  ({row['period']}, {row['source']})")
    lines.append(f"\nВсего показаний: {len(rows)} "
                 f"по {len(by_apartment)} помещениям.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Удаление тестовых показаний из базы DH OS")
    parser.add_argument("--before", default="",
                        help="удалить показания, внесённые ДО этой даты "
                             "(например 15.08.2026)")
    parser.add_argument("--period", default="",
                        help="только за расчётный период, например 2026-07")
    parser.add_argument("--apartment", default="",
                        help="только по одной квартире, например 1")
    parser.add_argument("--source", default="",
                        help="только из одного источника: bot, chat, admin")
    parser.add_argument("--yes", action="store_true",
                        help="выполнить удаление (без него — пробный прогон)")
    args = parser.parse_args()

    before = _parse_date(args.before) if args.before else ""
    filters = any([before, args.period, args.apartment, args.source])

    conn = repository.connect()
    try:
        rows = repository.find_readings(conn, before=before, period=args.period,
                                        apartment=args.apartment,
                                        source=args.source)
        if not filters:
            print("Показания в базе (фильтры не заданы — ничего не удаляется):")
            print(describe(rows))
            print("\nЧтобы удалить тестовые, укажите фильтр, например:")
            print("   python -m database.cleanup --before 15.08.2026")
            return

        print("Под удаление попадают:")
        print(describe(rows))
        if not rows:
            return

        if not args.yes:
            print("\nЭто пробный прогон — ничего не удалено.")
            print("Если список верный, повторите команду с --yes")
            return

        backup = make_backup()
        print(f"\nРезервная копия базы: {backup}")
        removed = repository.delete_readings(conn, [r["id"] for r in rows])
        repository.log_event(conn, None, "cleanup",
                             f"удалено показаний: {removed}")
        print(f"Удалено показаний: {removed}")
        print("Теперь бот считает предыдущими только оставшиеся показания.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
