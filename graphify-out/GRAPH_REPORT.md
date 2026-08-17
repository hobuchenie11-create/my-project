# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 79 files · ~35,976 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 894 nodes · 2341 edges · 40 communities (39 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `994557c3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- save_reading
- export_year_plan
- models.py
- build_statement
- generate_tasks
- reading_service.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- demo.py
- scheduler.py
- group.py
- TaskView
- CLAUDE.md
- build_debtors_statement
- generate_statement
- task_service.py
- main.py
- parse_message
- init_db
- workbook.py
- reminder_service.py
- get_apartment_by_number
- test_cleanup.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 64 edges
2. `parse_message()` - 46 edges
3. `init_db()` - 37 edges
4. `get_apartment_by_number()` - 34 edges
5. `save_parsed_readings()` - 31 edges
6. `generate_tasks()` - 30 edges
7. `current_period()` - 29 edges
8. `save_reading()` - 29 edges
9. `build_statement()` - 29 edges
10. `export_year_plan()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_default_house_meters()` --calls--> `house_meters()`  [EXTRACTED]
  tests/test_verification.py → database/repository.py
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_statement()` --calls--> `generate_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/monthly_statement.py
- `send_workbook()` --calls--> `generate_workbook()`  [EXTRACTED]
  bot/handlers/admin.py → excel/workbook.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (40 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.14
Nodes (27): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., remind_debtors(), send_backup() (+19 more)

### Community 1 - "repository.py"
Cohesion: 0.08
Nodes (53): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+45 more)

### Community 2 - "save_reading"
Cohesion: 0.17
Nodes (14): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), conn(), fixture, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note(), test_late_reading_marked_in_statement(), test_reading_in_time_has_no_note() (+6 more)

### Community 3 - "export_year_plan"
Cohesion: 0.10
Nodes (44): category_label(), status_label(), get_task(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., DataValidation, export_year_plan(), _fmt() (+36 more)

### Community 4 - "models.py"
Cohesion: 0.16
Nodes (17): layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number() (+9 more)

### Community 5 - "build_statement"
Cohesion: 0.13
Nodes (24): build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text(), export_statement(), fill_statement_sheet() (+16 more)

### Community 6 - "generate_tasks"
Cohesion: 0.14
Nodes (27): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), set_status(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title() (+19 more)

### Community 7 - "reading_service.py"
Cohesion: 0.06
Nodes (43): _check_hws_total(), _check_total(), _display(), _fold_totals(), datetime, Row, Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка… (+35 more)

### Community 8 - "test_council.py"
Cohesion: 0.10
Nodes (22): council_digest(), _month_period(), Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, create_task(), conn(), FakeBot, FakeMessage, _one_off() (+14 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (49): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+41 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.13
Nodes (34): log_task_event(), update_task(), _category_code(), _clean(), _create_one_off(), _header_map(), _import_meters(), _import_one_off() (+26 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (76): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+68 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (40): add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due(), Connection, date (+32 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.18
Nodes (11): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., Разовые задачи — на отдельном листе, с автоматическим отсчётом срока., test_generate_year_covers_twelve_months() (+3 more)

### Community 25 - "demo.py"
Cohesion: 0.48
Nodes (6): welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "group.py"
Cohesion: 0.05
Nodes (48): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+40 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "build_debtors_statement"
Cohesion: 0.39
Nodes (7): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short()

### Community 31 - "generate_statement"
Cohesion: 0.33
Nodes (6): save_report(), generate_workbook(), Path, Собирает книгу из базы и возвращает путь к файлу., generate_statement(), Path

### Community 32 - "task_service.py"
Cohesion: 0.16
Nodes (23): complete_task(), council_candidates(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title(), Connection (+15 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.08
Nodes (38): _classify(), _has(), _normalize(), parse_message(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю. (+30 more)

### Community 36 - "init_db"
Cohesion: 0.18
Nodes (18): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), Список приборов квартиры в порядке опроса в боте. (+10 more)

### Community 37 - "workbook.py"
Cohesion: 0.17
Nodes (24): current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label() (+16 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.19
Nodes (12): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget, Панель председателя (+4 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.17
Nodes (24): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), create_user(), get_apartment_by_number(), db(), fixture, test_late_flag_stored_for_parsed_message(), Раскладка распознанных показаний на приборы конкретной квартиры. (+16 more)

### Community 42 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `save_reading`, `init_db`, `models.py`, `build_statement`, `reading_service.py`, `test_council.py`, `handlers/readings.py`, `test_cleanup.py`, `tasks_import.py`, `get_apartment_by_number`, `test_verification.py`, `demo.py`, `scheduler.py`, `group.py`, `build_debtors_statement`, `generate_statement`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `save_reading`, `reading_service.py`, `test_council.py`, `get_apartment_by_number`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `save_reading`, `export_year_plan`, `build_statement`, `generate_tasks`, `reading_service.py`, `test_council.py`, `get_apartment_by_number`, `test_cleanup.py`, `connect`, `test_verification.py`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07878787878787878 - nodes in this community are weakly interconnected._
- **Should `export_year_plan` be split into smaller, more focused modules?**
  _Cohesion score 0.09565217391304348 - nodes in this community are weakly interconnected._