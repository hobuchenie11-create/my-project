"""Схема базы данных DH OS и справочник видов приборов учета."""

# Виды приборов учета: ключ -> подпись для пользователя
METER_KINDS: dict[str, str] = {
    "electricity": "Электроэнергия",
    "cws_kitchen": "ХВС кухня",
    "cws_bathroom": "ХВС сан.узел",
    "hws_kitchen": "ГВС кухня",
    "hws_bathroom": "ГВС ванна",
    "cws": "ХВС",
    "hws": "ГВС",
}

# Набор приборов квартиры определяется количеством счётчиков ХВС и ГВС —
# они независимы. Один счётчик -> общий прибор (cws/hws), два -> раздельно по
# кухне и санузлу. Электросчётчик у всех один. Встречается и смешанный случай
# (1 ХВС + 2 ГВС), поэтому ХВС и ГВС считаются отдельно.
def apartment_meters(cws_count: int, hws_count: int) -> list[str]:
    """Список приборов квартиры в порядке опроса в боте."""
    meters = ["electricity"]
    meters += ["cws_kitchen", "cws_bathroom"] if cws_count >= 2 else ["cws"]
    meters += ["hws_kitchen", "hws_bathroom"] if hws_count >= 2 else ["hws"]
    return meters


def layout_label(cws_count: int, hws_count: int) -> str:
    """Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»."""
    return f"ХВС×{min(cws_count, 2)} · ГВС×{min(hws_count, 2)}"


# Набор приборов по умолчанию для жилой квартиры (пока не загружен справочник)
DEFAULT_CWS_COUNT = 1
DEFAULT_HWS_COUNT = 1

# Набор приборов для нежилого помещения
NONRESIDENTIAL_METERS = ["cws", "hws"]

# Единицы измерения
METER_UNITS = {"electricity": "кВт·ч"}
DEFAULT_UNIT = "м³"

# Пороги «подозрительно большого» расхода за месяц (для предупреждений).
# ХВС/ГВС: расход > 100 м³ за месяц — повод уточнить (Этап 4).
DELTA_WARN_LIMITS = {"electricity": 1500.0}
DELTA_WARN_DEFAULT = 100.0

# Способы передачи показаний (колонка «Источник» в книге Excel)
SOURCE_LABELS = {
    "bot": "Telegram (бот)",
    "chat": "Telegram (чат)",
    "whatsapp": "WhatsApp",
    "admin": "Вручную",
}

# Колонки, добавленные после первой версии схемы: имя таблицы -> (колонка, тип)
MIGRATIONS = [
    ("apartments", "rooms", "INTEGER NOT NULL DEFAULT 0"),
    ("users", "username", "TEXT NOT NULL DEFAULT ''"),
    ("users", "last_seen", "TEXT NOT NULL DEFAULT ''"),
    ("readings", "late", "INTEGER NOT NULL DEFAULT 0"),
]

# Пометка в ведомости для показаний, переданных после срока сбора
LATE_NOTE = "Переданы после срока сбора показаний"

SCHEMA = """
CREATE TABLE IF NOT EXISTS apartments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    number      TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL DEFAULT 'residential',  -- residential | nonresidential
    rooms       INTEGER NOT NULL DEFAULT 0,           -- число комнат (0 — неизвестно)
    layout      TEXT NOT NULL DEFAULT '',             -- подпись планировки (ХВС×.. · ГВС×..)
    sort_order  INTEGER NOT NULL DEFAULT 0,
    note        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id        INTEGER NOT NULL UNIQUE,
    full_name    TEXT NOT NULL,
    phone        TEXT NOT NULL DEFAULT '',
    username     TEXT NOT NULL DEFAULT '',            -- Telegram @username
    apartment_id INTEGER REFERENCES apartments (id),
    role         TEXT NOT NULL DEFAULT 'resident',    -- resident | admin
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    last_seen    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS meters (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    apartment_id INTEGER NOT NULL REFERENCES apartments (id),
    kind         TEXT NOT NULL,
    serial       TEXT NOT NULL DEFAULT '',
    is_active    INTEGER NOT NULL DEFAULT 1,
    UNIQUE (apartment_id, kind)
);

CREATE TABLE IF NOT EXISTS readings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    meter_id   INTEGER NOT NULL REFERENCES meters (id),
    user_id    INTEGER REFERENCES users (id),
    period     TEXT NOT NULL,                          -- 'YYYY-MM'
    value      REAL NOT NULL,
    source     TEXT NOT NULL DEFAULT 'bot',            -- bot | chat | whatsapp | admin
    late       INTEGER NOT NULL DEFAULT 0,             -- 1 — передано после срока сбора
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE INDEX IF NOT EXISTS idx_readings_meter_period ON readings (meter_id, period);

-- Последнее показание по каждому прибору
CREATE VIEW IF NOT EXISTS current_readings AS
SELECT r.*
FROM readings r
JOIN (SELECT meter_id, MAX(id) AS max_id FROM readings GROUP BY meter_id) last
     ON last.max_id = r.id;

CREATE TABLE IF NOT EXISTS reports (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    period     TEXT NOT NULL,
    file_path  TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id      INTEGER,
    action     TEXT NOT NULL,
    details    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""
