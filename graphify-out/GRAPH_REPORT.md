# Graph Report - my-project  (2026-08-11)

## Corpus Check
- 71 files · ~29,566 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 714 nodes · 1919 edges · 30 communities (29 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `75984221`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- build_statement
- workbook.py
- parse_message
- reading_service.py
- task_service.py
- netcheck.py
- group.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- demo.py
- parser.py
- save_parsed_readings
- test_workbook.py
- common.py
- CLAUDE.md

## God Nodes (most connected - your core abstractions)
1. `connect()` - 56 edges
2. `parse_message()` - 33 edges
3. `current_period()` - 29 edges
4. `build_statement()` - 29 edges
5. `init_db()` - 29 edges
6. `generate_tasks()` - 28 edges
7. `save_reading()` - 27 edges
8. `get_apartment_by_number()` - 27 edges
9. `save_parsed_readings()` - 26 edges
10. `period_title()` - 23 edges

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
Nodes (66): Bot, Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors() (+58 more)

### Community 1 - "repository.py"
Cohesion: 0.09
Nodes (46): active_task_templates(), add_reading(), add_verification(), all_readings(), apartments_submitted(), _apply_migrations(), create_schema(), create_task() (+38 more)

### Community 2 - "build_statement"
Cohesion: 0.06
Nodes (71): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+63 more)

### Community 3 - "workbook.py"
Cohesion: 0.11
Nodes (34): Панель председателя, Регламент сбора 15–19 числа, current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), Цветовая схема DH OS, Модуль «Сбор показаний» (+26 more)

### Community 4 - "parse_message"
Cohesion: 0.25
Nodes (14): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., test_comma_separators_and_carry_context(), test_dotted_abbrev_full(), test_gas_ignored_and_room_temperature_words(), test_leading_zeros(), test_nonresidential(), test_ordinary_chat_message_ignored() (+6 more)

### Community 5 - "reading_service.py"
Cohesion: 0.14
Nodes (21): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), ParsedReadings, _check_hws_total(), _display() (+13 more)

### Community 6 - "task_service.py"
Cohesion: 0.06
Nodes (64): _clamp_day(), complete_task(), council_digest(), ensure_templates(), _fmt_date(), generate_tasks(), generate_year(), _month_period() (+56 more)

### Community 7 - "netcheck.py"
Cohesion: 0.18
Nodes (15): check(), _port_open(), Подбор рабочего прокси для подключения к Telegram. Запуск: python -m…, _try_http(), _try_socks(), build_socks_connector(), make_session(), normalize_proxy_url() (+7 more)

### Community 8 - "group.py"
Cohesion: 0.21
Nodes (14): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+6 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.05
Nodes (57): Реестр квартир, _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message (+49 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.06
Nodes (67): category_label(), status_label(), get_task(), log_task_event(), DataValidation, export_year_plan(), _fmt(), _hide_service_column() (+59 more)

### Community 11 - "connect"
Cohesion: 0.07
Nodes (56): back_to_admin(), change_task_status(), import_plan_file(), import_plan_hint(), meter_action(), meter_interval(), new_task_category(), new_task_due() (+48 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (41): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+33 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "demo.py"
Cohesion: 0.31
Nodes (9): late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary() (+1 more)

### Community 25 - "parser.py"
Cohesion: 0.22
Nodes (9): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., Приём показаний из общего чата, Словарь распознавания показаний (+1 more)

### Community 26 - "save_parsed_readings"
Cohesion: 0.29
Nodes (9): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., test_compact_apartment_rejects_split(), test_compact_apartment_single(), test_full_apartment_split() (+1 more)

### Community 27 - "test_workbook.py"
Cohesion: 0.36
Nodes (9): create_user(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted() (+1 more)

### Community 28 - "common.py"
Cohesion: 0.40
Nodes (4): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID текущего чата — нужен для настройки GROUP_CHAT_ID в .env.

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `build_statement`, `reading_service.py`, `group.py`, `handlers/readings.py`, `tasks_import.py`, `test_verification.py`, `demo.py`, `save_parsed_readings`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `build_statement`, `reading_service.py`, `group.py`, `handlers/readings.py`, `demo.py`, `parser.py`, `save_parsed_readings`, `test_workbook.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `init_db()` connect `build_statement` to `admin.py`, `repository.py`, `task_service.py`, `tasks_import.py`, `connect`, `test_verification.py`, `demo.py`, `save_parsed_readings`, `test_workbook.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.056943056943056944 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08973172987974098 - nodes in this community are weakly interconnected._
- **Should `build_statement` be split into smaller, more focused modules?**
  _Cohesion score 0.05555555555555555 - nodes in this community are weakly interconnected._