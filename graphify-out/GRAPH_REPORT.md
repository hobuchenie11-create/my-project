# Graph Report - my-project  (2026-08-11)

## Corpus Check
- 72 files · ~31,630 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 767 nodes · 2065 edges · 34 communities (33 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `425b993b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- init_db
- workbook.py
- parse_message
- get_apartment_by_number
- generate_tasks
- config.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- import_registry
- save_reading
- reading_service.py
- task_service.py
- CLAUDE.md
- group.py
- task_line
- TaskView
- save_parsed_readings

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

## Communities (34 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.06
Nodes (63): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+55 more)

### Community 1 - "repository.py"
Cohesion: 0.07
Nodes (57): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+49 more)

### Community 2 - "init_db"
Cohesion: 0.07
Nodes (45): build_statement(), Connection, Statement, StatementRow, late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text() (+37 more)

### Community 3 - "workbook.py"
Cohesion: 0.10
Nodes (41): category_label(), status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+33 more)

### Community 4 - "parse_message"
Cohesion: 0.21
Nodes (16): _normalize(), parse_message(), Убирает разделители, оставляя только буквы, для сопоставления по словарю., Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., test_comma_separators_and_carry_context(), test_dotted_abbrev_full(), test_gas_ignored_and_room_temperature_words(), test_leading_zeros() (+8 more)

### Community 5 - "get_apartment_by_number"
Cohesion: 0.25
Nodes (14): create_user(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), test_debtors_statement(), _build(), conn(), fixture, Книга Excel «Сбор показаний»: состав листов и наполнение. (+6 more)

### Community 6 - "generate_tasks"
Cohesion: 0.16
Nodes (24): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей. (+16 more)

### Community 7 - "config.py"
Cohesion: 0.08
Nodes (32): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., _apply_registry_if_present(), _log_chats() (+24 more)

### Community 8 - "test_council.py"
Cohesion: 0.12
Nodes (17): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+9 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (51): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+43 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., update_task(), export_year_plan(), Path, _category_code() (+54 more)

### Community 11 - "connect"
Cohesion: 0.07
Nodes (67): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+59 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.15
Nodes (15): complete_task(), ensure_templates(), generate_year(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., set_status() (+7 more)

### Community 25 - "import_registry"
Cohesion: 0.11
Nodes (24): Реестр квартир, layout_label(), Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number() (+16 more)

### Community 26 - "save_reading"
Cohesion: 0.16
Nodes (18): is_late(), Показание передано после срока сбора? Сбор идёт с READINGS_DAY_START по…, Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), Создание схемы БД и первичное заполнение реестра квартир. Запускается…, apartment_meters(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте. (+10 more)

### Community 27 - "reading_service.py"
Cohesion: 0.17
Nodes (12): _classify(), _has(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, _check_hws_total(), Сохранение и просмотр показаний., Итог записи показаний из одного сообщения (общий чат). (+4 more)

### Community 28 - "task_service.py"
Cohesion: 0.20
Nodes (14): _clamp_day(), council_digest(), _digest_text(), _month_period(), month_plan_text(), period_title(), date, Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные… (+6 more)

### Community 30 - "group.py"
Cohesion: 0.22
Nodes (14): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+6 more)

### Community 31 - "task_line"
Cohesion: 0.22
Nodes (13): _fmt_date(), one_off_text(), Row, Одна строка задачи для списка в боте., Просроченные и текущие задачи — то, чем заняться сейчас., Разовые задачи председателя — то, что он планирует сам., task_line(), urgent_text() (+5 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "save_parsed_readings"
Cohesion: 0.29
Nodes (9): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., test_compact_apartment_rejects_split(), test_compact_apartment_single(), test_full_apartment_split() (+1 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `init_db`, `save_parsed_readings`, `get_apartment_by_number`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `test_verification.py`, `import_registry`, `group.py`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `save_parsed_readings`, `init_db`, `get_apartment_by_number`, `handlers/readings.py`, `save_reading`, `reading_service.py`, `group.py`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `repository.py`, `save_parsed_readings`, `get_apartment_by_number`, `generate_tasks`, `config.py`, `test_council.py`, `tasks_import.py`, `connect`, `test_verification.py`, `save_reading`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.061971830985915494 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07247223845704266 - nodes in this community are weakly interconnected._
- **Should `init_db` be split into smaller, more focused modules?**
  _Cohesion score 0.06787330316742081 - nodes in this community are weakly interconnected._