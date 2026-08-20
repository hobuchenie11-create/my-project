"""Доступ к базе данных SQLite. Все запросы проекта собраны здесь."""
import sqlite3
from pathlib import Path

from bot.config import config
from database.models import MIGRATIONS, SCHEMA


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path or config.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    _apply_migrations(conn)
    conn.commit()


def _apply_migrations(conn: sqlite3.Connection) -> None:
    """Добавляет колонки, появившиеся после первой версии схемы (без потери данных)."""
    for table, column, definition in MIGRATIONS:
        existing = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
                     sort_order: int, note: str = "", layout: str = "",
                     rooms: int = 0) -> int:
    conn.execute(
        """INSERT INTO apartments (number, type, rooms, layout, sort_order, note)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(number) DO UPDATE SET type = excluded.type,
               rooms = excluded.rooms, layout = excluded.layout,
               sort_order = excluded.sort_order, note = excluded.note""",
        (number, type_, rooms, layout, sort_order, note),
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
                apartment_id: int, role: str = "resident",
                username: str = "") -> int:
    cur = conn.execute(
        """INSERT INTO users (tg_id, full_name, apartment_id, role, username, last_seen)
           VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))""",
        (tg_id, full_name, apartment_id, role, username),
    )
    conn.commit()
    return cur.lastrowid


def touch_user(conn: sqlite3.Connection, tg_id: int, username: str = "") -> None:
    """Отмечает последнюю активность жителя (и обновляет username)."""
    conn.execute(
        """UPDATE users SET last_seen = datetime('now', 'localtime'),
               username = CASE WHEN ? <> '' THEN ? ELSE username END
           WHERE tg_id = ?""",
        (username, username, tg_id),
    )
    conn.commit()


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


def reading_for_period(conn: sqlite3.Connection, meter_id: int,
                       period: str) -> sqlite3.Row | None:
    """Показание прибора, которое сейчас идёт в ведомость за этот период."""
    return conn.execute(
        """SELECT * FROM readings WHERE meter_id = ? AND period = ?
           ORDER BY id DESC LIMIT 1""",
        (meter_id, period),
    ).fetchone()


def last_reading_before_period(conn: sqlite3.Connection, meter_id: int,
                               period: str) -> sqlite3.Row | None:
    """Последнее показание прибора за месяцы до указанного.

    Нужно для правок: сверять исправленное показание с ошибочным за тот же
    месяц бессмысленно — сравнивать надо с прошлым месяцем.
    """
    return conn.execute(
        """SELECT * FROM readings
           WHERE meter_id = ? AND period < ?
           ORDER BY period DESC, id DESC LIMIT 1""",
        (meter_id, period),
    ).fetchone()


