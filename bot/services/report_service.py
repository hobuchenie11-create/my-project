"""Формирование данных ведомости передачи показаний.

Структура печатной ведомости (утверждена):
Кв. | ✔ | Электроэнергия | ГВС сумма | ХВС кухня | ХВС сан.узел |
ГВС кухня | ГВС ванна | Примечание
"""
import sqlite3
from dataclasses import dataclass, field

from database import repository

STATEMENT_COLUMNS = ["Кв.", "✔", "Электроэнергия", "ГВС сумма", "ХВС кухня",
                     "ХВС сан.узел", "ГВС кухня", "ГВС ванна", "Примечание"]


@dataclass
class StatementRow:
    number: str
    submitted: bool = False
    electricity: float | None = None
    hws_sum: float | None = None
    cws_kitchen: float | None = None
    cws_bathroom: float | None = None
    hws_kitchen: float | None = None
    hws_bathroom: float | None = None
    note: str = ""

    def as_cells(self) -> list:
        def fmt(v):
            if v is None:
                return ""
            v = round(v, 3)
            return int(v) if v == int(v) else v
        return [self.number, "✔" if self.submitted else "",
                fmt(self.electricity), fmt(self.hws_sum),
                fmt(self.cws_kitchen), fmt(self.cws_bathroom),
                fmt(self.hws_kitchen), fmt(self.hws_bathroom), self.note]


@dataclass
class Statement:
    period: str
    rows: list[StatementRow] = field(default_factory=list)
    submitted_count: int = 0
    total_count: int = 0


def build_statement(conn: sqlite3.Connection, period: str) -> Statement:
    readings: dict[str, dict[str, float]] = {}
    for row in repository.readings_for_period(conn, period):
        readings.setdefault(row["apartment_number"], {})[row["kind"]] = row["value"]

    statement = Statement(period=period)
    for apt in repository.list_apartments(conn):
        values = readings.get(apt["number"], {})
        row = StatementRow(number=apt["number"], submitted=bool(values),
                           note=apt["note"])
        if apt["type"] == "residential":
            row.electricity = values.get("electricity")
            row.cws_kitchen = values.get("cws_kitchen")
            row.cws_bathroom = values.get("cws_bathroom")
            row.hws_kitchen = values.get("hws_kitchen")
            row.hws_bathroom = values.get("hws_bathroom")
            if row.hws_kitchen is not None or row.hws_bathroom is not None:
                row.hws_sum = (row.hws_kitchen or 0) + (row.hws_bathroom or 0)
        else:
            # Нежилые: ХВС в колонке «ХВС кухня», ГВС в колонке «ГВС кухня»
            row.cws_kitchen = values.get("cws")
            row.hws_kitchen = values.get("hws")
            row.electricity = values.get("electricity")
        statement.rows.append(row)
        if row.submitted:
            statement.submitted_count += 1

    # Итоговая строка для общедомового прибора (заполняется вручную)
    statement.rows.append(StatementRow(number="Общедомовой прибор учета",
                                       note="(заполняется вручную)"))
    statement.total_count = len(repository.list_apartments(conn))
    return statement


def stats_text(conn: sqlite3.Connection, period: str, period_name: str) -> str:
    statement = build_statement(conn, period)
    missing = [r.number for r in statement.rows[:-1] if not r.submitted]
    lines = [f"📈 Статистика за {period_name}", "",
             f"Сдали показания: {statement.submitted_count} из {statement.total_count}"]
    if missing:
        lines.append("")
        lines.append("Не сдали: " + ", ".join(missing))
    return "\n".join(lines)
