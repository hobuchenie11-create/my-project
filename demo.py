"""Демонстрация модуля «Сбор показаний» — для проверки результата.

Создаёт отдельную демо-базу (рабочая база не затрагивается), наполняет её
показательными данными и формирует все документы модуля.

Запуск:  python demo.py
Результат: папка reports/demo/ с тремя файлами Excel.
"""
import shutil
from pathlib import Path

from bot.config import config
from bot.services.parser import parse_message
from bot.services.reading_service import save_parsed_readings
from bot.texts import late_submission_text, welcome_residents_text
from database import repository
from database.init_db import init_db
from excel.import_registry import REGISTRY_PATH, import_registry
from excel.workbook import build_workbook
from reports.debtors_statement import build_debtors_statement

DEMO_DIR = config.base_dir / "reports" / "demo"
DEMO_DB = DEMO_DIR / "demo.db"
PERIOD = "2026-07"

# Кто и как передал показания: (сообщение, источник, после срока?)
DEMO_SUBMISSIONS = [
    ("Кв 1\nЭл.эн 15230\nХвс кухня 120\nХвс санузел 45\n"
     "Гвс кухня 60\nГвс ванна 30\nСумма гвс 90", "chat", False),
    ("Кв. 2\nЭл. энерг. 8204\nХвс 15\nГвс 22", "bot", False),
    ("Кв 7\nСв 20820\nХв 1048\nГВ 490", "chat", False),
    ("Кв, 5\nЭдектро, 12178\nХв,кух,36\nСан,уз,228\n"
     "Гв,кух,114\nВанная,178", "chat", False),
    ("Кв 8\nЭ/энер - 32992\nХвс кухня - 6\nХвс с/уз - 140\n"
     "Гвс кухня - 0000076\nГвс ванна - 57", "chat", True),      # после срока
    ("Кв 3\nЭл 9100\nХвс 33\nГвс 41", "whatsapp", False),        # через WhatsApp
]


def build_demo() -> None:
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    DEMO_DIR.mkdir(parents=True)

    init_db(DEMO_DB)
    conn = repository.connect(DEMO_DB)
    try:
        if REGISTRY_PATH.exists():
            import_registry(REGISTRY_PATH, conn=conn)

        # Часть жителей зарегистрирована в боте, часть — нет
        for tg_id, number, name, username in [
            (1001, "1", "Иванова Мария Петровна", "maria"),
            (1002, "2", "Петров Иван Иванович", "ivan_p"),
            (1003, "4", "Сидорова Анна Сергеевна", ""),
            (1004, "6", "Кузнецов Пётр Олегович", "pkuz"),
        ]:
            apt = repository.get_apartment_by_number(conn, number)
            repository.create_user(conn, tg_id, name, apt["id"], username=username)

        for text, source, late in DEMO_SUBMISSIONS:
            parsed = parse_message(text)
            apt = repository.get_apartment_by_number(conn, parsed.apartment_number)
            user = None
            save_parsed_readings(conn, apt, parsed, user, source=source,
                                 period=PERIOD, late=late)

        _print_summary(conn)

        # 1. Книга Excel (5 листов)
        book = DEMO_DIR / "1_Книга_DH_OS.xlsx"
        build_workbook(conn, book, PERIOD)

        # 2. Ведомость для ресурсоснабжающих организаций
        from bot.services.report_service import build_statement
        from excel.export import export_statement
        from bot.services.reading_service import period_title
        statement = build_statement(conn, PERIOD)
        vedomost = DEMO_DIR / "2_Ведомость_для_РСО.xlsx"
        export_statement(statement, period_title(PERIOD), vedomost)
    finally:
        conn.close()

    # 3. Ведомость непередавших
    debtors, count = build_debtors_statement(
        PERIOD, DEMO_DIR / "3_Ведомость_непередавших.xlsx", DEMO_DB)

    print()
    print("Готово. Откройте файлы из папки reports/demo/:")
    for path in sorted(DEMO_DIR.glob("*.xlsx")):
        print(f"   • {path.name}")
    print()
    print("=" * 70)
    print("ЧТО ПРОВЕРИТЬ В КАЖДОМ ФАЙЛЕ")
    print("=" * 70)
    print(_checklist(count))
    print("=" * 70)
    print("ТЕКСТЫ, КОТОРЫЕ ПОЛУЧАЮТ ЖИТЕЛИ")
    print("=" * 70)
    print("\n--- Памятка в общий чат (кнопка «📣 Памятка жителям») ---\n")
    print(_plain(welcome_residents_text("ваш_бот")))
    print("\n--- Ответ при передаче после срока сбора ---\n")
    print(_plain(late_submission_text()))