def add_reading(conn: sqlite3.Connection, meter_id: int, user_id: int | None,
                period: str, value: float, source: str = "bot",
                late: bool = False) -> None:
    conn.execute(
        """INSERT INTO readings (meter_id, user_id, period, value, source, late)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (meter_id, user_id, period, value, source, int(late)),
    )
    conn.commit()


def readings_for_period(conn: sqlite3.Connection, period: str) -> list[sqlite3.Row]:
    """Последнее показание каждого прибора за период, с номером квартиры."""
    return conn.execute(
        """SELECT a.number AS apartment_number, a.type AS apartment_type,
                  m.kind, r.value, r.created_at, r.late
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


def find_readings(conn: sqlite3.Connection, before: str = "", period: str = "",
                  apartment: str = "", source: str = "") -> list[sqlite3.Row]:
    """Показания по фильтрам — для разбора и удаления тестовых записей."""
    where, params = ["1 = 1"], []
    if before:
        where.append("r.created_at < ?")
        params.append(before)
    if period:
        where.append("r.period = ?")
        params.append(period)
    if apartment:
        where.append("a.number = ?")
        params.append(apartment)
    if source:
        where.append("r.source = ?")
        params.append(source)

    return conn.execute(
        f"""SELECT r.id, r.created_at, r.period, r.value, r.source,
                   m.kind, a.number AS apartment_number
            FROM readings r
            JOIN meters m ON m.id = r.meter_id
            JOIN apartments a ON a.id = m.apartment_id
            WHERE {' AND '.join(where)}
            ORDER BY a.sort_order, a.id, r.id""",
        params,
    ).fetchall()


def delete_readings(conn: sqlite3.Connection, ids: list[int]) -> int:
    """Удаляет показания по списку id. Возвращает число удалённых строк."""
    if not ids:
        return 0
    placeholders = ",".join("?" * len(ids))
    cur = conn.execute(f"DELETE FROM readings WHERE id IN ({placeholders})", ids)
    conn.commit()
    return cur.rowcount


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


def registry_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Лист «Реестр квартир»: квартира + житель + последняя передача."""
    return conn.execute(
        """SELECT a.id, a.number, a.type, a.rooms, a.layout, a.note,
                  u.tg_id, u.username, u.full_name, u.created_at AS registered_at,
                  u.last_seen,
                  (SELECT MAX(r.created_at) FROM readings r
                   JOIN meters m ON m.id = r.meter_id
                   WHERE m.apartment_id = a.id) AS last_submission,
                  (SELECT r.source FROM readings r
                   JOIN meters m ON m.id = r.meter_id
                   WHERE m.apartment_id = a.id
                   ORDER BY r.id DESC LIMIT 1) AS last_source
           FROM apartments a
           LEFT JOIN users u ON u.apartment_id = a.id
           ORDER BY a.sort_order, a.id"""
    ).fetchall()


def all_readings(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Лист «Переданные показания»: полная история, свежие сверху."""
    return conn.execute(
        """SELECT r.created_at, r.period, a.number AS apartment_number,
                  m.kind, r.value, r.source
           FROM readings r
           JOIN meters m ON m.id = r.meter_id
           JOIN apartments a ON a.id = m.apartment_id
           ORDER BY r.id DESC"""
    ).fetchall()


def current_readings_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Лист «Текущие показания»: последнее значение каждого прибора."""
    return conn.execute(
        """SELECT a.number AS apartment_number, a.sort_order, m.kind,
                  r.value, r.period, r.created_at, r.source
           FROM current_readings r
           JOIN meters m ON m.id = r.meter_id
           JOIN apartments a ON a.id = m.apartment_id
           ORDER BY a.sort_order, a.id"""
    ).fetchall()


def save_report(conn: sqlite3.Connection, period: str, file_path: str) -> None:
    conn.execute("INSERT INTO reports (period, file_path) VALUES (?, ?)", (period, file_path))
    conn.commit()


# ---------- задачи председателя ----------

def upsert_task_template(conn: sqlite3.Connection, code: str, title: str,
                         description: str, category: str, day_start: int,
                         day_end: int, needs_amount: int, sort_order: int,
                         amount_field: str = "amount",
                         priority: str = "normal") -> int:
    conn.execute(
        """INSERT INTO task_templates
               (code, title, description, category, day_start, day_end,
                needs_amount, amount_field, priority, sort_order)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(code) DO UPDATE SET title = excluded.title,
               description = excluded.description, category = excluded.category,
               day_start = excluded.day_start, day_end = excluded.day_end,
               needs_amount = excluded.needs_amount,
               amount_field = excluded.amount_field,
               priority = excluded.priority,
               sort_order = excluded.sort_order""",
        (code, title, description, category, day_start, day_end,
         needs_amount, amount_field, priority, sort_order),
    )
    conn.commit()
    return conn.execute("SELECT id FROM task_templates WHERE code = ?",
                        (code,)).fetchone()["id"]


def sync_tasks_with_templates(conn: sqlite3.Connection) -> int:
    """Подтягивает в задачи изменения шаблонов (название, категория, приоритет).

    Нужна, когда регламент уточняется: уже созданные задачи не должны остаться
    со старой категорией или формулировкой.
    """
    cur = conn.execute(
        """UPDATE tasks SET
               title = (SELECT t.title FROM task_templates t WHERE t.id = tasks.template_id),
               category = (SELECT t.category FROM task_templates t WHERE t.id = tasks.template_id),
               priority = (SELECT t.priority FROM task_templates t WHERE t.id = tasks.template_id),
               description = (SELECT t.description FROM task_templates t WHERE t.id = tasks.template_id)
           WHERE template_id IS NOT NULL""")
    conn.commit()
    return cur.rowcount


def active_task_templates(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM task_templates WHERE is_active = 1 ORDER BY sort_order, id"
    ).fetchall()


def create_task(conn: sqlite3.Connection, title: str, **fields) -> int:
    columns = ["title"] + list(fields)
    values = [title] + list(fields.values())
    placeholders = ", ".join("?" * len(columns))
    cur = conn.execute(
        f"INSERT INTO tasks ({', '.join(columns)}) VALUES ({placeholders})", values
    )
    conn.commit()
    return cur.lastrowid


def task_exists(conn: sqlite3.Connection, template_id: int, period: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM tasks WHERE template_id = ? AND period = ?",
        (template_id, period),
    ).fetchone() is not None


def get_task(conn: sqlite3.Connection, task_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()


def update_task(conn: sqlite3.Connection, task_id: int, **fields) -> None:
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(
        f"UPDATE tasks SET {assignments}, updated_at = datetime('now', 'localtime') "
        f"WHERE id = ?",
        (*fields.values(), task_id),
    )
    conn.commit()


def tasks_for_period(conn: sqlite3.Connection, period: str) -> list[sqlite3.Row]:
    """Задачи месяца в хронологическом порядке: по сроку, затем по началу окна."""
    return conn.execute(
        "SELECT * FROM tasks WHERE period = ? ORDER BY due_date, start_date, id",
        (period,),
    ).fetchall()


def open_tasks(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Все незакрытые задачи — по сроку, ближайшие первыми."""
    return conn.execute(
        """SELECT * FROM tasks WHERE status IN ('new', 'in_progress', 'waiting')
           ORDER BY (due_date = ''), due_date, start_date, id"""
    ).fetchall()


def one_off_tasks(conn: sqlite3.Connection, include_done: bool = False) -> list[sqlite3.Row]:
    """Разовые задачи (не из годового цикла) — то, что председатель ставит сам."""
    where = "template_id IS NULL"
    if not include_done:
        where += " AND status IN ('new', 'in_progress', 'waiting')"
    return conn.execute(
        f"SELECT * FROM tasks WHERE {where} ORDER BY (due_date = ''), due_date, id"
    ).fetchall()


def tasks_in_year(conn: sqlite3.Connection, year: int) -> list[sqlite3.Row]:
    """Регулярные задачи года — годовой цикл (без разовых), по датам."""
    return conn.execute(
        """SELECT * FROM tasks
           WHERE template_id IS NOT NULL AND period LIKE ?
           ORDER BY period, due_date, start_date, id""",
        (f"{year}-%",),
    ).fetchall()


def one_off_tasks_all(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Все разовые задачи, включая закрытые — для листа «Мои задачи»."""
    return conn.execute(
        """SELECT * FROM tasks WHERE template_id IS NULL
           ORDER BY (status IN ('done', 'cancelled')), (due_date = ''),
                    due_date, id"""
    ).fetchall()


def log_task_event(conn: sqlite3.Connection, task_id: int, tg_id: int | None,
                   action: str, details: str = "") -> None:
    conn.execute(
        "INSERT INTO task_events (task_id, tg_id, action, details) VALUES (?, ?, ?, ?)",
        (task_id, tg_id, action, details),
    )
    conn.commit()


def task_history(conn: sqlite3.Connection, task_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM task_events WHERE task_id = ? ORDER BY id", (task_id,)
    ).fetchall()


# ---------- общедомовые приборы и поверка ----------

def ensure_house_meter(conn: sqlite3.Connection, code: str, name: str,
                       sort_order: int, interval_years: int) -> int:
    conn.execute(
        """INSERT INTO house_meters (code, name, sort_order, interval_years)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(code) DO NOTHING""",
        (code, name, sort_order, interval_years),
    )
    conn.commit()
    return conn.execute("SELECT id FROM house_meters WHERE code = ?",
                        (code,)).fetchone()["id"]


def house_meters(conn: sqlite3.Connection, only_active: bool = True) -> list[sqlite3.Row]:
    where = "WHERE is_active = 1" if only_active else ""
    return conn.execute(
        f"SELECT * FROM house_meters {where} ORDER BY sort_order, id").fetchall()


def get_house_meter(conn: sqlite3.Connection, meter_id: int) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM house_meters WHERE id = ?",
                        (meter_id,)).fetchone()


def update_house_meter(conn: sqlite3.Connection, meter_id: int, **fields) -> None:
    if not fields:
        return
    assignments = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(f"UPDATE house_meters SET {assignments} WHERE id = ?",
                 (*fields.values(), meter_id))
    conn.commit()


def add_verification(conn: sqlite3.Connection, house_meter_id: int,
                     verified_at: str, next_due: str, document: str = "",
                     note: str = "") -> int:
    cur = conn.execute(
        """INSERT INTO verifications (house_meter_id, verified_at, next_due,
                                      document, note)
           VALUES (?, ?, ?, ?, ?)""",
        (house_meter_id, verified_at, next_due, document, note),
    )
    conn.commit()
    return cur.lastrowid


def verification_history(conn: sqlite3.Connection,
                         house_meter_id: int) -> list[sqlite3.Row]:
    return conn.execute(
        """SELECT * FROM verifications WHERE house_meter_id = ?
           ORDER BY verified_at DESC""",
        (house_meter_id,),
    ).fetchall()


def verification_task(conn: sqlite3.Connection, house_meter_id: int,
                      due_date: str) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM tasks WHERE house_meter_id = ? AND due_date = ?",
        (house_meter_id, due_date),
    ).fetchone()


# ---------- памятки Домоведа ----------

def upsert_memo(conn: sqlite3.Connection, code: str, title: str, category: str,
                keywords: str, body: str, image: str, sort_order: int) -> None:
    conn.execute(
        """INSERT INTO faq (code, title, category, keywords, body, image,
                            sort_order, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1)
           ON CONFLICT(code) DO UPDATE SET title = excluded.title,
               category = excluded.category, keywords = excluded.keywords,
               body = excluded.body, image = excluded.image,
               sort_order = excluded.sort_order, is_active = 1,
               updated_at = datetime('now', 'localtime')""",
        (code, title, category, keywords, body, image, sort_order),
    )
    conn.commit()


def deactivate_missing_memos(conn: sqlite3.Connection, codes: list[str]) -> None:
    """Памятки, файлов которых больше нет, убираем из меню (но не из базы)."""
    placeholders = ",".join("?" * len(codes)) or "''"
    conn.execute(f"UPDATE faq SET is_active = 0 WHERE code NOT IN ({placeholders})",
                 codes)
    conn.commit()


def active_memos(conn: sqlite3.Connection,
                 category: str = "") -> list[sqlite3.Row]:
    where = "WHERE is_active = 1"
    params: tuple = ()
    if category:
        where += " AND category = ?"
        params = (category,)
    return conn.execute(
        f"SELECT * FROM faq {where} ORDER BY sort_order, title", params
    ).fetchall()


def get_memo(conn: sqlite3.Connection, code: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM faq WHERE code = ? AND is_active = 1",
                        (code,)).fetchone()


def memo_categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        """SELECT category, MIN(sort_order) AS ord FROM faq WHERE is_active = 1
           GROUP BY category ORDER BY ord, category"""
    ).fetchall()
    return [row["category"] for row in rows]


def add_faq_gap(conn: sqlite3.Connection, tg_id: int | None, apartment: str,
                question: str) -> None:
    conn.execute(
        "INSERT INTO faq_gaps (tg_id, apartment, question) VALUES (?, ?, ?)",
        (tg_id, apartment, question),
    )
    conn.commit()


def faq_gaps(conn: sqlite3.Connection, limit: int = 20) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM faq_gaps WHERE answered = 0 ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()


def log_event(conn: sqlite3.Connection, tg_id: int | None, action: str, details: str = "") -> None:
    conn.execute(
        "INSERT INTO events (tg_id, action, details) VALUES (?, ?, ?)",
        (tg_id, action, details),
    )
    conn.commit()
