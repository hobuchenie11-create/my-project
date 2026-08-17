# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 81 files · ~38,421 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 949 nodes · 2483 edges · 44 communities (41 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `58fa1d42`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- current_period
- test_common_meters.py
- handlers/readings.py
- init_db
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
- scheduler.py
- handle_group_message
- receipt_text
- CLAUDE.md
- build_debtors_statement
- parser.py
- task_service.py
- config.py
- parse_message
- show_month_plan
- test_large_template_asks_for_the_hot_water_total
- workbook.py
- council_digest
- reminder_service.py
- test_workbook.py
- get_apartment_by_number
- reading_service.py
- Регламент сбора 15–19 числа

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

## Communities (44 total, 3 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.14
Nodes (22): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+14 more)

### Community 1 - "repository.py"
Cohesion: 0.08
Nodes (54): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+46 more)

### Community 2 - "current_period"
Cohesion: 0.29
Nodes (11): send_statement(), send_workbook(), current_period(), period_title(), save_report(), generate_workbook(), Собирает книгу из базы и возвращает путь к файлу., generate_statement() (+3 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.12
Nodes (21): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+13 more)

### Community 4 - "handlers/readings.py"
Cohesion: 0.06
Nodes (52): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+44 more)

### Community 5 - "init_db"
Cohesion: 0.05
Nodes (72): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+64 more)

### Community 6 - "generate_tasks"
Cohesion: 0.16
Nodes (23): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей. (+15 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.06
Nodes (41): Реестр квартир, complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), parse_amount(), parse_value(), Проверка вводимых показаний. (+33 more)

### Community 8 - "test_council.py"
Cohesion: 0.13
Nodes (14): conn(), FakeBot, FakeMessage, fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., Напоминание в чат: срок берётся из настроек и текущего месяца. (+6 more)

### Community 9 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (61): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, _category_code(), _clean() (+53 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (68): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+60 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.16
Nodes (14): _clamp_day(), ensure_templates(), generate_year(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task() (+6 more)

### Community 25 - "demo.py"
Cohesion: 0.16
Nodes (17): collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, welcome_residents_text() (+9 more)

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "handle_group_message"
Cohesion: 0.10
Nodes (32): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+24 more)

### Community 28 - "receipt_text"
Cohesion: 0.28
Nodes (8): manual_readings(), message, Ручной ввод показаний председателем — в личном чате с ботом. Нежилые помещения…, _display(), datetime, Row, Квитанция-подтверждение после передачи показаний (Этап 5)., receipt_text()

### Community 30 - "build_debtors_statement"
Cohesion: 0.33
Nodes (8): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short(), test_debtors_statement()

### Community 31 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 32 - "task_service.py"
Cohesion: 0.10
Nodes (24): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _digest_text(), _fmt_date(), month_plan_text(), one_off_text(), period_title() (+16 more)

### Community 33 - "config.py"
Cohesion: 0.06
Nodes (40): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note() (+32 more)

### Community 34 - "parse_message"
Cohesion: 0.10
Nodes (34): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+26 more)

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 38 - "council_digest"
Cohesion: 0.19
Nodes (14): council_candidates(), council_digest(), _month_period(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, set_status(), open_tasks(), Все незакрытые задачи — по сроку, ближайшие первыми. (+6 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.24
Nodes (9): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget (+1 more)

### Community 40 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.25
Nodes (15): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., «ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор. (+7 more)

### Community 42 - "reading_service.py"
Cohesion: 0.16
Nodes (12): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _fold_totals(), Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка…, Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим. (+4 more)

### Community 45 - "Регламент сбора 15–19 числа"
Cohesion: 0.33
Nodes (7): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Ведомость непередавших, Книга Excel из 5 листов

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `current_period`, `test_common_meters.py`, `handlers/readings.py`, `init_db`, `test_amounts.py`, `test_council.py`, `test_cleanup.py`, `tasks_import.py`, `test_verification.py`, `demo.py`, `scheduler.py`, `handle_group_message`, `receipt_text`, `build_debtors_statement`, `task_service.py`, `show_month_plan`, `reminder_service.py`, `test_workbook.py`, `get_apartment_by_number`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `test_common_meters.py`, `test_large_template_asks_for_the_hot_water_total`, `init_db`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `reading_service.py`, `test_workbook.py`, `demo.py`, `handle_group_message`, `receipt_text`, `parser.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `config.py`, `repository.py`, `test_common_meters.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `test_cleanup.py`, `test_workbook.py`, `connect`, `get_apartment_by_number`, `tasks_import.py`, `test_verification.py`, `demo.py`, `handle_group_message`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07662337662337662 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._