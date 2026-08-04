# Graph Report - .  (2026-08-04)

## Corpus Check
- Corpus is ~15,669 words - fits in a single context window. You may not need a graph.

## Summary
- 408 nodes · 1095 edges · 22 communities
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 32 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Меню председателя
- Просмотр показаний жителем
- Схема базы и реестр квартир
- Книга Excel и оформление
- Раскладка показаний по приборам
- Словарь распознавания сообщений
- Ведомость и запись показаний
- Настройки и служебные команды
- Приём показаний из чата
- Передача показаний в боте
- Регистрация жителя
- Регламент и отчётность (концепции)

## God Nodes (most connected - your core abstractions)
1. `connect()` - 36 edges
2. `parse_message()` - 33 edges
3. `current_period()` - 29 edges
4. `save_reading()` - 26 edges
5. `save_parsed_readings()` - 26 edges
6. `get_apartment_by_number()` - 26 edges
7. `build_statement()` - 25 edges
8. `period_title()` - 22 edges
9. `init_db()` - 22 edges
10. `import_registry()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `send_debtors_doc()` --calls--> `generate_debtors_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/debtors_statement.py
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

## Communities (22 total, 0 thin omitted)

### Community 0 - "Меню председателя"
Cohesion: 0.08
Nodes (51): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+43 more)

### Community 1 - "Просмотр показаний жителем"
Cohesion: 0.10
Nodes (40): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+32 more)

### Community 2 - "Схема базы и реестр квартир"
Cohesion: 0.09
Nodes (36): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), layout_label() (+28 more)

### Community 3 - "Книга Excel и оформление"
Cohesion: 0.11
Nodes (34): welcome_residents_text(), Лист «Реестр квартир»: квартира + житель + последняя передача., registry_rows(), build_demo(), _checklist(), _plain(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+26 more)

### Community 4 - "Раскладка показаний по приборам"
Cohesion: 0.12
Nodes (34): parse_message(), Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), create_user(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture (+26 more)

### Community 5 - "Словарь распознавания сообщений"
Cohesion: 0.09
Nodes (29): _classify(), _has(), _normalize(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., _check_hws_total() (+21 more)

### Community 6 - "Ведомость и запись показаний"
Cohesion: 0.12
Nodes (27): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+19 more)

### Community 7 - "Настройки и служебные команды"
Cohesion: 0.09
Nodes (26): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID текущего чата — нужен для настройки GROUP_CHAT_ID в .env., _apply_registry_if_present(), main() (+18 more)

### Community 8 - "Приём показаний из чата"
Cohesion: 0.11
Nodes (25): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+17 more)

### Community 9 - "Передача показаний в боте"
Cohesion: 0.15
Nodes (21): _ask_next_meter(), cancel_submission(), _finish(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры., start_submission() (+13 more)

### Community 10 - "Регистрация жителя"
Cohesion: 0.16
Nodes (17): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+9 more)

### Community 11 - "Регламент и отчётность (концепции)"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

## Knowledge Gaps
- **1 isolated node(s):** `Config`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `Меню председателя` to `Просмотр показаний жителем`, `Схема базы и реестр квартир`, `Книга Excel и оформление`, `Раскладка показаний по приборам`, `Ведомость и запись показаний`, `Приём показаний из чата`, `Передача показаний в боте`, `Регистрация жителя`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `Раскладка показаний по приборам` to `Приём показаний из чата`, `Книга Excel и оформление`, `Словарь распознавания сообщений`, `Ведомость и запись показаний`?**
  _High betweenness centrality (0.078) - this node is a cross-community bridge._
- **Why does `current_period()` connect `Меню председателя` to `Книга Excel и оформление`, `Словарь распознавания сообщений`, `Ведомость и запись показаний`, `Приём показаний из чата`, `Передача показаний в боте`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **What connects `Config` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Меню председателя` be split into smaller, more focused modules?**
  _Cohesion score 0.08208020050125313 - nodes in this community are weakly interconnected._
- **Should `Просмотр показаний жителем` be split into smaller, more focused modules?**
  _Cohesion score 0.10104529616724739 - nodes in this community are weakly interconnected._
- **Should `Схема базы и реестр квартир` be split into smaller, more focused modules?**
  _Cohesion score 0.08636977058029689 - nodes in this community are weakly interconnected._