"""Разовая чистка: оставить в имени жителя только первое слово.

Раньше при регистрации бот просил ФИО, теперь спрашивает только имя.
Уже записанные фамилии и отчества системе не нужны — показания привязаны
к квартире, а имя служит лишь обращением. Этот скрипт приводит старые
записи к новому виду: «Иванова Мария Петровна» -> «Мария».

Порядок обратный обычному: сначала показывает, что изменится, и ничего
не трогает. Правит только с ключом --apply, и перед правкой сам делает
резервную копию базы — вернуть всё назад можно одной заменой файла.

    python -m scripts.shorten_names           # показать, что изменится
    python -m scripts.shorten_names --apply   # выполнить
"""
import argparse
import sys

from database import repository
from database.backup import make_backup

# Порядок слов в ФИО жители пишут по-разному: «Иванова Мария Петровна» и
# «Мария Иванова». Отчество узнаётся по окончанию — по нему и понимаем,
# где имя: если последнее слово отчество, имя стоит вторым.
PATRONYMIC_ENDINGS = ("вич", "вна", "чна", "ична")


def short_name(full_name: str) -> str:
    """Имя из записи любого вида. Пустую строку и одно слово не трогает."""
    parts = full_name.split()
    if len(parts) < 2:
        return full_name.strip()
    if parts[-1].lower().endswith(PATRONYMIC_ENDINGS):
        # «Иванова Мария Петровна» — имя посередине
        return parts[1] if len(parts) >= 3 else parts[0]
    # «Мария Иванова» — имя первое
    return parts[0]


def is_ambiguous(full_name: str) -> bool:
    """Два слова без отчества — где имя, а где фамилия, не разобрать.

    «Мария Иванова» и «Петров Пётр» выглядят одинаково, и угадать порядок
    нельзя. Берём первое слово, но помечаем такую строку в просмотре —
    председатель увидит и поправит, если бот угадал неверно.
    """
    parts = full_name.split()
    return (len(parts) == 2
            and not parts[-1].lower().endswith(PATRONYMIC_ENDINGS))


def planned_changes(conn) -> list[tuple[int, str, str, str, bool]]:
    """Что изменится: (id, квартира, было, станет, надо ли проверить глазами)."""
    changes = []
    for user in repository.list_users(conn):
        was = (user["full_name"] or "").strip()
        becomes = short_name(was)
        if was and becomes != was:
            changes.append((user["id"], user["apartment_number"] or "—",
                            was, becomes, is_ambiguous(was)))
    return changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="выполнить правку (без ключа — только показать)")
    args = parser.parse_args(argv)

    conn = repository.connect()
    try:
        changes = planned_changes(conn)
        if not changes:
            print("Менять нечего: у всех жителей записано одно слово.")
            return 0

        print(f"Записей к правке: {len(changes)}\n")
        for _, apartment, was, becomes, ambiguous in changes:
            mark = "  ← проверьте порядок слов" if ambiguous else ""
            print(f"  кв. {apartment}: «{was}» -> «{becomes}»{mark}")
        if any(ambiguous for *_, ambiguous in changes):
            print("\nПомеченные строки — из двух слов без отчества: где имя, "
                  "а где фамилия, не разобрать.\nБот берёт первое слово; "
                  "если ошибся, скажите — поправлю вручную.")

        if not args.apply:
            print("\nЭто только просмотр, база не изменена.")
            print("Чтобы выполнить: python -m scripts.shorten_names --apply")
            return 0

        backup = make_backup()
        print(f"\nРезервная копия базы: {backup}")
        for user_id, _, _, becomes, _ in changes:
            conn.execute("UPDATE users SET full_name = ? WHERE id = ?",
                         (becomes, user_id))
        conn.commit()
        print(f"Готово: исправлено записей — {len(changes)}.")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
