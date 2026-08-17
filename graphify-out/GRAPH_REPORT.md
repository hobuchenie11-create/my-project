# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 81 files · ~37,421 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 934 nodes · 2447 edges · 47 communities (46 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6404c236`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- build_statement
- test_common_meters.py
- models.py
- test_statements.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- demo.py
- scheduler.py
- group.py
- TaskView
- CLAUDE.md
- build_debtors_statement
- council_digest
- task_service.py
- main.py
- parse_message
- init_db
- connect
- workbook.py
- current_period
- reminder_service.py
- test_workbook.py
- get_apartment_by_number
- reading_service.py
- config.py
- receipt_text
- Ведомость для ресурсоснабжающих организаций
- parser.py

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

## Communities (47 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.15
Nodes (21): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+13 more)

### Community 1 - "repository.py"
Cohesion: 0.06
Nodes (70): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+62 more)

### Community 2 - "build_statement"
Cohesion: 0.24
Nodes (14): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), test_export_statement(), Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note() (+6 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.14
Nodes (19): Последнее показание каждого прибора за период, с номером квартиры., readings_for_period(), db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда. (+11 more)

### Community 4 - "models.py"
Cohesion: 0.15
Nodes (19): apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template() (+11 more)

### Community 5 - "test_statements.py"
Cohesion: 0.14
Nodes (17): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx)., Отдельный файл ведомости — его председатель отправляет ресурсникам. (+9 more)

### Community 6 - "generate_tasks"
Cohesion: 0.16
Nodes (23): generate_tasks(), Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей. (+15 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.08
Nodes (34): complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний. (+26 more)

### Community 8 - "test_council.py"
Cohesion: 0.12
Nodes (14): conn(), FakeBot, FakeMessage, fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., Напоминание в чат: срок берётся из настроек и текущего месяца. (+6 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (52): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+44 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, _category_code(), _clean() (+54 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.05
Nodes (74): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+66 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (37): add_years(), _fmt(), meters_text(), MeterView, next_due(), Connection, date, Row (+29 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.18
Nodes (12): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+4 more)

### Community 25 - "demo.py"
Cohesion: 0.14
Nodes (19): collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., Три сообщения для чата: пояснение и два шаблона по отдельности., Короткое напоминание в чат дома: до какого числа передать показания. Дата… (+11 more)

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "group.py"
Cohesion: 0.09
Nodes (29): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+21 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "build_debtors_statement"
Cohesion: 0.39
Nodes (7): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short()

### Community 31 - "council_digest"
Cohesion: 0.31
Nodes (9): council_digest(), _month_period(), Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, _one_off(), Ежемесячный регламент Совету не предлагается — только разовые дела., test_candidates_are_one_off_tasks_only(), test_done_task_is_offered_and_shown_as_done(), test_only_selected_tasks_reach_the_digest() (+1 more)

### Community 32 - "task_service.py"
Cohesion: 0.16
Nodes (24): council_candidates(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title(), Connection, date (+16 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.09
Nodes (35): parse_message(), test_common_meter_is_recognised_by_name(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке. (+27 more)

### Community 35 - "init_db"
Cohesion: 0.22
Nodes (15): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential() (+7 more)

### Community 36 - "connect"
Cohesion: 0.12
Nodes (17): connect(), Path, conn(), fixture, Нежилое №1 — свет и вода, нежилое №2 — только свет., test_nonresidential_meter_sets_differ(), test_registry_has_the_common_meter_row(), conn() (+9 more)

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (41): category_label(), status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+33 more)

### Community 38 - "current_period"
Cohesion: 0.26
Nodes (11): send_workbook(), current_period(), period_title(), save_report(), generate_workbook(), Собирает книгу из базы и возвращает путь к файлу., generate_statement(), Path (+3 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.28
Nodes (8): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 40 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.25
Nodes (15): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., «ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор. (+7 more)

### Community 42 - "reading_service.py"
Cohesion: 0.16
Nodes (11): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _fold_totals(), Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка…, Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим. (+3 more)

### Community 43 - "config.py"
Cohesion: 0.22
Nodes (6): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии.

### Community 44 - "receipt_text"
Cohesion: 0.28
Nodes (8): manual_readings(), message, Ручной ввод показаний председателем — в личном чате с ботом. Нежилые помещения…, _display(), datetime, Row, Квитанция-подтверждение после передачи показаний (Этап 5)., receipt_text()

### Community 45 - "Ведомость для ресурсоснабжающих организаций"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

### Community 46 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `build_statement`, `test_common_meters.py`, `models.py`, `test_statements.py`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `handlers/tasks.py`, `test_verification.py`, `demo.py`, `scheduler.py`, `group.py`, `build_debtors_statement`, `init_db`, `current_period`, `reminder_service.py`, `test_workbook.py`, `get_apartment_by_number`, `receipt_text`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `build_statement`, `test_common_meters.py`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `reading_service.py`, `test_workbook.py`, `receipt_text`, `parser.py`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `test_common_meters.py`, `connect`, `build_statement`, `test_statements.py`, `test_amounts.py`, `test_council.py`, `test_workbook.py`, `get_apartment_by_number`, `generate_tasks`, `tasks_import.py`, `test_verification.py`, `demo.py`, `group.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05886708626434654 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13852813852813853 - nodes in this community are weakly interconnected._
- **Should `test_statements.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14285714285714285 - nodes in this community are weakly interconnected._