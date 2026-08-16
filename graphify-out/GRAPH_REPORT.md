# Graph Report - my-project  (2026-08-16)

## Corpus Check
- 74 files · ~32,084 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 777 nodes · 2084 edges · 40 communities (39 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `374ecdd4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- build_statement
- workbook.py
- parse_message
- get_apartment_by_number
- generate_tasks
- netcheck.py
- test_council.py
- handlers/registration.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- models.py
- save_reading
- SaveOutcome
- council_digest
- CLAUDE.md
- reading_service.py
- task_service.py
- TaskView
- main.py
- tasks_export.py
- parse_value
- init_db
- handlers/readings.py
- main_menu
- Проверка показаний

## God Nodes (most connected - your core abstractions)
1. `connect()` - 59 edges
2. `parse_message()` - 33 edges
3. `init_db()` - 31 edges
4. `current_period()` - 29 edges
5. `build_statement()` - 29 edges
6. `generate_tasks()` - 29 edges
7. `save_reading()` - 27 edges
8. `get_apartment_by_number()` - 27 edges
9. `save_parsed_readings()` - 26 edges
10. `export_year_plan()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_debtors()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_users()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_users()` --calls--> `list_users()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (40 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.05
Nodes (71): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+63 more)

### Community 1 - "repository.py"
Cohesion: 0.09
Nodes (46): last_reading_value(), active_task_templates(), add_reading(), add_verification(), all_readings(), apartments_submitted(), _apply_migrations(), create_schema() (+38 more)

### Community 2 - "build_statement"
Cohesion: 0.11
Nodes (27): build_statement(), Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx). (+19 more)

### Community 3 - "workbook.py"
Cohesion: 0.19
Nodes (21): Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label(), status_fill(), style_header(), build_workbook(), _current_by_apartment() (+13 more)

### Community 4 - "parse_message"
Cohesion: 0.05
Nodes (53): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., _dm(), _guidance() (+45 more)

### Community 5 - "get_apartment_by_number"
Cohesion: 0.19
Nodes (20): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), create_user(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры. (+12 more)

### Community 6 - "generate_tasks"
Cohesion: 0.16
Nodes (23): generate_tasks(), Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей. (+15 more)

### Community 7 - "netcheck.py"
Cohesion: 0.18
Nodes (15): check(), _port_open(), Подбор рабочего прокси для подключения к Telegram. Запуск: python -m…, _try_http(), _try_socks(), build_socks_connector(), make_session(), normalize_proxy_url() (+7 more)

### Community 8 - "test_council.py"
Cohesion: 0.16
Nodes (10): conn(), FakeBot, FakeMessage, fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., test_digest_goes_to_the_council_chat() (+2 more)

### Community 9 - "handlers/registration.py"
Cohesion: 0.21
Nodes (13): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), find_apartment() (+5 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., update_task(), export_year_plan(), Path, _category_code() (+54 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (70): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+62 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 25 - "models.py"
Cohesion: 0.15
Nodes (19): apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template() (+11 more)

### Community 26 - "save_reading"
Cohesion: 0.33
Nodes (8): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), conn(), fixture, test_save_and_last_reading(), test_statement_single_apartment(), test_statement_split_apartment(), test_submitted_set()

### Community 27 - "SaveOutcome"
Cohesion: 0.50
Nodes (3): _check_hws_total(), Итог записи показаний из одного сообщения (общий чат)., SaveOutcome

### Community 28 - "council_digest"
Cohesion: 0.21
Nodes (13): complete_task(), council_candidates(), council_digest(), _month_period(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка., _one_off() (+5 more)

### Community 30 - "reading_service.py"
Cohesion: 0.20
Nodes (16): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), _display(), history_text(), my_last_readings_text() (+8 more)

### Community 31 - "task_service.py"
Cohesion: 0.14
Nodes (27): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title(), Connection (+19 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "main.py"
Cohesion: 0.15
Nodes (17): allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята., Возвращает обычное поведение — вызывается при остановке бота., _apply_registry_if_present(), _log_chats(), main() (+9 more)

### Community 34 - "tasks_export.py"
Cohesion: 0.23
Nodes (15): category_label(), DataValidation, _fmt(), _hide_service_column(), _list_validation(), Connection, Годовой план задач председателя в Excel. Лист «Годовой план» — все задачи года…, Разовые задачи председателя — то, что он планирует сам. (+7 more)

### Community 35 - "parse_value"
Cohesion: 0.20
Nodes (14): check_reading(), CheckResult, parse_value(), Проверка вводимых показаний., Сверяет новое показание с предыдущим. Меньше предыдущего — ошибка (замену…, Разбирает число из текста пользователя (принимает запятую и точку)., Вопрос посреди передачи показаний должен распознаваться как вопрос., test_first_reading_always_ok() (+6 more)

### Community 36 - "init_db"
Cohesion: 0.20
Nodes (14): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), Приводит набор приборов квартиры к заданному: нужные — активны, лишние — нет., set_meters() (+6 more)

### Community 37 - "handlers/readings.py"
Cohesion: 0.29
Nodes (12): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+4 more)

### Community 38 - "main_menu"
Cohesion: 0.25
Nodes (9): cmd_start(), FSMContext, message, Команда /start и справка., show_help(), cancel_keyboard(), main_menu(), ReplyKeyboardMarkup (+1 more)

### Community 39 - "Проверка показаний"
Cohesion: 0.40
Nodes (5): Реестр квартир, Правило суммы ГВС, Приём показаний через бота, Планировка приборов учёта, Проверка показаний

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `build_statement`, `parse_message`, `handlers/readings.py`, `main_menu`, `init_db`, `test_council.py`, `handlers/registration.py`, `tasks_import.py`, `get_apartment_by_number`, `test_verification.py`, `models.py`, `save_reading`, `reading_service.py`, `task_service.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `build_statement`, `parse_message`, `get_apartment_by_number`, `generate_tasks`, `test_council.py`, `tasks_import.py`, `connect`, `test_verification.py`, `save_reading`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `build_statement`, `parse_value`, `get_apartment_by_number`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05427905427905428 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08973172987974098 - nodes in this community are weakly interconnected._
- **Should `build_statement` be split into smaller, more focused modules?**
  _Cohesion score 0.10984848484848485 - nodes in this community are weakly interconnected._