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

# Набор приборов для нежилого помещения по умолчанию
NONRESIDENTIAL_METERS = ["electricity", "cws", "hws"]

# У нежилых помещений набор приборов свой: во втором стоит только
# электросчётчик, воды там нет.
NONRESIDENTIAL_METER_SETS = {
    1: ["electricity", "cws", "hws"],
    2: ["electricity"],
}

# Общедомовой прибор учёта — отдельная строка ведомости. Показания по нему
# передаёт председатель, так же как по квартире.
COMMON_NUMBER = "Общедомовой прибор учета"
COMMON_METERS = ["electricity"]

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
    # Комментарий председателя к задаче. Отдельно от description: описание
    # приходит из шаблона регламента и обновляется вместе с ним, а этот
    # комментарий пишется руками (в том числе правкой в Excel) и не затирается.
    ("tasks", "note", "TEXT NOT NULL DEFAULT ''"),
    # Во вкладке приборов появилось оборудование с гарантией (лифт): у него
    # свой вид записи и свой срок напоминания
    ("house_meters", "kind", "TEXT NOT NULL DEFAULT 'verification'"),
    ("house_meters", "lead_days", "INTEGER NOT NULL DEFAULT 180"),
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

# Гарантийный срок на оборудование считается так же, как межповерочный
# интервал: от даты ввода в эксплуатацию. Разница в том, что делать перед
# сроком: поверку организуют заранее (полгода), а по гарантии достаточно
# успеть осмотреть оборудование и предъявить претензии — хватает трёх месяцев.
WARRANTY_LEAD_DAYS = 90

# Виды записей во вкладке «Приборы учёта и оборудование»
KIND_VERIFICATION = "verification"   # прибор учёта: срок поверки
KIND_WARRANTY = "warranty"           # оборудование: срок гарантии

# Общедомовые приборы и оборудование, которые заводятся при первом запуске.
# Даты председатель вносит сама — до этого срок не считается. Исключение —
# лифт: его паспортные данные известны и внесены сразу.
DEFAULT_HOUSE_METERS = [
    {"code": "heat", "name": "Тепловая энергия (отопление)"},
    {"code": "hws_house", "name": "ГВС — горячее водоснабжение"},
    {"code": "cws_house", "name": "ХВС — холодное водоснабжение"},
    {
        "code": "lift_1",
        "name": "Лифт, подъезд 1",
        "kind": KIND_WARRANTY,
        "serial": "348578",
        "location": "подъезд 1",
        "interval_years": 5,             # гарантия изготовителя — 5 лет
        "lead_days": WARRANTY_LEAD_DAYS,
        # Точка отсчёта гарантии — ввод в эксплуатацию, не дата изготовления
        "last_verified": "2026-07-10",
        "note": ('Изготовитель ОАО "Могилевлифтмаш", дата изготовления — '
                 "март 2026, ввод в эксплуатацию — 10.07.2026. "
                 "Гарантийный срок 5 лет."),
    },
    {
        # Строка заведена заранее: лифт второго подъезда меняют позже.
        # Дату ввода в эксплуатацию и заводской номер председатель внесёт
        # сама — до этого срок гарантии не считается.
        "code": "lift_2",
        "name": "Лифт, подъезд 2",
        "kind": KIND_WARRANTY,
        "location": "подъезд 2",
        "interval_years": 5,
        "lead_days": WARRANTY_LEAD_DAYS,
        "note": "Заполнить после замены лифта: заводской № и дату ввода "
                "в эксплуатацию.",
    },
]

# Пометка в ведомости для показаний, переданных после срока сбора
LATE_NOTE = "Переданы после срока сбора показаний"

# ---------------------------------------------------------------------------
# Модуль «Памятки» — база знаний Домоведа
# ---------------------------------------------------------------------------

