# Graph Report - my-project  (2026-08-11)

## Corpus Check
- 72 files · ~30,727 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 742 nodes · 1993 edges · 30 communities (29 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `023fcd34`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connect
- Connection
- build_statement
- workbook.py
- parse_message
- get_apartment_by_number
- task_service.py
- config.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- export_year_plan
- init_db
- save_reading
- reading_service.py
- repository.py
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `connect()` - 57 edges
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
- `show_users()` --calls--> `list_users()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_backup()` --calls--> `log_event()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `handle_group_message()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py
- `handle_group_message()` --calls--> `get_apartment_by_id()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py
- `handle_group_message()` --calls--> `get_apartment_by_number()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (30 total, 1 thin omitted)

### Community 0 - "connect"
Cohesion: 0.06
Nodes (76): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+68 more)

### Community 1 - "Connection"
Cohesion: 0.10
Nodes (33): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), _display(), history_text(), my_last_readings_text() (+25 more)

### Community 2 - "build_statement"
Cohesion: 0.14
Nodes (22): build_statement(), Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx). (+14 more)

### Community 3 - "workbook.py"
Cohesion: 0.09
Nodes (43): Панель председателя, current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Цветовая схема DH OS, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+35 more)

### Community 4 - "parse_message"
Cohesion: 0.07
Nodes (44): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+36 more)

### Community 5 - "get_apartment_by_number"
Cohesion: 0.18
Nodes (21): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), create_user(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры. (+13 more)

### Community 6 - "task_service.py"
Cohesion: 0.05
Nodes (69): change_task_status(), Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), Кнопки под конкретной задачей., task_actions(), category_label() (+61 more)

### Community 7 - "config.py"
Cohesion: 0.06
Nodes (46): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., _apply_registry_if_present(), _log_chats() (+38 more)

### Community 8 - "test_council.py"
Cohesion: 0.17
Nodes (11): digest_env(), FakeBot, FakeMessage, fixture, Сводка для Совета дома уходит в свой чат, а не в чат показаний., Чат показаний подключён, чат Совета — нет: в чат жителей не пишем., Обсуждения Совета не разбираются как показания., _run() (+3 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (54): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+46 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.12
Nodes (36): complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка., log_task_event(), update_task(), _category_code(), _clean(), _create_one_off(), _header_map() (+28 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.09
Nodes (41): back_to_admin(), import_plan_file(), import_plan_hint(), meter_action(), new_task_category(), new_task_due(), new_task_start(), new_task_title() (+33 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (45): meter_interval(), open_tasks_menu(), Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text() (+37 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "export_year_plan"
Cohesion: 0.11
Nodes (38): send_year_plan(), generate_year(), Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), get_task(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., task_exists() (+30 more)

### Community 25 - "init_db"
Cohesion: 0.18
Nodes (16): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), Схема базы данных DH OS и справочник видов приборов учета. (+8 more)

### Community 26 - "save_reading"
Cohesion: 0.18
Nodes (14): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), conn(), fixture, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note(), test_late_reading_marked_in_statement(), test_reading_in_time_has_no_note() (+6 more)

### Community 27 - "reading_service.py"
Cohesion: 0.18
Nodes (9): _check_hws_total(), Сохранение и просмотр показаний., Итог записи показаний из одного сообщения (общий чат)., _resolve_meter_kind(), SaveOutcome, Регламент сбора 15–19 числа, Модуль «Сбор показаний», Передача после срока (+1 more)

### Community 28 - "repository.py"
Cohesion: 0.20
Nodes (11): last_reading_value(), add_reading(), _apply_migrations(), create_schema(), ensure_meter(), get_meter(), last_reading(), Доступ к базе данных SQLite. Все запросы проекта собраны здесь. (+3 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `Connection`, `build_statement`, `parse_message`, `get_apartment_by_number`, `task_service.py`, `config.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `handlers/tasks.py`, `test_verification.py`, `export_year_plan`, `init_db`, `save_reading`, `repository.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `connect`, `handlers/readings.py`, `save_reading`, `get_apartment_by_number`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `connect`, `build_statement`, `get_apartment_by_number`, `task_service.py`, `config.py`, `test_council.py`, `test_verification.py`, `export_year_plan`, `save_reading`, `repository.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `connect` be split into smaller, more focused modules?**
  _Cohesion score 0.05671466353217749 - nodes in this community are weakly interconnected._
- **Should `Connection` be split into smaller, more focused modules?**
  _Cohesion score 0.09803921568627451 - nodes in this community are weakly interconnected._
- **Should `build_statement` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._