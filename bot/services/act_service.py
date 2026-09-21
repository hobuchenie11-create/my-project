"""Акты поверки квартирных приборов учёта: список для письма ресурснику.

Ресурснику нужен не ворох фотографий, а перечень квартир: по каким именно
сведения о поверке не дошли до базы начислений. Этот перечень идёт
приложением к письму, поэтому собирается ровно в том виде, в каком его
можно вставить в документ.
"""
import sqlite3

from database import repository

# Что житель выбирает кнопкой. Ключ уходит в callback_data, значение —
# в список для письма
ACT_KINDS = {
    "hws": "ГВС",
    "cws": "ХВС",
    "power": "электроэнергия",
    "all": "все приборы",
}


def kind_title(code: str) -> str:
    return ACT_KINDS.get(code, code)


def acts_text(conn: sqlite3.Connection) -> str:
    """Сводка для председателя: от кого акты уже есть."""
    rows = repository.meter_acts(conn)
    if not rows:
        return (
            "📄 <b>Акты поверки</b>\n\n"
            "Пока ни одного акта не прислали.\n\n"
            "Житель отправляет акт кнопкой «📄 Передать акт поверки» в меню: "
            "выбирает квартиру и прибор, присылает фото или файл. Документ "
            "придёт вам сюда, а квартира попадёт в этот список — из него "
            "собирается приложение к письму ресурсоснабжающей организации."
        )

    lines = [f"📄 <b>Акты поверки ({len(rows)})</b>", ""]
    for row in rows:
        kind = f" — {row['kind']}" if row["kind"] else ""
        lines.append(f"• кв. {row['apartment_number']}{kind}"
                     f" <i>({row['created_at'][:10]})</i>")
    lines.append("")
    lines.append("<b>Для приложения к письму:</b>")
    lines.append(f"<code>{flats_line(conn)}</code>")
    return "\n".join(lines)


def flats_line(conn: sqlite3.Connection) -> str:
    """«кв. 5, 12, 43» — строка для приложения к письму, без повторов."""
    numbers = []
    for row in repository.meter_acts(conn):
        number = row["apartment_number"]
        if number not in numbers:
            numbers.append(number)
    return "кв. " + ", ".join(numbers) if numbers else "—"
