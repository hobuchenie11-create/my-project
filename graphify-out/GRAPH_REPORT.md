# Graph Report - my-project  (2026-08-16)

## Corpus Check
- 75 files · ~32,638 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 799 nodes · 2136 edges · 42 communities (41 shown, 1 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1bb3d5b7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- connect
- repository.py
- build_statement
- workbook.py
- config.py
- test_workbook.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- init_db.py
- save_reading
- group.py
- council_digest
- CLAUDE.md
- reading_service.py
- task_service.py
- date
- main.py
- parse_message
- validation.py
- init_db
- Регламент сбора 15–19 числа
- build_debtors_statement
- Проверка показаний
- parser.py
- ensure_templates

## God Nodes (most connected - your core abstractions)
1. `connect()` - 60 edges
2. `parse_message()` - 33 edges
3. `init_db()` - 33 edges
4. `generate_tasks()` - 30 edges
5. `current_period()` - 29 edges
6. `build_statement()` - 29 edges
7. `save_reading()` - 27 edges
8. `get_apartment_by_number()` - 27 edges
9. `save_parsed_readings()` - 26 edges
10. `export_year_plan()` - 25 edges

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

## Communities (42 total, 1 thin omitted)

### Community 0 - "connect"
Cohesion: 0.08
Nodes (55): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., remind_debtors(), send_backup(), send_debtors_doc() (+47 more)

### Community 1 - "repository.py"
Cohesion: 0.09
Nodes (46): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+38 more)

### Community 2 - "build_statement"
Cohesion: 0.13
Nodes (24): build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text(), export_statement(), fill_statement_sheet() (+16 more)

### Community 3 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 4 - "config.py"
Cohesion: 0.21
Nodes (11): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., late_submission_text(), Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist() (+3 more)

### Community 5 - "test_workbook.py"
Cohesion: 0.36
Nodes (9): create_user(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted() (+1 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.15
Nodes (17): Amount, parse_amount(), Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания., Разбирает сумму: одно число или несколько через «+». Принимает…, conn(), fixture, Сумма платежа вводится по частям: 214,33+155+207 — бот считает и расшифровывает. (+9 more)

### Community 8 - "test_council.py"
Cohesion: 0.16
Nodes (10): conn(), FakeBot, FakeMessage, fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., test_digest_goes_to_the_council_chat() (+2 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.09
Nodes (37): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+29 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (61): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, _category_code(), _clean() (+53 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.06
Nodes (64): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+56 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (42): meter_interval(), Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView (+34 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.20
Nodes (11): send_year_plan(), _clamp_day(), generate_year(), День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out(), Разовые задачи — на отдельном листе, с автоматическим отсчётом срока. (+3 more)

### Community 25 - "init_db.py"
Cohesion: 0.11
Nodes (28): Connection, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте. (+20 more)

### Community 26 - "save_reading"
Cohesion: 0.23
Nodes (15): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), get_apartment_by_number(), Последнее показание каждого прибора за период, с номером квартиры., readings_for_period(), Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_flag_stored_for_parsed_message(), test_late_note_appended_to_existing_note() (+7 more)

### Community 27 - "group.py"
Cohesion: 0.21
Nodes (14): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+6 more)

### Community 28 - "council_digest"
Cohesion: 0.19
Nodes (16): complete_task(), council_candidates(), council_digest(), _month_period(), Connection, Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —… (+8 more)

### Community 30 - "reading_service.py"
Cohesion: 0.16
Nodes (18): ParsedReadings, _check_hws_total(), _display(), datetime, Row, Сохранение и просмотр показаний., Квитанция-подтверждение после передачи показаний (Этап 5)., Итог записи показаний из одного сообщения (общий чат). (+10 more)

### Community 31 - "task_service.py"
Cohesion: 0.14
Nodes (23): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text() (+15 more)

### Community 32 - "date"
Cohesion: 0.17
Nodes (5): date, Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., _shift_month(), TaskView

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.25
Nodes (14): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., test_comma_separators_and_carry_context(), test_dotted_abbrev_full(), test_gas_ignored_and_room_temperature_words(), test_leading_zeros(), test_nonresidential(), test_ordinary_chat_message_ignored() (+6 more)

### Community 35 - "validation.py"
Cohesion: 0.24
Nodes (12): check_reading(), CheckResult, parse_value(), Проверка вводимых показаний., Сверяет новое показание с предыдущим. Меньше предыдущего — ошибка (замену…, Разбирает число из текста пользователя (принимает запятую и точку)., test_first_reading_always_ok(), test_huge_delta_warns_but_accepts() (+4 more)

### Community 36 - "init_db"
Cohesion: 0.14
Nodes (14): init_db(), Path, conn(), fixture, conn(), fixture, conn(), fixture (+6 more)

### Community 37 - "Регламент сбора 15–19 числа"
Cohesion: 0.29
Nodes (8): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Книга Excel из 5 листов

### Community 38 - "build_debtors_statement"
Cohesion: 0.39
Nodes (7): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short()

### Community 39 - "Проверка показаний"
Cohesion: 0.25
Nodes (8): Реестр квартир, Правило суммы ГВС, Приём показаний из общего чата, Приём показаний через бота, Планировка приборов учёта, Проверка показаний, Словарь распознавания показаний, Шаблоны передачи показаний

### Community 40 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 41 - "ensure_templates"
Cohesion: 0.40
Nodes (5): ensure_templates(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Подтягивает в задачи изменения шаблонов (название, категория, приоритет).…, sync_tasks_with_templates(), test_templates_cover_the_chairman_cycle()

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `repository.py`, `build_statement`, `init_db`, `config.py`, `build_debtors_statement`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `handlers/tasks.py`, `test_verification.py`, `generate_year`, `init_db.py`, `save_reading`, `group.py`, `task_service.py`?**
  _High betweenness centrality (0.097) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `connect`, `main.py`, `repository.py`, `build_statement`, `config.py`, `test_workbook.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `tasks_import.py`, `test_verification.py`, `init_db.py`, `save_reading`, `reading_service.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `validation.py`, `config.py`, `test_workbook.py`, `parser.py`, `save_reading`, `group.py`, `reading_service.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `connect` be split into smaller, more focused modules?**
  _Cohesion score 0.07595628415300547 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.09131205673758866 - nodes in this community are weakly interconnected._
- **Should `build_statement` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._