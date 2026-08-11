# Graph Report - my-project  (2026-08-11)

## Corpus Check
- 72 files · ~30,654 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 740 nodes · 1990 edges · 30 communities (29 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d59e52dc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- init_db
- workbook.py
- parse_message
- get_apartment_by_number
- task_service.py
- config.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- group.py
- demo.py
- parser.py
- test_workbook.py
- receipt_text
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

## Communities (30 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.06
Nodes (67): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+59 more)

### Community 1 - "repository.py"
Cohesion: 0.07
Nodes (59): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+51 more)

### Community 2 - "init_db"
Cohesion: 0.07
Nodes (52): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+44 more)

### Community 3 - "workbook.py"
Cohesion: 0.11
Nodes (37): category_label(), status_label(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label(), status_fill() (+29 more)

### Community 4 - "parse_message"
Cohesion: 0.25
Nodes (14): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., test_comma_separators_and_carry_context(), test_dotted_abbrev_full(), test_gas_ignored_and_room_temperature_words(), test_leading_zeros(), test_nonresidential(), test_ordinary_chat_message_ignored() (+6 more)

### Community 5 - "get_apartment_by_number"
Cohesion: 0.17
Nodes (16): ParsedReadings, _check_hws_total(), Итог записи показаний из одного сообщения (общий чат)., Раскладывает распознанные показания на приборы конкретной квартиры. Один…, _resolve_meter_kind(), save_parsed_readings(), SaveOutcome, get_apartment_by_number() (+8 more)

### Community 6 - "task_service.py"
Cohesion: 0.06
Nodes (64): _clamp_day(), complete_task(), council_digest(), ensure_templates(), _fmt_date(), generate_tasks(), generate_year(), _month_period() (+56 more)

### Community 7 - "config.py"
Cohesion: 0.06
Nodes (45): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., _apply_registry_if_present(), main() (+37 more)

### Community 8 - "test_council.py"
Cohesion: 0.17
Nodes (11): digest_env(), FakeBot, FakeMessage, fixture, Сводка для Совета дома уходит в свой чат, а не в чат показаний., Чат показаний подключён, чат Совета — нет: в чат жителей не пишем., Обсуждения Совета не разбираются как показания., _run() (+3 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.05
Nodes (58): Реестр квартир, _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message (+50 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.08
Nodes (59): get_task(), log_task_event(), export_year_plan(), Path, _category_code(), _clean(), _create_one_off(), _header_map() (+51 more)

### Community 11 - "connect"
Cohesion: 0.07
Nodes (56): back_to_admin(), change_task_status(), import_plan_file(), import_plan_hint(), meter_action(), meter_interval(), new_task_category(), new_task_due() (+48 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "group.py"
Cohesion: 0.21
Nodes (14): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+6 more)

### Community 25 - "demo.py"
Cohesion: 0.31
Nodes (9): late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary() (+1 more)

### Community 26 - "parser.py"
Cohesion: 0.22
Nodes (9): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., Приём показаний из общего чата, Словарь распознавания показаний (+1 more)

### Community 27 - "test_workbook.py"
Cohesion: 0.36
Nodes (9): create_user(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted() (+1 more)

### Community 28 - "receipt_text"
Cohesion: 0.50
Nodes (5): _display(), datetime, Row, Квитанция-подтверждение после передачи показаний (Этап 5)., receipt_text()

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `init_db`, `get_apartment_by_number`, `config.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `test_verification.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `init_db`, `get_apartment_by_number`, `handlers/readings.py`, `group.py`, `demo.py`, `parser.py`, `test_workbook.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `repository.py`, `get_apartment_by_number`, `task_service.py`, `config.py`, `test_council.py`, `tasks_import.py`, `connect`, `test_verification.py`, `demo.py`, `test_workbook.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06126126126126126 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06994535519125683 - nodes in this community are weakly interconnected._
- **Should `init_db` be split into smaller, more focused modules?**
  _Cohesion score 0.07231638418079096 - nodes in this community are weakly interconnected._