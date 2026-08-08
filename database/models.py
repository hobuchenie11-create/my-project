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
    ("tasks", "utility_amount", "REAL"),
    ("tasks", "utility_paid_at", "TEXT NOT NULL DEFAULT ''"),
    ("task_templates", "amount_field", "TEXT NOT NULL DEFAULT 'amount'"),
    ("task_templates", "priority", "TEXT NOT NULL DEFAULT 'normal'"),
    ("tasks", "house_meter_id", "INTEGER"),
]

# За сколько дней до срока задача считается «горящей» (подсветка и напоминание)
TASK_SOON_DAYS = 3

# ---------------------------------------------------------------------------
# Поверка общедомовых приборов учёта
# ---------------------------------------------------------------------------

# Межповерочный интервал по умолчанию, лет. У каждого прибора он свой —
# в справочнике можно указать любой.
VERIFICATION_INTERVAL_YEARS = 4

# За сколько дней до срока поверки заводить задачу и начинать напоминать.
# Поверку нужно организовать заранее: заявка, доступ, акт.
VERIFICATION_LEAD_DAYS = 180

# Общедомовые приборы, которые заводятся при первом запуске.
# Даты последней поверки председатель вносит сам — до этого срок не считается.
DEFAULT_HOUSE_METERS = [
    {"code": "heat", "name": "Тепловая энергия (отопление)"},
    {"code": "hws_house", "name": "ГВС — горячее водоснабжение"},
    {"code": "cws_house", "name": "ХВС — холодное водоснабжение"},
]

# Пометка в ведомости для показаний, переданных после срока сбора
LATE_NOTE = "Переданы после срока сбора показаний"

# ---------------------------------------------------------------------------
# Модуль «Задачи председателя»
# ---------------------------------------------------------------------------

# Статусы задачи. «Просрочена» не хранится — вычисляется по сроку.
TASK_STATUSES = {
    "new": "Новая",
    "in_progress": "В работе",
    "waiting": "Ожидает",
    "done": "Выполнена",
    "cancelled": "Отменена",
}
TASK_OPEN_STATUSES = ("new", "in_progress", "waiting")

TASK_CATEGORIES = {
    "finance": "Спецсчёт и финансы",
    "nonresidential": "Сопровождение нежилого помещения",
    "meters": "Показания и ресурсники",
    "verification": "Поверка приборов учёта",
    "repair": "Текущий ремонт",
    "improvement": "Благоустройство",
    "docs": "Документы и отчётность",
    "meetings": "Собрания",
    "other": "Прочее",
}

TASK_PRIORITIES = {"high": "Высокий", "normal": "Обычный", "low": "Низкий"}

# Регулярные задачи председателя — годовой цикл. Каждый месяц из этих шаблонов
# создаются задачи со своими сроками, статусом и напоминаниями.
# day_start/day_end — окно выполнения в числах месяца.
DEFAULT_TASK_TEMPLATES = [
    {
        "code": "bank_statement",
        "title": "Взять выписку из банка по спецсчёту",
        "category": "finance",
        "day_start": 2, "day_end": 5,
        "needs_amount": 0,
        "amount_field": "", "priority": "normal",
        "description": "Получить банковскую выписку по специальному счёту "
                       "за прошедший месяц.",
    },
    {
        "code": "posting_invoices",
        "title": "Разноска платежей и печать квитанций",
        "category": "finance",
        "day_start": 5, "day_end": 10,
        "needs_amount": 0,
        "amount_field": "", "priority": "normal",
        "description": "Разнести поступления по лицевым счетам, сформировать "
                       "и распечатать квитанции.",
    },
    {
        "code": "nonresidential_payment",
        "title": "Аренда за нежилое помещение — поступление",
        "category": "nonresidential",
        "day_start": 1, "day_end": 10,
        "needs_amount": 1,          # сумма аренды и дата поступления
        "amount_field": "amount",
        "priority": "normal",
        "description": "Проконтролировать, что арендатор внёс арендную плату "
                       "(срок — до 10 числа). Указать сумму и дату.",
    },
    {
        "code": "nonresidential_utilities",
        "title": "❗ Оплата коммунальных услуг по нежилому помещению",
        "category": "nonresidential",
        "day_start": 10, "day_end": 18,
        "needs_amount": 1,          # сумма коммуналки и дата оплаты
        "amount_field": "utility_amount",
        "priority": "high",
        "description": "Важно: оплатить коммунальные услуги по нежилому "
                       "помещению строго до 18 числа. Указать сумму и дату оплаты.",
    },
    {
        "code": "submit_readings_rso",
        "title": "Передать показания ресурсоснабжающим организациям",
        "category": "meters",
        "day_start": 20, "day_end": 25,
        "needs_amount": 0,
        "amount_field": "", "priority": "normal",
        "description": "Передать собранные показания в Росводоканал и ОЭК.",
    },
]

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

