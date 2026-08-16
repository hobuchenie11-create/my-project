# Graph Report - my-project  (2026-08-16)

## Corpus Check
- 77 files · ~33,876 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 831 nodes · 2214 edges · 43 communities (42 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `589ff9ae`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- reading_service.py
- repository.py
- report_service.py
- workbook.py
- demo.py
- get_apartment_by_number
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
- task_service.py
- CLAUDE.md
- save_parsed_readings
- task_line
- date
- main.py
- parse_message
- models.py
- reminder_service.py
- Регламент сбора 15–19 числа
- save_reading
- test_statements.py
- parser.py
- build_debtors_statement
- receipt_text

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
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_workbook()` --calls--> `generate_workbook()`  [EXTRACTED]
  bot/handlers/admin.py → excel/workbook.py
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

## Communities (43 total, 1 thin omitted)

### Community 0 - "reading_service.py"
Cohesion: 0.19
Nodes (22): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc(), send_invite() (+14 more)

### Community 1 - "repository.py"
Cohesion: 0.05
Nodes (74): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+66 more)

### Community 2 - "report_service.py"
Cohesion: 0.21
Nodes (10): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, fill_statement_sheet(), Выгрузка ведомости передачи показаний в Excel (.xlsx)., Заполняет готовый лист ведомостью — используется и в отдельном файле, и как…, Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждом листе., _setup_print() (+2 more)

### Community 3 - "workbook.py"
Cohesion: 0.16
Nodes (25): Лист «Реестр квартир»: квартира + житель + последняя передача., registry_rows(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label(), status_fill(), style_header() (+17 more)

### Community 4 - "demo.py"
Cohesion: 0.31
Nodes (9): late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary() (+1 more)

### Community 5 - "get_apartment_by_number"
Cohesion: 0.29
Nodes (12): create_user(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), test_debtors_statement(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets() (+4 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.06
Nodes (42): Реестр квартир, complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), CheckResult, parse_amount(), parse_value() (+34 more)

### Community 8 - "test_council.py"
Cohesion: 0.11
Nodes (18): council_candidates(), Row, Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture (+10 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.08
Nodes (39): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+31 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.06
Nodes (74): status_label(), get_task(), log_task_event(), DataValidation, export_year_plan(), _fmt(), _hide_service_column(), _list_validation() (+66 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (68): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+60 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (41): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+33 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.16
Nodes (14): _clamp_day(), ensure_templates(), generate_year(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task() (+6 more)

### Community 25 - "init_db"
Cohesion: 0.12
Nodes (22): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), Приводит набор приборов квартиры к заданному: нужные — активны, лишние — нет., set_meters() (+14 more)

### Community 26 - "scheduler.py"
Cohesion: 0.18
Nodes (18): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+10 more)

### Community 27 - "group.py"
Cohesion: 0.21
Nodes (14): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+6 more)

### Community 28 - "task_service.py"
Cohesion: 0.21
Nodes (12): council_digest(), _digest_text(), _fmt_date(), _month_period(), month_plan_text(), period_title(), Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —… (+4 more)

### Community 30 - "save_parsed_readings"
Cohesion: 0.16
Nodes (14): ParsedReadings, _check_hws_total(), Итог записи показаний из одного сообщения (общий чат)., Раскладывает распознанные показания на приборы конкретной квартиры. Один…, _resolve_meter_kind(), save_parsed_readings(), SaveOutcome, conn() (+6 more)

### Community 31 - "task_line"
Cohesion: 0.19
Nodes (15): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), one_off_text(), Одна строка задачи для списка в боте., Разовые задачи председателя — то, что он планирует сам. (+7 more)

### Community 32 - "date"
Cohesion: 0.16
Nodes (7): date, Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., Просроченные и текущие задачи — то, чем заняться сейчас., TaskView, urgent_text(), view()

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.15
Nodes (22): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., test_apartment_number_without_space(), test_comma_inside_a_number_is_not_a_separator(), test_comma_separators_and_carry_context() (+14 more)

### Community 35 - "models.py"
Cohesion: 0.15
Nodes (19): apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template() (+11 more)

### Community 36 - "reminder_service.py"
Cohesion: 0.32
Nodes (7): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 37 - "Регламент сбора 15–19 числа"
Cohesion: 0.29
Nodes (8): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Книга Excel из 5 листов

### Community 38 - "save_reading"
Cohesion: 0.24
Nodes (14): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note(), test_late_reading_marked_in_statement() (+6 more)

### Community 39 - "test_statements.py"
Cohesion: 0.19
Nodes (12): export_statement(), Path, Отдельный файл ведомости — его председатель отправляет ресурсникам., db(), fixture, Печатные ведомости: для ресурсоснабжающих организаций и непередавших., В доме на 80 квартир ведомость печатается на двух листах: на первом — нежилые,…, Длинное примечание должно переноситься внутри колонки, иначе при печати оно… (+4 more)

### Community 40 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 41 - "build_debtors_statement"
Cohesion: 0.39
Nodes (7): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short()

### Community 42 - "receipt_text"
Cohesion: 0.50
Nodes (5): _display(), datetime, Row, Квитанция-подтверждение после передачи показаний (Этап 5)., receipt_text()

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `reading_service.py`, `repository.py`, `models.py`, `demo.py`, `workbook.py`, `get_apartment_by_number`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `build_debtors_statement`, `test_statements.py`, `test_verification.py`, `init_db`, `scheduler.py`, `group.py`, `save_parsed_readings`, `task_line`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `demo.py`, `get_apartment_by_number`, `save_reading`, `test_amounts.py`, `parser.py`, `group.py`, `save_parsed_readings`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `demo.py`, `get_apartment_by_number`, `save_reading`, `test_amounts.py`, `test_council.py`, `test_statements.py`, `generate_tasks`, `connect`, `tasks_import.py`, `test_verification.py`, `save_parsed_readings`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.053554040895813046 - nodes in this community are weakly interconnected._
- **Should `test_amounts.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06382978723404255 - nodes in this community are weakly interconnected._
- **Should `test_council.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11462450592885376 - nodes in this community are weakly interconnected._