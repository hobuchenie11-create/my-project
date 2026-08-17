# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 79 files · ~36,215 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 900 nodes · 2351 edges · 41 communities (40 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `65d9ecb5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- save_reading
- export_year_plan
- import_registry
- report_service.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- demo.py
- scheduler.py
- group.py
- date
- CLAUDE.md
- build_debtors_statement
- council_digest
- task_service.py
- main.py
- parse_message
- init_db.py
- connect
- workbook.py
- reminder_service.py
- get_apartment_by_number
- reading_service.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 64 edges
2. `parse_message()` - 50 edges
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

## Communities (41 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.13
Nodes (28): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., remind_debtors(), send_backup() (+20 more)

### Community 1 - "repository.py"
Cohesion: 0.05
Nodes (76): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+68 more)

### Community 2 - "save_reading"
Cohesion: 0.15
Nodes (19): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), print_statement(), Текстовая (печатная) версия ведомости для быстрого просмотра в консоли. Запуск:…, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note(), test_late_reading_marked_in_statement() (+11 more)

### Community 3 - "export_year_plan"
Cohesion: 0.10
Nodes (43): status_label(), get_task(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., DataValidation, export_year_plan(), _fmt(), _hide_service_column() (+35 more)

### Community 4 - "import_registry"
Cohesion: 0.18
Nodes (16): layout_label(), Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number(), _pick_sheet() (+8 more)

### Community 5 - "report_service.py"
Cohesion: 0.15
Nodes (17): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, Регламент сбора 15–19 числа, Модуль «Сбор показаний», export_statement(), fill_statement_sheet(), Path (+9 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.09
Nodes (32): complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний. (+24 more)

### Community 8 - "test_council.py"
Cohesion: 0.19
Nodes (8): FakeBot, FakeMessage, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., test_digest_goes_to_the_council_chat(), test_digest_never_goes_to_the_readings_chat(), test_readings_are_not_collected_in_the_council_chat()

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (47): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+39 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.13
Nodes (33): log_task_event(), _category_code(), _clean(), _create_one_off(), _header_map(), _import_meters(), _import_one_off(), _import_tasks() (+25 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.06
Nodes (70): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+62 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (36): add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due(), Connection, date (+28 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 25 - "demo.py"
Cohesion: 0.48
Nodes (6): welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…

### Community 26 - "scheduler.py"
Cohesion: 0.20
Nodes (18): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+10 more)

### Community 27 - "group.py"
Cohesion: 0.05
Nodes (50): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+42 more)

### Community 28 - "date"
Cohesion: 0.14
Nodes (7): _digest_text(), date, Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., Собирает текст сводки из трёх групп задач., _shift_month(), TaskView

### Community 30 - "build_debtors_statement"
Cohesion: 0.39
Nodes (7): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short()

### Community 31 - "council_digest"
Cohesion: 0.25
Nodes (11): council_candidates(), council_digest(), _month_period(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, _one_off(), Ежемесячный регламент Совету не предлагается — только разовые дела., test_candidates_are_one_off_tasks_only() (+3 more)

### Community 32 - "task_service.py"
Cohesion: 0.18
Nodes (19): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _fmt_date(), month_plan_text(), one_off_text(), period_title(), Connection (+11 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.07
Nodes (44): _classify(), _has(), _normalize(), parse_message(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю. (+36 more)

### Community 35 - "init_db.py"
Cohesion: 0.29
Nodes (7): Создание схемы БД и первичное заполнение реестра квартир. Запускается…, apartment_meters(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте., test_save_and_last_reading(), test_statement_split_apartment(), test_submitted_set()

### Community 36 - "connect"
Cohesion: 0.10
Nodes (30): init_db(), Connection, Path, _seed_nonresidential(), _seed_residential(), connect(), create_user(), Path (+22 more)

### Community 37 - "workbook.py"
Cohesion: 0.15
Nodes (27): current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label() (+19 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.19
Nodes (12): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget, Панель председателя (+4 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.17
Nodes (23): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., «ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор. (+15 more)

### Community 42 - "reading_service.py"
Cohesion: 0.15
Nodes (12): _check_hws_total(), _check_total(), _fold_totals(), Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка…, Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим., Итог записи показаний из одного сообщения (общий чат)., _resolve_meter_kind() (+4 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `task_service.py`, `save_reading`, `import_registry`, `workbook.py`, `report_service.py`, `handlers/readings.py`, `tasks_import.py`, `handlers/tasks.py`, `get_apartment_by_number`, `demo.py`, `scheduler.py`, `group.py`, `build_debtors_statement`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `save_reading`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `init_db()` connect `connect` to `main.py`, `repository.py`, `init_db.py`, `save_reading`, `report_service.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `reading_service.py`, `export_year_plan`, `test_verification.py`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12561576354679804 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.050949367088607596 - nodes in this community are weakly interconnected._
- **Should `export_year_plan` be split into smaller, more focused modules?**
  _Cohesion score 0.09696969696969697 - nodes in this community are weakly interconnected._