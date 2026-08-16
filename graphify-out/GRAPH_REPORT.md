# Graph Report - my-project  (2026-08-16)

## Corpus Check
- 77 files · ~34,418 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 841 nodes · 2233 edges · 40 communities (39 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6c532c85`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connect
- repository.py
- test_cleanup.py
- workbook.py
- demo.py
- save_reading
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- test_statements.py
- handlers/registration.py
- reading_service.py
- task_service.py
- CLAUDE.md
- import_registry
- council_digest
- TaskView
- main.py
- parse_message
- init_db
- config.py
- scheduler.py
- Ведомость для ресурсоснабжающих организаций
- reminder_service.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 62 edges
2. `parse_message()` - 38 edges
3. `init_db()` - 35 edges
4. `generate_tasks()` - 30 edges
5. `current_period()` - 29 edges
6. `save_reading()` - 29 edges
7. `build_statement()` - 29 edges
8. `get_apartment_by_number()` - 29 edges
9. `save_parsed_readings()` - 26 edges
10. `export_year_plan()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `send_debtors_doc()` --calls--> `generate_debtors_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/debtors_statement.py
- `show_users()` --calls--> `list_users()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_backup()` --calls--> `make_backup()`  [EXTRACTED]
  bot/handlers/admin.py → database/backup.py
- `send_backup()` --calls--> `log_event()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `handle_group_message()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/group.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (40 total, 1 thin omitted)

### Community 0 - "connect"
Cohesion: 0.15
Nodes (28): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., remind_debtors(), send_backup(), send_chat_reminder() (+20 more)

### Community 1 - "repository.py"
Cohesion: 0.08
Nodes (50): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+42 more)

### Community 2 - "test_cleanup.py"
Cohesion: 0.13
Nodes (25): make_backup(), Path, Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили…, «15.08.2026» или «2026-08-15» -> «2026-08-15 00:00:00» для сравнения. (+17 more)

### Community 3 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 4 - "demo.py"
Cohesion: 0.48
Nodes (6): welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…

### Community 5 - "save_reading"
Cohesion: 0.19
Nodes (21): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), get_apartment_by_number(), parametrize, test_export_statement() (+13 more)

### Community 6 - "generate_tasks"
Cohesion: 0.14
Nodes (25): generate_tasks(), Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), conn(), fixture, Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.06
Nodes (42): Реестр квартир, complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), CheckResult, parse_amount(), parse_value() (+34 more)

### Community 8 - "test_council.py"
Cohesion: 0.09
Nodes (25): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, collection_reminder_text(), _days_word(), date, Короткое напоминание в чат дома: до какого числа передать показания. Дата…, conn(), FakeBot (+17 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.15
Nodes (22): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+14 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (61): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, _category_code(), _clean() (+53 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.06
Nodes (66): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+58 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.22
Nodes (10): _clamp_day(), generate_year(), День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out(), Разовые задачи — на отдельном листе, с автоматическим отсчётом срока., test_generate_year_covers_twelve_months() (+2 more)

### Community 25 - "test_statements.py"
Cohesion: 0.13
Nodes (18): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx)., Отдельный файл ведомости — его председатель отправляет ресурсникам. (+10 more)

### Community 26 - "handlers/registration.py"
Cohesion: 0.16
Nodes (17): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+9 more)

### Community 27 - "reading_service.py"
Cohesion: 0.13
Nodes (22): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+14 more)

### Community 28 - "task_service.py"
Cohesion: 0.14
Nodes (27): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text() (+19 more)

### Community 30 - "import_registry"
Cohesion: 0.21
Nodes (14): _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number(), _pick_sheet(), Connection, Path (+6 more)

### Community 31 - "council_digest"
Cohesion: 0.28
Nodes (9): council_digest(), ensure_templates(), _month_period(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, set_status(), test_council_digest_hides_internal_details() (+1 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (38): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+30 more)

### Community 34 - "parse_message"
Cohesion: 0.07
Nodes (49): _classify(), _has(), _normalize(), parse_message(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю. (+41 more)

### Community 35 - "init_db"
Cohesion: 0.13
Nodes (22): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), layout_label() (+14 more)

### Community 36 - "config.py"
Cohesion: 0.19
Nodes (10): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., Резервное копирование базы данных., build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников. (+2 more)

### Community 37 - "scheduler.py"
Cohesion: 0.27
Nodes (12): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям., send_debtors_statement() (+4 more)

### Community 38 - "Ведомость для ресурсоснабжающих организаций"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.32
Nodes (7): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `repository.py`, `test_cleanup.py`, `demo.py`, `save_reading`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `handlers/tasks.py`, `test_verification.py`, `test_statements.py`, `handlers/registration.py`, `reading_service.py`, `task_service.py`, `import_registry`, `init_db`, `config.py`, `scheduler.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `reading_service.py`, `demo.py`, `save_reading`, `test_amounts.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `connect`, `main.py`, `repository.py`, `test_cleanup.py`, `demo.py`, `save_reading`, `parse_message`, `test_amounts.py`, `test_council.py`, `generate_tasks`, `tasks_import.py`, `test_verification.py`, `test_statements.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08295625942684766 - nodes in this community are weakly interconnected._
- **Should `test_cleanup.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13105413105413105 - nodes in this community are weakly interconnected._
- **Should `workbook.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09634551495016612 - nodes in this community are weakly interconnected._