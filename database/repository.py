"""Доступ к базе данных SQLite. Все запросы проекта собраны здесь."""
import sqlite3
from pathlib import Path

from bot.config import config
from database.models import SCHEMA


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or config.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


# ---------- apartments ----------

def get_apartment_by_number(conn: sqlite3.Connection, number: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM apartments WHERE number = ?", (number.strip(),)
    ).fetchone()


def list_apartments(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT * FROM apartments ORDER BY sort_order, id").fetchall()


def get_apartment_by_id(conn: sqlite3.Connection, apartment_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM apartments WHERE id = ?", (apartment_id,)
    ).fetchone()


def upsert_apartment(conn: sqlite3.Connection, number: str, type_: str,
                     sort_order: int, note: str = "", layout: str = "full") -> int:
    conn.execute(
        """INSERT INTO apartments (number, type, layout, sort_order, note)
           VALUES (?, ?, ?, ?, ?)
           ON CONFLICT(number) DO UPDATE SET type = excluded.type,
               layout = excluded.layout, sort_order = excluded.sort_order,
               note = excluded.note""",
        (number, type_, layout, sort_order, note),
    )
    return conn.execute(
        "SELECT id FROM apartments WHERE number = ?", (number,)
    ).fetchone()["id"]


# ---------- meters ----------

def ensure_meter(conn: sqlite3.Connection, apartment_id: int, kind: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO meters (apartment_id, kind) VALUES (?, ?)",
        (apartment_id, kind),
    )


def set_meters(conn: sqlite3.Connection, apartment_id: int, kinds: list[str]) -> None:
    """Приводит набор приборов квартиры к заданному: нужные — активны, лишние — нет."""
    for kind in kinds:
        ensure_meter(conn, apartment_id, kind)
    placeholders = ",".join("?" * len(kinds)) or "''"
    conn.execute(
        f"UPDATE meters SET is_active = 0 WHERE apartment_id = ? "
        f"AND kind NOT IN ({placeholders})",
        (apartment_id, *kinds),
    )
    conn.execute(
        f"UPDATE meters SET is_active = 1 WHERE apartment_id = ? "
        f"AND kind IN ({placeholders})",
        (apartment_id, *kinds),
    )


def meters_for_apartment(conn: sqlite3.Connection, apartment_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM meters WHERE apartment_id = ? AND is_active = 1 ORDER BY id",
        (apartment_id,),
    ).fetchall()


def get_meter(conn: sqlite3.Connection, apartment_id: int, kind: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM meters WHERE apartment_id = ? AND kind = ? AND is_active = 1",
        (apartment_id, kind),
    ).fetchone()


# ---------- users ----------

def get_user_by_tg(conn: sqlite3.Connection, tg_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()


def create_user(conn: sqlite3.Connection, tg_id: int, full_name: str,
                apartment_id: int, role: str = "resident") -> int:
    cur = conn.execute(
        "INSERT INTO users (tg_id, full_name, apartment_id, role) VALUES (?, ?, ?, ?)",
        (tg_id, full_name, apartment_id, role),
    )
    conn.commit()
    return cur.lastrowid


def list_users(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT u.*, a.number AS apartment_number
           FROM users u LEFT JOIN apartments a ON a.id = u.apartment_id
           ORDER BY a.sort_order, a.id"""
    ).fetchall()


# ---------- readings ----------

def last_reading(conn: sqlite3.Connection, meter_id: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM current_readings WHERE meter_id = ?", (meter_id,)
    ).fetchone()


def add_reading(conn: sqlite3.Connection, meter_id: int, user_id: int | None,
                period: str, value: float, source: str = "bot") -> None:
    conn.execute(
        "INSERT INTO readings (meter_id, user_id, period, value, source) VALUES (?, ?, ?, ?, ?)",
        (meter_id, user_id, period, value, source),
    )
    conn.commit()


def readings_for_period(conn: sqlite3.Connection, period: str) -> list[sqlite3.Row]:
    """Последнее показание каждого прибора за период, с номером квартиры."""
    return conn.execute(
        """SELECT a.number AS apartment_number, a.type AS apartment_type,
                  m.kind, r.value, r.created_at
           FROM readings r
           JOIN meters m ON m.id = r.meter_id
           JOIN apartments a ON a.id = m.apartment_id
           WHERE r.period = ?
             AND r.id = (SELECT MAX(r2.id) FROM readings r2
                         WHERE r2.meter_id = r.meter_id AND r2.period = ?)
           ORDER BY a.sort_order, a.id""",
        (period, period),
    ).fetchall()


def readings_history_for_apartment(conn: sqlite3.Connection, apartment_id: int,
                                   limit: int = 30) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT r.period, m.kind, r.value, r.source, r.created_at
           FROM readings r JOIN meters m ON m.id = r.meter_id
           WHERE m.apartment_id = ?
           ORDER BY r.id DESC LIMIT ?""",
        (apartment_id, limit),
    ).fetchall()


def apartments_submitted(conn: sqlite3.Connection, period: str) -> set[str]:
    rows = conn.execute(
        """SELECT DISTINCT a.number
           FROM readings r
           JOIN meters m ON m.id = r.meter_id
           JOIN apartments a ON a.id = m.apartment_id
           WHERE r.period = ?""",
        (period,),
    ).fetchall()
    return {row["number"] for row in rows}


# ---------- reports / events ----------

def debtors(conn: sqlite3.Connection, period: str) -> list[sqlite3.Row]:
    """Квартиры, не сдавшие показания за период, с зарегистрированным жителем."""
    return conn.execute(
        """SELECT a.number, a.id AS apartment_id, u.tg_id, u.full_name
           FROM apartments a
           LEFT JOIN users u ON u.apartment_id = a.id
           WHERE a.number NOT IN (
               SELECT DISTINCT a2.number FROM readings r
               JOIN meters m ON m.id = r.meter_id
               JOIN apartments a2 ON a2.id = m.apartment_id
               WHERE r.period = ?)
           ORDER BY a.sort_order, a.id""",
        (period,),
    ).fetchall()


def save_report(conn: sqlite3.Connection, period: str, file_path: str) -> None:
    conn.execute("INSERT INTO reports (period, file_path) VALUES (?, ?)", (period, file_path))
    conn.commit()


def log_event(conn: sqlite3.Connection, tg_id: int | None, action: str, details: str = "") -> None:
    conn.execute(
        "INSERT INTO events (tg_id, action, details) VALUES (?, ?, ?)",
        (tg_id, action, details),
    )
    conn.commit()
