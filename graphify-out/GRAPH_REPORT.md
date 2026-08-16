# Graph Report - my-project  (2026-08-16)

## Corpus Check
- 75 files · ~32,931 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 807 nodes · 2149 edges · 40 communities (39 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `185abfcf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- reading_service.py
- workbook.py
- demo.py
- test_workbook.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- init_db
- scheduler.py
- group.py
- council_digest
- CLAUDE.md
- get_apartment_by_number
- task_service.py
- TaskView
- main.py
- parse_message
- config.py
- reminder_service.py
- Ведомость для ресурсоснабжающих организаций
- SaveOutcome
- parser.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 60 edges
2. `parse_message()` - 38 edges
3. `init_db()` - 33 edges
4. `generate_tasks()` - 30 edges
5. `current_period()` - 29 edges
6. `build_statement()` - 29 edges
7. `save_reading()` - 27 edges
8. `get_apartment_by_number()` - 27 edges
9. `save_parsed_readings()` - 26 edges
10. `export_year_plan()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_statement()` --calls--> `generate_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/monthly_statement.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_debtors()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_debtors_doc()` --calls--> `generate_debtors_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/debtors_statement.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (40 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.20
Nodes (20): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc(), send_invite() (+12 more)

### Community 1 - "repository.py"
Cohesion: 0.09
Nodes (49): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+41 more)

### Community 2 - "reading_service.py"
Cohesion: 0.29
Nodes (7): period_title(), Сохранение и просмотр показаний., generate_statement(), Path, Формирование месячной ведомости в Excel. Из кода: generate_statement(period) ->…, print_statement(), Текстовая (печатная) версия ведомости для быстрого просмотра в консоли. Запуск:…

### Community 3 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 4 - "demo.py"
Cohesion: 0.17
Nodes (17): late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary() (+9 more)

### Community 5 - "test_workbook.py"
Cohesion: 0.36
Nodes (9): create_user(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted() (+1 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.07
Nodes (39): Реестр квартир, Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит… (+31 more)

### Community 8 - "test_council.py"
Cohesion: 0.12
Nodes (17): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+9 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.08
Nodes (37): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+29 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., update_task(), export_year_plan(), Path, _category_code() (+54 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (70): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+62 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (41): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+33 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.14
Nodes (15): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), Подтягивает в задачи изменения шаблонов (название, категория, приоритет).… (+7 more)

### Community 25 - "init_db"
Cohesion: 0.05
Nodes (72): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+64 more)

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "group.py"
Cohesion: 0.17
Nodes (17): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+9 more)

### Community 28 - "council_digest"
Cohesion: 0.27
Nodes (10): complete_task(), council_digest(), _month_period(), Connection, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, set_status(), open_tasks() (+2 more)

### Community 30 - "get_apartment_by_number"
Cohesion: 0.23
Nodes (14): _display(), Row, Раскладывает распознанные показания на приборы конкретной квартиры. Один…, _resolve_meter_kind(), save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn() (+6 more)

### Community 31 - "task_service.py"
Cohesion: 0.17
Nodes (21): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title() (+13 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.15
Nodes (22): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., test_apartment_number_without_space(), test_comma_inside_a_number_is_not_a_separator(), test_comma_separators_and_carry_context() (+14 more)

### Community 35 - "config.py"
Cohesion: 0.22
Nodes (6): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии.

### Community 36 - "reminder_service.py"
Cohesion: 0.32
Nodes (7): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 37 - "Ведомость для ресурсоснабжающих организаций"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

### Community 38 - "SaveOutcome"
Cohesion: 0.33
Nodes (4): ParsedReadings, _check_hws_total(), Итог записи показаний из одного сообщения (общий чат)., SaveOutcome

### Community 40 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `reading_service.py`, `demo.py`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `test_verification.py`, `init_db`, `scheduler.py`, `group.py`, `get_apartment_by_number`, `task_service.py`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `demo.py`, `test_workbook.py`, `SaveOutcome`, `test_amounts.py`, `parser.py`, `init_db`, `group.py`, `get_apartment_by_number`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `demo.py`, `test_workbook.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `tasks_import.py`, `connect`, `test_verification.py`, `get_apartment_by_number`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08549019607843138 - nodes in this community are weakly interconnected._
- **Should `workbook.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09634551495016612 - nodes in this community are weakly interconnected._
- **Should `test_amounts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06765327695560254 - nodes in this community are weakly interconnected._