# Разделы памяток. Порядок задаёт порядок кнопок у жителя.
FAQ_CATEGORIES = {
    "payments": "💳 Оплата",
    "gates": "🚗 Ворота и шлагбаум",
    "access": "🚶 Доступ во двор",
    "gsm": "📱 GSM-модуль",
    "meters": "🚰 Показания счётчиков",
    "contacts": "☎️ Контакты служб",
    "rules": "📗 Правила проживания",
    "newcomers": "🔑 Новосёлам",
}

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
    "services": "Абонентские платежи и обслуживание",
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
#
# Порядок в списке — хронологический, по сроку (day_end), при равном сроке —
# по началу окна. Из него берётся sort_order шаблонов, поэтому и в боте, и в
# годовом плане задачи месяца идут по датам, а не по времени добавления.
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
        "code": "gsm_fee",
        "title": "Оплатить абонентскую плату за GSM-модуль",
        "category": "services",
        "day_start": 5, "day_end": 7,
        "needs_amount": 0,
        "amount_field": "", "priority": "normal",
        "description": "Внести абонентскую плату за GSM-модуль — срок до 7 "
                       "числа. Напоминания начинаются с 5 числа.",
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
    {
        "code": "nonresidential_payment",
        "title": "Аренда за нежилое помещение — поступление",
        "category": "nonresidential",
        "day_start": 25, "day_end": 30,
        "needs_amount": 1,          # сумма аренды и дата поступления
        "amount_field": "amount",
        "priority": "normal",
        "description": "Проверить поступление арендной платы за нежилое "
                       "помещение — платёж приходит с 25 по 30 число "
                       "(в феврале — по последний день месяца). "
                       "Указать сумму и дату поступления.",
    },
    {
        "code": "oks_fee",
        "title": "Оплатить абонентскую плату ОКС",
        "category": "services",
        "day_start": 27, "day_end": 30,
        "needs_amount": 0,
        "amount_field": "", "priority": "normal",
        "description": "Внести абонентскую плату ОКС — срок до 30 числа "
                       "(в феврале — последний день месяца). Напоминания "
                       "начинаются с 27 числа.",
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
    note         TEXT NOT NULL DEFAULT '',        -- комментарий председателя
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
    kind           TEXT NOT NULL DEFAULT 'verification',  -- поверка или гарантия
    last_verified  TEXT NOT NULL DEFAULT '',      -- поверка / ввод в эксплуатацию
    interval_years INTEGER NOT NULL DEFAULT 4,    -- интервал поверки или гарантии
    lead_days      INTEGER NOT NULL DEFAULT 180,  -- за сколько дней напоминать
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

-- Памятки Домоведа. Тексты живут в файлах content/faq/*.md и загружаются
-- при старте бота — править их удобнее в редакторе, чем в переписке.
CREATE TABLE IF NOT EXISTS faq (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    code        TEXT NOT NULL UNIQUE,          -- имя файла без расширения
    title       TEXT NOT NULL,
    category    TEXT NOT NULL DEFAULT 'other',
    keywords    TEXT NOT NULL DEFAULT '',      -- через запятую, для поиска
    body        TEXT NOT NULL DEFAULT '',
    image       TEXT NOT NULL DEFAULT '',      -- файл в content/faq/images/
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_active   INTEGER NOT NULL DEFAULT 1,
    updated_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Вопросы, на которые Домовед не нашёл ответа. Главный источник новых
-- памяток: раз в неделю смотрим, о чём спрашивали, и дописываем.
CREATE TABLE IF NOT EXISTS faq_gaps (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id       INTEGER,
    apartment   TEXT NOT NULL DEFAULT '',
    question    TEXT NOT NULL,
    answered    INTEGER NOT NULL DEFAULT 0,    -- 1 — памятка уже написана
    created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- Что планировщик уже сделал за сутки. Раньше это помнилось только в памяти
-- процесса, и после перезапуска бота 20 числа объявление о завершении сбора
-- уходило в чат заново — жители получали его по три раза.
CREATE TABLE IF NOT EXISTS scheduler_log (
    key        TEXT PRIMARY KEY,        -- 'announce:2026-08-20'
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
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
