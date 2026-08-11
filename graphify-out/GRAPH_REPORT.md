# Graph Report - my-project  (2026-08-11)

## Corpus Check
- 71 files · ~30,136 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 724 nodes · 1959 edges · 24 communities (23 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `617ac759`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connect
- repository.py
- build_statement
- workbook.py
- parse_message
- handlers/registration.py
- task_service.py
- config.py
- reading_service.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
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
10. `export_year_plan()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `Проверка показаний` --checks--> `Правило суммы ГВС`  [INFERRED]
  README.md → docs/templates.md
- `show_users()` --calls--> `list_users()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_backup()` --calls--> `log_event()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `handle_group_message()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py
- `handle_group_message()` --calls--> `get_apartment_by_id()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (24 total, 1 thin omitted)

### Community 0 - "connect"
Cohesion: 0.06
Nodes (68): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+60 more)

### Community 1 - "repository.py"
Cohesion: 0.08
Nodes (53): Connection, Текстовый реестр квартир с отметкой о сдаче показаний за период., registry_summary(), active_task_templates(), add_reading(), add_verification(), all_readings(), apartments_submitted() (+45 more)

### Community 2 - "build_statement"
Cohesion: 0.06
Nodes (72): Проверяет и сохраняет одно показание. Возвращает результат проверки., Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement (+64 more)

### Community 3 - "workbook.py"
Cohesion: 0.11
Nodes (36): status_label(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label(), status_fill(), style_header() (+28 more)

### Community 4 - "parse_message"
Cohesion: 0.08
Nodes (41): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+33 more)

### Community 5 - "handlers/registration.py"
Cohesion: 0.19
Nodes (14): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+6 more)

### Community 6 - "task_service.py"
Cohesion: 0.05
Nodes (73): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), Кнопки под конкретной задачей., task_actions(), category_label(), _clamp_day() (+65 more)

### Community 7 - "config.py"
Cohesion: 0.05
Nodes (48): Реестр квартир, Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID текущего чата — нужен для настройки GROUP_CHAT_ID в .env., _apply_registry_if_present() (+40 more)

### Community 9 - "reading_service.py"
Cohesion: 0.05
Nodes (62): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+54 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.08
Nodes (60): get_task(), log_task_event(), update_task(), export_year_plan(), Path, _category_code(), _clean(), _create_one_off() (+52 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.08
Nodes (46): back_to_admin(), change_task_status(), import_plan_file(), import_plan_hint(), meter_action(), meter_interval(), new_task_category(), new_task_due() (+38 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `repository.py`, `build_statement`, `parse_message`, `handlers/registration.py`, `task_service.py`, `config.py`, `reading_service.py`, `tasks_import.py`, `handlers/tasks.py`, `test_verification.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `reading_service.py`, `build_statement`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `init_db()` connect `build_statement` to `connect`, `repository.py`, `parse_message`, `task_service.py`, `config.py`, `tasks_import.py`, `test_verification.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `connect` be split into smaller, more focused modules?**
  _Cohesion score 0.062342342342342344 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07617051013277429 - nodes in this community are weakly interconnected._
- **Should `build_statement` be split into smaller, more focused modules?**
  _Cohesion score 0.059319482083709726 - nodes in this community are weakly interconnected._