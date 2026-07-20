"""Операции с реестром квартир."""
import sqlite3

from database import repository


def find_apartment(conn: sqlite3.Connection, number: str) -> sqlite3.Row | None:
    return repository.get_apartment_by_number(conn, number)


def registry_summary(conn: sqlite3.Connection, period: str) -> str:
    """Текстовый реестр квартир с отметкой о сдаче показаний за период."""
    submitted = repository.apartments_submitted(conn, period)
    lines = [f"📋 Реестр квартир — {period}", ""]
    for apt in repository.list_apartments(conn):
        mark = "✅" if apt["number"] in submitted else "▫️"
        layout = f" · {apt['layout']}" if apt["layout"] else ""
        lines.append(f"{mark} {_display_number(apt)}{layout}")
    lines.append("")
    lines.append(f"Сдали: {len(submitted)} из {len(repository.list_apartments(conn))}")
    return "\n".join(lines)


def _display_number(apt: sqlite3.Row) -> str:
    if apt["type"] == "residential":
        return f"кв. {apt['number']}"
    return apt["number"]
