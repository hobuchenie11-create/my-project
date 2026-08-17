# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 81 files · ~39,284 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 968 nodes · 2551 edges · 41 communities (39 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7690c4f7`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- current_period
- connect
- main_menu
- init_db
- task_service.py
- test_amounts.py
- test_council.py
- netcheck.py
- tasks_import.py
- handlers/tasks.py
- test_verification.py
- Модуль 1. Задачи (только председатель)
- handlers/registration.py
- texts.py
- scheduler.py
- handle_group_message
- config.py
- CLAUDE.md
- demo.py
- parser.py
- states/registration.py
- main.py
- parse_message
- workbook.py
- reminder_service.py
- test_workbook.py
- get_apartment_by_number
- reading_service.py
- Регламент сбора 15–19 числа

## God Nodes (most connected - your core abstractions)
1. `connect()` - 76 edges
2. `parse_message()` - 60 edges
3. `get_apartment_by_number()` - 41 edges
4. `init_db()` - 40 edges
5. `save_parsed_readings()` - 35 edges
6. `current_period()` - 33 edges
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
- `show_users()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (41 total, 2 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.15
Nodes (21): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+13 more)

### Community 1 - "repository.py"
Cohesion: 0.05
Nodes (75): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+67 more)

### Community 2 - "current_period"
Cohesion: 0.25
Nodes (10): send_statement(), send_workbook(), current_period(), save_report(), generate_workbook(), Собирает книгу из базы и возвращает путь к файлу., generate_statement(), Path (+2 more)

### Community 3 - "connect"
Cohesion: 0.06
Nodes (66): manual_readings(), message, Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, _resolve(), _ask_next_meter(), cancel_submission(), _finish() (+58 more)

### Community 4 - "main_menu"
Cohesion: 0.15
Nodes (17): cmd_start(), FSMContext, message, Команда /start и справка., show_help(), cancel_keyboard(), main_menu(), ReplyKeyboardMarkup (+9 more)

### Community 5 - "init_db"
Cohesion: 0.05
Nodes (74): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+66 more)

### Community 6 - "task_service.py"
Cohesion: 0.05
Nodes (74): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _clamp_day(), complete_task(), council_digest(), _digest_text(), ensure_templates() (+66 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.07
Nodes (39): Реестр квартир, Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит… (+31 more)

### Community 8 - "test_council.py"
Cohesion: 0.08
Nodes (27): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note(), conn(), FakeBot (+19 more)

### Community 9 - "netcheck.py"
Cohesion: 0.18
Nodes (15): check(), _port_open(), Подбор рабочего прокси для подключения к Telegram. Запуск: python -m…, _try_http(), _try_socks(), build_socks_connector(), make_session(), normalize_proxy_url() (+7 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.08
Nodes (59): get_task(), log_task_event(), export_year_plan(), Path, _category_code(), _clean(), _create_one_off(), _header_map() (+51 more)

### Community 11 - "handlers/tasks.py"
Cohesion: 0.06
Nodes (69): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+61 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (44): meter_interval(), Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView (+36 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "handlers/registration.py"
Cohesion: 0.22
Nodes (14): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+6 more)

### Community 25 - "texts.py"
Cohesion: 0.22
Nodes (10): collection_reminder_text(), _days_word(), date, Тексты для жителей (памятка/приветствие/уведомления)., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, welcome_residents_text(), Памятка и напоминание — одна формулировка и шаблоны без чисел., Шаблоны уходят по отдельности — чтобы житель копировал нужный. (+2 more)

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "handle_group_message"
Cohesion: 0.10
Nodes (32): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+24 more)

### Community 30 - "demo.py"
Cohesion: 0.23
Nodes (14): send_debtors_doc(), period_title(), build_demo(), _checklist(), _plain(), _print_summary(), Демонстрация модуля «Сбор показаний» — для проверки результата. Создаёт…, build_debtors_statement() (+6 more)

### Community 31 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 32 - "states/registration.py"
Cohesion: 0.50
Nodes (3): StatesGroup, Состояния сценария регистрации жителя., Registration

### Community 33 - "main.py"
Cohesion: 0.15
Nodes (17): allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята., Возвращает обычное поведение — вызывается при остановке бота., _apply_registry_if_present(), _log_chats(), main() (+9 more)

### Community 34 - "parse_message"
Cohesion: 0.08
Nodes (41): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+33 more)

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.24
Nodes (9): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget (+1 more)

### Community 40 - "test_workbook.py"
Cohesion: 0.39
Nodes (8): _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted(), test_submitted_status_without_registration()

### Community 41 - "get_apartment_by_number"
Cohesion: 0.22
Nodes (13): get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., «ГВС» одной строкой у 3-комнатной — это итог, а не отсутствующий прибор., test_cold_total_is_checked_too(), test_compact_apartment_rejects_split() (+5 more)

### Community 42 - "reading_service.py"
Cohesion: 0.16
Nodes (16): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _display(), _fold_totals(), datetime, Row (+8 more)

### Community 45 - "Регламент сбора 15–19 числа"
Cohesion: 0.33
Nodes (7): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Ведомость непередавших, Книга Excel из 5 листов

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `current_period`, `main_menu`, `init_db`, `task_service.py`, `reminder_service.py`, `test_amounts.py`, `test_council.py`, `tasks_import.py`, `handlers/tasks.py`, `get_apartment_by_number`, `test_verification.py`, `handlers/registration.py`, `scheduler.py`, `handle_group_message`, `demo.py`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `connect`, `init_db`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `reading_service.py`, `test_workbook.py`, `handle_group_message`, `demo.py`, `parser.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `connect`, `task_service.py`, `test_amounts.py`, `test_council.py`, `get_apartment_by_number`, `tasks_import.py`, `test_workbook.py`, `test_verification.py`, `handle_group_message`, `demo.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1471861471861472 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.052531645569620256 - nodes in this community are weakly interconnected._
- **Should `connect` be split into smaller, more focused modules?**
  _Cohesion score 0.05712050078247261 - nodes in this community are weakly interconnected._