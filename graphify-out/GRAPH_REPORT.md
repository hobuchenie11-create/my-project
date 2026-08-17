# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 79 files · ~35,564 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 886 nodes · 2325 edges · 39 communities (38 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dd124e0b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- init_db
- workbook.py
- init_db.py
- build_statement
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
- validation.py
- group.py
- TaskView
- CLAUDE.md
- demo.py
- council_digest
- task_service.py
- main.py
- parse_message
- reading_service.py
- Amount
- parser.py
- get_apartment_by_number

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

## Communities (39 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.06
Nodes (67): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., remind_debtors(), send_backup() (+59 more)

### Community 1 - "repository.py"
Cohesion: 0.06
Nodes (66): last_reading_value(), describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили…, «15.08.2026» или «2026-08-15» -> «2026-08-15 00:00:00» для сравнения., Список показаний по квартирам — чтобы видеть, что удаляем., active_task_templates() (+58 more)

### Community 2 - "init_db"
Cohesion: 0.15
Nodes (19): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), init_db(), Path, test_export_statement(), conn(), fixture, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора». (+11 more)

### Community 3 - "workbook.py"
Cohesion: 0.11
Nodes (36): status_label(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label(), status_fill(), style_header() (+28 more)

### Community 4 - "init_db.py"
Cohesion: 0.11
Nodes (28): Connection, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, _seed_nonresidential(), _seed_residential(), apartment_meters(), layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте. (+20 more)

### Community 5 - "build_statement"
Cohesion: 0.13
Nodes (23): build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text(), export_statement(), fill_statement_sheet() (+15 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.22
Nodes (14): parse_amount(), Разбирает сумму: одно число или несколько через «+». Принимает…, conn(), fixture, Сумма платежа вводится по частям: 214,33+155+207 — бот считает и расшифровывает., Одна сумма — расшифровки нет, и старое примечание не затирается., _task(), test_breakdown_is_saved_as_the_task_note() (+6 more)

### Community 8 - "test_council.py"
Cohesion: 0.12
Nodes (17): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+9 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (51): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+43 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., update_task(), export_year_plan(), Path, _category_code() (+54 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (74): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+66 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 25 - "reports.py"
Cohesion: 0.42
Nodes (8): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), my_last_readings_text(), Connection

### Community 26 - "validation.py"
Cohesion: 0.24
Nodes (12): check_reading(), CheckResult, parse_value(), Проверка вводимых показаний., Сверяет новое показание с предыдущим. Меньше предыдущего — ошибка (замену…, Разбирает число из текста пользователя (принимает запятую и точку)., test_first_reading_always_ok(), test_huge_delta_warns_but_accepts() (+4 more)

### Community 27 - "group.py"
Cohesion: 0.06
Nodes (45): Реестр квартир, _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось. (+37 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "demo.py"
Cohesion: 0.48
Nodes (6): welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…

### Community 31 - "council_digest"
Cohesion: 0.27
Nodes (10): complete_task(), council_digest(), _month_period(), Connection, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, set_status(), open_tasks() (+2 more)

### Community 32 - "task_service.py"
Cohesion: 0.17
Nodes (21): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title() (+13 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.11
Nodes (30): _normalize(), parse_message(), Убирает разделители, оставляя только буквы, для сопоставления по словарю., Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире. (+22 more)

### Community 35 - "reading_service.py"
Cohesion: 0.18
Nodes (13): _check_hws_total(), _check_total(), _display(), _fold_totals(), datetime, Row, Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка… (+5 more)

### Community 36 - "Amount"
Cohesion: 0.40
Nodes (3): Amount, Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания.

### Community 40 - "parser.py"
Cohesion: 0.25
Nodes (6): _classify(), _has(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя.

### Community 41 - "get_apartment_by_number"
Cohesion: 0.14
Nodes (27): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, _resolve_meter_kind(), save_parsed_readings(), create_user(), get_apartment_by_number(), db(), fixture, test_late_flag_stored_for_parsed_message() (+19 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `task_service.py`, `repository.py`, `init_db`, `init_db.py`, `build_statement`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `get_apartment_by_number`, `test_verification.py`, `reports.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `init_db`, `parser.py`, `get_apartment_by_number`, `validation.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `init_db.py`, `build_statement`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `tasks_import.py`, `connect`, `test_verification.py`, `group.py`, `demo.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05898021308980213 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06223358908780904 - nodes in this community are weakly interconnected._
- **Should `init_db` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._