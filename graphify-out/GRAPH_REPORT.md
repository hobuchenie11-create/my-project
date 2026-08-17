# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 81 files · ~38,149 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 945 nodes · 2475 edges · 47 communities (45 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `855893dd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- save_reading
- test_common_meters.py
- handlers/readings.py
- build_statement
- generate_tasks
- test_amounts.py
- test_council.py
- test_cleanup.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- demo.py
- current_period
- handle_group_message
- TaskView
- CLAUDE.md
- build_debtors_statement
- init_db
- task_service.py
- config.py
- parse_message
- import_registry
- set_meters
- workbook.py
- council_digest
- reminder_service.py
- test_workbook.py
- get_apartment_by_number
- reading_service.py
- make_backup
- create_schema
- Ведомость непередавших
- touch_user

## God Nodes (most connected - your core abstractions)
1. `connect()` - 71 edges
2. `parse_message()` - 54 edges
3. `init_db()` - 40 edges
4. `get_apartment_by_number()` - 37 edges
5. `current_period()` - 33 edges
6. `save_parsed_readings()` - 33 edges
7. `build_statement()` - 33 edges
8. `generate_tasks()` - 30 edges
9. `save_reading()` - 29 edges
10. `handle_group_message()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `test_common_meter_is_recognised_by_name()` --calls--> `parse_message()`  [EXTRACTED]
  tests/test_common_meters.py → bot/services/parser.py
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_workbook()` --calls--> `generate_workbook()`  [EXTRACTED]
  bot/handlers/admin.py → excel/workbook.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_debtors()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (47 total, 2 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.14
Nodes (23): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+15 more)

### Community 1 - "repository.py"
Cohesion: 0.10
Nodes (41): active_task_templates(), add_reading(), add_verification(), all_readings(), apartments_submitted(), current_readings_rows(), debtors(), ensure_house_meter() (+33 more)

### Community 2 - "save_reading"
Cohesion: 0.18
Nodes (16): is_late(), Показание передано после срока сбора? Сбор идёт с READINGS_DAY_START по…, Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), apartment_meters(), Список приборов квартиры в порядке опроса в боте., parametrize, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора». (+8 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.12
Nodes (21): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+13 more)

### Community 4 - "handlers/readings.py"
Cohesion: 0.07
Nodes (47): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+39 more)

### Community 5 - "build_statement"
Cohesion: 0.13
Nodes (22): build_statement(), Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, Регламент сбора 15–19 числа, Модуль «Сбор показаний», export_statement(), Path (+14 more)

### Community 6 - "generate_tasks"
Cohesion: 0.17
Nodes (21): generate_tasks(), Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей., Абонентские платежи: ОКС — с 27 числа, GSM — с 5 числа., Срок «до 30 числа» в феврале — последний день месяца. (+13 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.09
Nodes (31): Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания. (+23 more)

### Community 8 - "test_council.py"
Cohesion: 0.10
Nodes (21): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+13 more)

### Community 9 - "test_cleanup.py"
Cohesion: 0.14
Nodes (23): describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили…, «15.08.2026» или «2026-08-15» -> «2026-08-15 00:00:00» для сравнения., Список показаний по квартирам — чтобы видеть, что удаляем., delete_readings(), find_readings() (+15 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.08
Nodes (60): get_task(), log_task_event(), update_task(), export_year_plan(), Path, _category_code(), _clean(), _create_one_off() (+52 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (70): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+62 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.15
Nodes (14): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), task_exists() (+6 more)

### Community 25 - "demo.py"
Cohesion: 0.15
Nodes (17): collection_reminder_text(), _days_word(), date, Тексты для жителей (памятка/приветствие/уведомления)., Три сообщения для чата: пояснение и два шаблона по отдельности., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, template_messages(), welcome_residents_text() (+9 more)

### Community 26 - "current_period"
Cohesion: 0.19
Nodes (21): Bot, send_statement(), datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число… (+13 more)

### Community 27 - "handle_group_message"
Cohesion: 0.09
Nodes (34): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+26 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "build_debtors_statement"
Cohesion: 0.33
Nodes (8): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short(), test_debtors_statement()

### Community 31 - "init_db"
Cohesion: 0.16
Nodes (13): init_db(), Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_residential(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., conn() (+5 more)

### Community 32 - "task_service.py"
Cohesion: 0.14
Nodes (27): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text() (+19 more)

### Community 33 - "config.py"
Cohesion: 0.06
Nodes (44): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, _get_user(), Message (+36 more)

### Community 34 - "parse_message"
Cohesion: 0.07
Nodes (42): _classify(), _has(), _normalize(), parse_message(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю. (+34 more)

### Community 35 - "import_registry"
Cohesion: 0.12
Nodes (22): Реестр квартир, _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number(), _pick_sheet(), Connection (+14 more)

### Community 36 - "set_meters"
Cohesion: 0.27
Nodes (10): Connection, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), ensure_meter(), Приводит набор приборов квартиры к заданному: нужные — активны, лишние — нет., set_meters(), upsert_apartment() (+2 more)

### Community 37 - "workbook.py"
Cohesion: 0.09
Nodes (42): status_label(), DataValidation, fill_statement_sheet(), Заполняет готовый лист ведомостью — используется и в отдельном файле, и как…, Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждом листе., _setup_print(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+34 more)

### Community 38 - "council_digest"
Cohesion: 0.36
Nodes (8): complete_task(), council_digest(), _month_period(), Connection, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, set_status(), test_council_digest_hides_internal_details()

### Community 39 - "reminder_service.py"
Cohesion: 0.28
Nodes (8): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 40 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.19
Nodes (18): manual_readings(), message, Ручной ввод показаний председателем — в личном чате с ботом. Нежилые помещения…, Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn() (+10 more)

### Community 42 - "reading_service.py"
Cohesion: 0.14
Nodes (18): _check_hws_total(), _check_total(), _display(), _fold_totals(), last_reading_value(), my_last_readings_text(), Connection, datetime (+10 more)

### Community 43 - "make_backup"
Cohesion: 0.40
Nodes (4): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии.

### Community 44 - "create_schema"
Cohesion: 0.67
Nodes (3): _apply_migrations(), create_schema(), Добавляет колонки, появившиеся после первой версии схемы (без потери данных).

### Community 45 - "Ведомость непередавших"
Cohesion: 0.50
Nodes (5): Панель председателя, Цветовая схема DH OS, Напоминания жителям, Ведомость непередавших, Книга Excel из 5 листов

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `test_common_meters.py`, `handlers/readings.py`, `build_statement`, `test_amounts.py`, `test_council.py`, `test_cleanup.py`, `tasks_import.py`, `test_verification.py`, `demo.py`, `current_period`, `handle_group_message`, `build_debtors_statement`, `init_db`, `task_service.py`, `config.py`, `import_registry`, `set_meters`, `workbook.py`, `reminder_service.py`, `test_workbook.py`, `get_apartment_by_number`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `save_reading`, `test_common_meters.py`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `test_workbook.py`, `demo.py`, `handle_group_message`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `config.py`, `save_reading`, `test_common_meters.py`, `set_meters`, `build_statement`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `test_cleanup.py`, `test_workbook.py`, `connect`, `create_schema`, `get_apartment_by_number`, `tasks_import.py`, `test_verification.py`, `demo.py`, `handle_group_message`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13768115942028986 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10104529616724739 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._