def _print_summary(conn) -> None:
    submitted = repository.apartments_submitted(conn, PERIOD)
    total = len(repository.list_apartments(conn))
    print(f"Демо-данные за {PERIOD}: передали {len(submitted)} из {total} помещений")


def _checklist(debtors_count: int) -> str:
    return f"""
1. Реестр квартир — файл 1, лист «Реестр квартир»
   (ведомость для ресурсников — первый лист той же книги и файл 2)
   • строка на каждую квартиру, 80 квартир + нежилые помещения
   • тип квартиры цветом: 🟩 1-комн · 🟦 2-комн · 🟪 3-комн
   • Telegram ID заполнен у зарегистрированных (кв. 1, 2, 4, 6)
   • статус цветом: 🟨 Передал · 🟥 Не передал · 🩶 Нет в Telegram
     (кв. 4 и 6 — зарегистрированы, но не передали: 🟥;
      кв. 3 передала через WhatsApp без регистрации: 🟨)
   • служебные столбцы (M–Q) серые и защищены от правки
   • закреплена шапка, включены автофильтры, статус — выпадающий список

2. Журнал показаний — файл 1, лист «Переданные показания»
   • каждая передача отдельной строкой: дата, время, квартира, показания
   • колонка «Источник»: Telegram (бот) · Telegram (чат) · WhatsApp

3. Текущие показания — файл 1, лист «Текущие показания»
   • последние значения по каждой квартире, период и время обновления

4. Ведомость для РСО — файл 2
   • квартиры строго по порядку 1 → 80, затем нежилые и общедомовой прибор
   • «ГВС сумма» считается автоматически (кухня + ванна)
   • у кв. 8 в «Примечании»: «Переданы после срока сбора показаний»
   • готова к печати: А4, вписана по ширине, шапка на каждой странице
     (проверить: Файл → Печать → предпросмотр)

5. Ведомость непередавших — файл 3 (должников: {debtors_count})
   • формируется автоматически 20 числа в 09:00 и приходит председателю
   • квартиры по порядку, серым — те, кто не зарегистрирован в Telegram
   • есть пустая графа «Отметка» для пометок от руки
   • тоже готова к печати

6. Панель председателя — файл 1, лист «Контроль передачи»
   • всего квартир / передали / не передали / процент передачи
   • зарегистрированы в Telegram, без регистрации, пользуются WhatsApp
   • значения — формулы, пересчитываются при правке реестра
   • легенда цветовой схемы DH OS
   В самом боте: 🛠 Меню председателя →
   📄 Ведомость передачи · 📗 Книга Excel · 📕 Ведомость непередавших ·
   📈 Статистика · 🔴 Должники · 🔔 Напомнить · 📣 Памятка жителям

7. Регламент сбора (15–19 число)
   • 15, 17, 19 — напоминания жителям
   • 20 в 09:00 — ведомость непередавших председателю
   • 20 в 10:00 — ведомость со всеми собранными показаниями
   • с 20 по 30 — показания принимаются с пометкой, житель получает
     сообщение об учёте в следующем расчётном периоде (текст ниже)
"""


def _plain(text: str) -> str:
    for tag in ("<b>", "</b>", "<code>", "</code>", "<i>", "</i>"):
        text = text.replace(tag, "")
    return text


if __name__ == "__main__":
    build_demo()
