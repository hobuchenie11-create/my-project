"""Готовая форма под сфотографированный бумажный бланк.

Цифры с фотографии бот не распознаёт — рукописные показания читаются
ненадёжно, а ошибка в одной цифре уходит в ведомость и в реестр ОЭК и
находится только через месяц. Поэтому работа устроена как полуавтомат:
бот готовит форму по конкретной квартире — её приборы и прошлые
показания, — председатель переписывает цифры с бланка, а проверку
расхода бот берёт на себя (см. services/validation.check_reading).

Прошлые показания в форме нужны не для красоты: по ним сразу видно,
что 267 после 250 — правдоподобно, а 67 — описка.
"""
import sqlite3

from database import repository
from database.models import METER_KINDS

# Подписи приборов так, как их пишут в сообщениях: форму сразу можно
# заполнить и отправить, ничего не переписывая по-своему
FORM_LABELS = {
    "electricity": "Эл.эн",
    "cws": "Хвс",
    "hws": "Гвс",
    "cws_kitchen": "Хвс кухня",
    "cws_bathroom": "Хвс санузел",
    "hws_kitchen": "Гвс кухня",
    "hws_bathroom": "Гвс санузел",
}


def display(apartment: sqlite3.Row) -> str:
    if apartment["type"] == "residential":
        return f"кв. {apartment['number']}"
    return apartment["number"]


def previous_values(conn: sqlite3.Connection,
                    apartment: sqlite3.Row) -> dict[str, float]:
    """Последние принятые показания по каждому прибору квартиры."""
    values = {}
    for meter in repository.meters_for_apartment(conn, apartment["id"]):
        last = repository.last_reading(conn, meter["id"])
        if last is not None:
            values[meter["kind"]] = last["value"]
    return values


def form_text(conn: sqlite3.Connection, apartment: sqlite3.Row) -> str:
    """Форма под бланк: что переписать и с чем сверить."""
    meters = repository.meters_for_apartment(conn, apartment["id"])
    if not meters:
        return (f"У {display(apartment)} в реестре нет приборов. "
                "Поправьте набор счётчиков и повторите.")

    previous = previous_values(conn, apartment)
    number = (f"Кв. {apartment['number']}" if apartment["type"] == "residential"
              else apartment["number"])

    form = "\n".join([number] + [FORM_LABELS.get(m["kind"], METER_KINDS[m["kind"]])
                                 for m in meters])

    text = (f"🖨 <b>Бланк · {display(apartment)}</b>\n\n"
            "Перепишите цифры с бланка в эту форму и отправьте одним "
            "сообщением — нажмите на неё, чтобы скопировать:\n\n"
            f"<code>{form}</code>")

    if previous:
        was = " · ".join(
            f"{FORM_LABELS.get(m['kind'], METER_KINDS[m['kind']])} "
            f"{previous[m['kind']]:g}"
            for m in meters if m["kind"] in previous)
        text += (f"\n\n<b>Прошлые показания:</b> {was}\n"
                 "Новые должны быть не меньше. Если расход выйдет необычным, "
                 "бот предупредит.")
    else:
        text += ("\n\nПрошлых показаний по этой квартире нет — сверять не с чем, "
                 "поэтому цифры проверьте внимательно.")
    return text


def history_text(conn: sqlite3.Connection, apartment: sqlite3.Row,
                 months: int = 4) -> str:
    """Карточка помещения: приборы и показания по месяцам.

    Нужна, когда бот отвечает «показание меньше предыдущего». Решить, чья
    цифра неверна — сегодняшняя с бланка или прошлая в базе, — можно только
    увидев обе. Отдельно видно и расход: если в прошлом месяце кухню и
    санузел записали местами, в таблице это бросается в глаза.
    """
    meters = repository.meters_for_apartment(conn, apartment["id"])
    if not meters:
        return f"У {display(apartment)} в реестре нет приборов."

    rows = repository.readings_history_for_apartment(conn, apartment["id"],
                                                     limit=200)
    # period -> kind -> значение. Записи идут от новых к старым, поэтому
    # первая встреченная по паре и есть действующая (правки лежат сверху)
    by_period: dict[str, dict[str, float]] = {}
    for row in rows:
        by_period.setdefault(row["period"], {}).setdefault(row["kind"],
                                                           row["value"])

    periods = sorted(by_period, reverse=True)[:months]
    if not periods:
        return (f"📋 <b>{display(apartment)}</b>\n\n"
                "Показаний по этому помещению ещё не было.")

    lines = [f"📋 <b>{display(apartment)}</b>", ""]
    for meter in meters:
        kind = meter["kind"]
        label = FORM_LABELS.get(kind, METER_KINDS[kind])
        parts = []
        for period in periods:
            value = by_period[period].get(kind)
            month = f"{period[5:7]}.{period[:4]}"
            parts.append(f"{month} — {value:g}" if value is not None
                         else f"{month} — нет")
        lines.append(f"<b>{label}</b>: " + " · ".join(parts))

    lines.append("")
    lines.append("Чтобы переписать принятую цифру, пришлите показание заново "
                 "со словом «Исправить» первой строкой.")
    return "\n".join(lines)
