# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 79 files · ~35,879 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 892 nodes · 2337 edges · 44 communities (42 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `fa917151`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- save_reading
- export_year_plan
- models.py
- test_statements.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- reports.py
- scheduler.py
- group.py
- TaskView
- CLAUDE.md
- demo.py
- council_digest
- task_service.py
- main.py
- parse_message
- reading_service.py
- init_db
- workbook.py
- texts.py
- style.py
- test_workbook.py
- get_apartment_by_number
- make_backup
- db

## God Nodes (most connected - your core abstractions)
1. `connect()` - 64 edges
2. `parse_message()` - 44 edges
3. `init_db()` - 37 edges
4. `get_apartment_by_number()` - 34 edges
5. `save_parsed_readings()` - 31 edges
6. `generate_tasks()` - 30 edges
7. `current_period()` - 29 edges
8. `save_reading()` - 29 edges
9. `build_statement()` - 29 edges
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

## Communities (44 total, 2 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.16
Nodes (25): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., remind_debtors(), send_backup() (+17 more)

### Community 1 - "repository.py"
Cohesion: 0.06
Nodes (71): describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили…, «15.08.2026» или «2026-08-15» -> «2026-08-15 00:00:00» для сравнения., Список показаний по квартирам — чтобы видеть, что удаляем., active_task_templates(), add_reading() (+63 more)

### Community 2 - "save_reading"
Cohesion: 0.20
Nodes (16): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note(), test_late_reading_marked_in_statement() (+8 more)

### Community 3 - "export_year_plan"
Cohesion: 0.10
Nodes (43): category_label(), status_label(), get_task(), Оформляет строку заголовков таблицы и задаёт ширину колонок., style_header(), export_year_plan(), _fmt(), _hide_service_column() (+35 more)

### Community 4 - "models.py"
Cohesion: 0.15
Nodes (19): apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template() (+11 more)

### Community 5 - "test_statements.py"
Cohesion: 0.13
Nodes (18): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, Регламент сбора 15–19 числа, Модуль «Сбор показаний», export_statement(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx). (+10 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.09
Nodes (31): Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания. (+23 more)

### Community 8 - "test_council.py"
Cohesion: 0.12
Nodes (17): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+9 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (49): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+41 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.13
Nodes (34): log_task_event(), update_task(), _category_code(), _clean(), _create_one_off(), _header_map(), _import_meters(), _import_one_off() (+26 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (72): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+64 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (41): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+33 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 25 - "reports.py"
Cohesion: 0.36
Nodes (9): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+1 more)

### Community 26 - "scheduler.py"
Cohesion: 0.14
Nodes (22): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+14 more)

### Community 27 - "group.py"
Cohesion: 0.07
Nodes (34): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+26 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "demo.py"
Cohesion: 0.18
Nodes (16): late_submission_text(), Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт… (+8 more)

### Community 31 - "council_digest"
Cohesion: 0.36
Nodes (8): complete_task(), council_digest(), _month_period(), Connection, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, set_status(), test_council_digest_hides_internal_details()

### Community 32 - "task_service.py"
Cohesion: 0.19
Nodes (18): _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title(), date, Row, Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные… (+10 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.12
Nodes (28): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+20 more)

### Community 35 - "reading_service.py"
Cohesion: 0.15
Nodes (18): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _display(), _fold_totals(), datetime, Row (+10 more)

### Community 36 - "init_db"
Cohesion: 0.12
Nodes (22): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), Приводит набор приборов квартиры к заданному: нужные — активны, лишние — нет., set_meters() (+14 more)

### Community 37 - "workbook.py"
Cohesion: 0.17
Nodes (20): DataValidation, fill_statement_sheet(), Заполняет готовый лист ведомостью — используется и в отдельном файле, и как…, Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждом листе., _setup_print(), build_workbook(), _current_by_apartment(), generate_workbook() (+12 more)

### Community 38 - "texts.py"
Cohesion: 0.15
Nodes (13): collection_reminder_text(), _days_word(), date, Тексты для жителей (памятка/приветствие/уведомления)., Три сообщения для чата: пояснение и два шаблона по отдельности., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, template_messages(), Напоминание в чат: срок берётся из настроек и текущего месяца. (+5 more)

### Community 39 - "style.py"
Cohesion: 0.24
Nodes (9): Панель председателя, Цветовая схема DH OS, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, room_fill(), room_label(), status_fill(), PatternFill, Ведомость непередавших (+1 more)

### Community 40 - "test_workbook.py"
Cohesion: 0.18
Nodes (15): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., create_user(), _build() (+7 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.21
Nodes (13): get_apartment_by_number(), db(), fixture, test_late_flag_stored_for_parsed_message(), Раскладка распознанных показаний на приборы конкретной квартиры., «ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор., test_cold_total_is_checked_too(), test_compact_apartment_rejects_split() (+5 more)

### Community 42 - "make_backup"
Cohesion: 0.40
Nodes (4): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии.

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `save_reading`, `init_db`, `models.py`, `workbook.py`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `get_apartment_by_number`, `test_statements.py`, `test_verification.py`, `reports.py`, `scheduler.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `save_reading`, `reading_service.py`, `test_amounts.py`, `test_workbook.py`, `get_apartment_by_number`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `save_reading`, `export_year_plan`, `test_statements.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `test_workbook.py`, `connect`, `db`, `test_verification.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05775638652350981 - nodes in this community are weakly interconnected._
- **Should `export_year_plan` be split into smaller, more focused modules?**
  _Cohesion score 0.10101010101010101 - nodes in this community are weakly interconnected._
- **Should `test_statements.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13438735177865613 - nodes in this community are weakly interconnected._