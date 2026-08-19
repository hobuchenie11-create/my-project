# Graph Report - my-project  (2026-08-19)

## Corpus Check
- 81 files · ~39,837 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 985 nodes · 2585 edges · 42 communities (40 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e7872dc8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- current_period
- repository.py
- admin.py
- connect
- handlers/readings.py
- save_reading
- generate_tasks
- task_service.py
- test_council.py
- demo.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- registry_summary
- get_apartment_by_number
- test_amounts.py
- handle_group_message
- council_digest
- CLAUDE.md
- generate_year
- parser.py
- TaskView
- config.py
- parse_message
- reports.py
- test_workbook.py
- workbook.py
- Регламент сбора 15–19 числа
- test_large_template_asks_for_the_hot_water_total
- reading_service.py
- build_statement

## God Nodes (most connected - your core abstractions)
1. `connect()` - 76 edges
2. `parse_message()` - 67 edges
3. `get_apartment_by_number()` - 44 edges
4. `init_db()` - 40 edges
5. `save_parsed_readings()` - 39 edges
6. `current_period()` - 33 edges
7. `build_statement()` - 33 edges
8. `generate_tasks()` - 30 edges
9. `save_reading()` - 29 edges
10. `handle_group_message()` - 26 edges

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

## Communities (42 total, 2 thin omitted)

### Community 0 - "current_period"
Cohesion: 0.15
Nodes (26): Bot, send_statement(), datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число… (+18 more)

### Community 1 - "repository.py"
Cohesion: 0.06
Nodes (72): send_backup(), last_reading_value(), make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main() (+64 more)

### Community 2 - "admin.py"
Cohesion: 0.10
Nodes (31): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+23 more)

### Community 3 - "connect"
Cohesion: 0.06
Nodes (56): manual_readings(), message, Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, _resolve(), init_db(), Path, connect() (+48 more)

### Community 4 - "handlers/readings.py"
Cohesion: 0.06
Nodes (50): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+42 more)

### Community 5 - "save_reading"
Cohesion: 0.09
Nodes (38): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), Connection, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential() (+30 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "task_service.py"
Cohesion: 0.16
Nodes (23): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text() (+15 more)

### Community 8 - "test_council.py"
Cohesion: 0.15
Nodes (12): FakeBot, FakeMessage, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., Напоминание в чат: срок берётся из настроек и текущего месяца., «Приватность выключена» ещё не значит, что бот видит этот чат., test_chat_reminder_names_the_deadline() (+4 more)

### Community 9 - "demo.py"
Cohesion: 0.15
Nodes (19): late_submission_text(), Сообщение жителю, передавшему показания после срока сбора., welcome_residents_text(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт… (+11 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.06
Nodes (75): status_label(), get_task(), log_task_event(), update_task(), DataValidation, export_year_plan(), _fmt(), _hide_service_column() (+67 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.06
Nodes (66): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+58 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (41): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+33 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "registry_summary"
Cohesion: 0.40
Nodes (5): _display_number(), Операции с реестром квартир., Текстовый реестр квартир с отметкой о сдаче показаний за период., registry_summary(), apartments_submitted()

### Community 25 - "get_apartment_by_number"
Cohesion: 0.14
Nodes (20): get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., Прибор один, а мест названо два — записывать наугад нельзя., У кв. 1 учёт раздельный — подписи по местам работают как раньше., Прибор один, названо одно место — это он и есть (счётчик в санузле). (+12 more)

### Community 26 - "test_amounts.py"
Cohesion: 0.07
Nodes (37): Реестр квартир, Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит… (+29 more)

### Community 27 - "handle_group_message"
Cohesion: 0.10
Nodes (32): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+24 more)

### Community 28 - "council_digest"
Cohesion: 0.20
Nodes (15): complete_task(), council_candidates(), council_digest(), _month_period(), Connection, Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —… (+7 more)

### Community 30 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 31 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "config.py"
Cohesion: 0.06
Nodes (40): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note() (+32 more)

### Community 34 - "parse_message"
Cohesion: 0.06
Nodes (50): parse_message(), test_common_meter_is_recognised_by_name(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке. (+42 more)

### Community 35 - "reports.py"
Cohesion: 0.42
Nodes (8): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), my_last_readings_text(), Connection

### Community 36 - "test_workbook.py"
Cohesion: 0.39
Nodes (8): _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted(), test_submitted_status_without_registration()

### Community 37 - "workbook.py"
Cohesion: 0.14
Nodes (27): current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), save_report(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill() (+19 more)

### Community 38 - "Регламент сбора 15–19 числа"
Cohesion: 0.33
Nodes (7): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Ведомость непередавших, Книга Excel из 5 листов

### Community 42 - "reading_service.py"
Cohesion: 0.15
Nodes (20): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _display(), _fold_locations(), _fold_totals(), datetime (+12 more)

### Community 45 - "build_statement"
Cohesion: 0.12
Nodes (26): build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text(), export_statement(), fill_statement_sheet() (+18 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_message()` connect `parse_message` to `connect`, `handlers/readings.py`, `save_reading`, `test_workbook.py`, `test_large_template_asks_for_the_hot_water_total`, `test_council.py`, `demo.py`, `reading_service.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`, `parser.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `current_period`, `repository.py`, `admin.py`, `reports.py`, `handlers/readings.py`, `save_reading`, `workbook.py`, `task_service.py`, `demo.py`, `tasks_import.py`, `handlers/tasks.py`, `build_statement`, `test_verification.py`, `get_apartment_by_number`, `handle_group_message`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `init_db()` connect `connect` to `config.py`, `repository.py`, `test_workbook.py`, `save_reading`, `generate_tasks`, `test_council.py`, `demo.py`, `tasks_import.py`, `build_statement`, `test_verification.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `current_period` be split into smaller, more focused modules?**
  _Cohesion score 0.14532019704433496 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.055087719298245616 - nodes in this community are weakly interconnected._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.10037878787878787 - nodes in this community are weakly interconnected._