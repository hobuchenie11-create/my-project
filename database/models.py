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

# Наборы приборов по типу/планировке квартиры (порядок = порядок опроса в боте).
#   full    — 3-комнатные: раздельный учет ХВС/ГВС по кухне и санузлу
#   compact — 1-2-комнатные: один ХВС и один ГВС на квартиру
LAYOUT_METERS: dict[str, list[str]] = {
    "full": ["electricity", "cws_kitchen", "cws_bathroom", "hws_kitchen", "hws_bathroom"],
    "compact": ["electricity", "cws", "hws"],
}
DEFAULT_LAYOUT = "full"

# Набор приборов для нежилого помещения
NONRESIDENTIAL_METERS = ["cws", "hws"]

# Единицы измерения
METER_UNITS = {"electricity": "кВт·ч"}
DEFAULT_UNIT = "м³"

# Пороги «подозрительно большого» расхода за месяц (для предупреждений).
# ХВС/ГВС: расход > 100 м³ за месяц — повод уточнить (Этап 4).
DELTA_WARN_LIMITS = {"electricity": 1500.0}
DELTA_WARN_DEFAULT = 100.0

SCHEMA = """
CREATE TABLE IF NOT EXISTS apartments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    number      TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL DEFAULT 'residential',  -- residential | nonresidential
    layout      TEXT NOT NULL DEFAULT 'full',         -- full | compact (для жилых)
    sort_order  INTEGER NOT NULL DEFAULT 0,
    note        TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS users (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id        INTEGER NOT NULL UNIQUE,
    full_name    TEXT NOT NULL,
    phone        TEXT NOT NULL DEFAULT '',
    apartment_id INTEGER REFERENCES apartments (id),
    role         TEXT NOT NULL DEFAULT 'resident',    -- resident | admin
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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
    source     TEXT NOT NULL DEFAULT 'bot',            -- bot | chat | admin
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
