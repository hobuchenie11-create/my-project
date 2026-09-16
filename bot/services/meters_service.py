"""Набор счётчиков квартиры: посмотреть и поправить.

Сколько в квартире счётчиков воды, известно из справочника
data/apartments.xlsx. Но жизнь идёт: житель ставит второй счётчик, в
справочнике была описка, квартиру объединили. Пока это правилось только
заменой файла и перезапуском бота.

А расхождение видно сразу и стоит дорого: житель прислал «Хв.кух.37» и
«Сан.узел.229», а в реестре у него один ХВС — бот отвечает, что не знает,
какое из двух записать, и показания не попадают в ведомость. Со стороны
это выглядит как «бот прочитал не все показания».
"""
import sqlite3

from database import repository
from database.models import METER_KINDS, apartment_meters, layout_label

# Варианты, которые встречаются в доме, и других нет: либо два счётчика
# воды на квартиру, либо четыре — в трёхкомнатных, где кухня и санузел
# разведены. Смешанные наборы (2 ХВС + 1 ГВС) в списке только путали бы.
# Ключ уходит в callback_data кнопки.
LAYOUTS = {
    "1-1": (1, 1),
    "2-2": (2, 2),
}


def layout_of(conn: sqlite3.Connection, apartment_id: int) -> tuple[int, int]:
    """Сколько сейчас счётчиков ХВС и ГВС числится за квартирой."""
    kinds = {m["kind"] for m in repository.meters_for_apartment(conn, apartment_id)}
    cws = 2 if {"cws_kitchen", "cws_bathroom"} & kinds else 1
    hws = 2 if {"hws_kitchen", "hws_bathroom"} & kinds else 1
    return cws, hws


def describe(conn: sqlite3.Connection, apartment: sqlite3.Row) -> str:
    """Текущий набор приборов квартиры — списком, как его видит бот."""
    meters = repository.meters_for_apartment(conn, apartment["id"])
    names = [METER_KINDS.get(m["kind"], m["kind"]) for m in meters]
    cws, hws = layout_of(conn, apartment["id"])
    return (f"🔧 <b>{_display(apartment)}</b>\n"
            f"Сейчас в реестре: {layout_label(cws, hws)}\n\n"
            + "\n".join(f"• {name}" for name in names))


def apply_layout(conn: sqlite3.Connection, apartment_id: int,
                 cws: int, hws: int) -> list[str]:
    """Переводит квартиру на другой набор приборов. Показания сохраняются.

    Прежние счётчики не удаляются, а помечаются неактивными: история
    показаний по ним остаётся в базе и в ведомостях за прошлые месяцы.
    """
    kinds = apartment_meters(cws, hws)
    repository.set_meters(conn, apartment_id, kinds)
    repository.update_apartment_layout(conn, apartment_id, layout_label(cws, hws))
    conn.commit()
    return kinds


def _display(apartment: sqlite3.Row) -> str:
    if apartment["type"] == "residential":
        return f"кв. {apartment['number']}"
    return apartment["number"]