-- Шаблоны регулярных задач председателя (годовой цикл)
CREATE TABLE IF NOT EXISTS task_templates (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    code         TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    category     TEXT NOT NULL DEFAULT 'other',
    day_start    INTEGER NOT NULL DEFAULT 1,
    day_end      INTEGER NOT NULL DEFAULT 28,
    needs_amount INTEGER NOT NULL DEFAULT 0,
    amount_field TEXT NOT NULL DEFAULT 'amount',  -- amount | utility_amount
    priority     TEXT NOT NULL DEFAULT 'normal',
    assignee     TEXT NOT NULL DEFAULT '',
    is_active    INTEGER NOT NULL DEFAULT 1,
    sort_order   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id  INTEGER REFERENCES task_templates (id),
    period       TEXT NOT NULL DEFAULT '',        -- 'YYYY-MM' у регулярных
    title        TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    category     TEXT NOT NULL DEFAULT 'other',
    priority     TEXT NOT NULL DEFAULT 'normal',
    status       TEXT NOT NULL DEFAULT 'new',
    assignee     TEXT NOT NULL DEFAULT '',
    start_date   TEXT NOT NULL DEFAULT '',        -- с какого числа можно делать
    due_date     TEXT NOT NULL DEFAULT '',        -- до какого числа
    amount       REAL,                            -- сумма аренды (нежилое)
    paid_at      TEXT NOT NULL DEFAULT '',        -- дата поступления аренды
    utility_amount REAL,                          -- сумма оплаты коммуналки
    utility_paid_at TEXT NOT NULL DEFAULT '',     -- дата оплаты коммуналки
    apartment_id INTEGER REFERENCES apartments (id),
    house_meter_id INTEGER REFERENCES house_meters (id),
    source       TEXT NOT NULL DEFAULT 'chairman',
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    done_at      TEXT NOT NULL DEFAULT '',
    UNIQUE (template_id, period)
);

CREATE INDEX IF NOT EXISTS idx_tasks_period ON tasks (period);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);

-- Общедомовые приборы учёта и их поверка
CREATE TABLE IF NOT EXISTS house_meters (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT NOT NULL UNIQUE,
    name           TEXT NOT NULL,
    serial         TEXT NOT NULL DEFAULT '',
    location       TEXT NOT NULL DEFAULT '',
    last_verified  TEXT NOT NULL DEFAULT '',      -- дата последней поверки
    interval_years INTEGER NOT NULL DEFAULT 4,    -- межповерочный интервал
    note           TEXT NOT NULL DEFAULT '',
    is_active      INTEGER NOT NULL DEFAULT 1,
    sort_order     INTEGER NOT NULL DEFAULT 0
);

-- Журнал поверок: сохраняем каждую, чтобы была история по прибору
CREATE TABLE IF NOT EXISTS verifications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    house_meter_id INTEGER NOT NULL REFERENCES house_meters (id),
    verified_at    TEXT NOT NULL,
    next_due       TEXT NOT NULL DEFAULT '',
    document       TEXT NOT NULL DEFAULT '',      -- номер акта/свидетельства
    note           TEXT NOT NULL DEFAULT '',
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Журнал изменений по задачам
CREATE TABLE IF NOT EXISTS task_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id    INTEGER NOT NULL REFERENCES tasks (id),
    tg_id      INTEGER,
    action     TEXT NOT NULL,
    details    TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);
"""
