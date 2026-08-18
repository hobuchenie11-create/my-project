# Graph Report - my-project  (2026-08-18)

## Corpus Check
- 81 files · ~39,504 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 976 nodes · 2563 edges · 42 communities (41 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `847fe9ad`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- init_db
- test_common_meters.py
- main_menu
- models.py
- task_service.py
- test_amounts.py
- test_council.py
- handlers/readings.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- handlers/registration.py
- build_statement
- validation.py
- handle_group_message
- test_statements.py
- CLAUDE.md
- Проверка показаний
- parser.py
- states/registration.py
- config.py
- parse_message
- receipt_text
- is_late
- workbook.py
- Amount
- states/readings.py
- reading_service.py
- report_service.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 76 edges
2. `parse_message()` - 64 edges
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

## Communities (42 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.05
Nodes (72): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору. (+64 more)

### Community 1 - "repository.py"
Cohesion: 0.06
Nodes (72): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+64 more)

### Community 2 - "init_db"
Cohesion: 0.13
Nodes (21): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential() (+13 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.10
Nodes (27): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+19 more)

### Community 4 - "main_menu"
Cohesion: 0.15
Nodes (17): cmd_start(), FSMContext, message, Команда /start и справка., show_help(), cancel_keyboard(), main_menu(), ReplyKeyboardMarkup (+9 more)

### Community 5 - "models.py"
Cohesion: 0.16
Nodes (17): layout_label(), Схема базы данных DH OS и справочник видов приборов учета., Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number() (+9 more)

### Community 6 - "task_service.py"
Cohesion: 0.05
Nodes (72): Каждую открытую задачу отправляем отдельно — с кнопками управления., show_urgent(), category_label(), _clamp_day(), complete_task(), council_digest(), _digest_text(), ensure_templates() (+64 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.22
Nodes (14): parse_amount(), Разбирает сумму: одно число или несколько через «+». Принимает…, conn(), fixture, Сумма платежа вводится по частям: 214,33+155+207 — бот считает и расшифровывает., Одна сумма — расшифровки нет, и старое примечание не затирается., _task(), test_breakdown_is_saved_as_the_task_note() (+6 more)

### Community 8 - "test_council.py"
Cohesion: 0.06
Nodes (43): manual_readings(), message, Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, _resolve(), collection_reminder_text(), _days_word(), late_submission_text() (+35 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.24
Nodes (16): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+8 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (62): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., update_task(), export_year_plan(), Path, _category_code() (+54 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (72): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+64 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "handlers/registration.py"
Cohesion: 0.22
Nodes (14): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+6 more)

### Community 25 - "build_statement"
Cohesion: 0.24
Nodes (14): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), test_export_statement(), Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_late_note_appended_to_existing_note() (+6 more)

### Community 26 - "validation.py"
Cohesion: 0.24
Nodes (12): check_reading(), CheckResult, parse_value(), Проверка вводимых показаний., Сверяет новое показание с предыдущим. Меньше предыдущего — ошибка (замену…, Разбирает число из текста пользователя (принимает запятую и точку)., test_first_reading_always_ok(), test_huge_delta_warns_but_accepts() (+4 more)

### Community 27 - "handle_group_message"
Cohesion: 0.10
Nodes (32): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+24 more)

### Community 28 - "test_statements.py"
Cohesion: 0.19
Nodes (12): export_statement(), Path, Отдельный файл ведомости — его председатель отправляет ресурсникам., db(), fixture, Печатные ведомости: для ресурсоснабжающих организаций и непередавших., В доме на 80 квартир ведомость печатается на двух листах: на первом — нежилые,…, Длинное примечание должно переноситься внутри колонки, иначе при печати оно… (+4 more)

### Community 30 - "Проверка показаний"
Cohesion: 0.25
Nodes (8): Реестр квартир, Правило суммы ГВС, Приём показаний из общего чата, Приём показаний через бота, Планировка приборов учёта, Проверка показаний, Словарь распознавания показаний, Шаблоны передачи показаний

### Community 31 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю.

### Community 32 - "states/registration.py"
Cohesion: 0.50
Nodes (3): StatesGroup, Состояния сценария регистрации жителя., Registration

### Community 33 - "config.py"
Cohesion: 0.06
Nodes (40): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note() (+32 more)

### Community 34 - "parse_message"
Cohesion: 0.05
Nodes (75): parse_message(), Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), create_user(), get_apartment_by_number(), db(), fixture, test_late_flag_stored_for_parsed_message() (+67 more)

### Community 35 - "receipt_text"
Cohesion: 0.50
Nodes (5): _display(), datetime, Row, Квитанция-подтверждение после передачи показаний (Этап 5)., receipt_text()

### Community 36 - "is_late"
Cohesion: 0.40
Nodes (5): is_late(), date, Показание передано после срока сбора? Сбор идёт с READINGS_DAY_START по…, parametrize, test_is_late_by_day()

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (40): status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок. (+32 more)

### Community 38 - "Amount"
Cohesion: 0.40
Nodes (3): Amount, Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания.

### Community 39 - "states/readings.py"
Cohesion: 0.50
Nodes (3): StatesGroup, Состояния сценария передачи показаний., SubmitReadings

### Community 42 - "reading_service.py"
Cohesion: 0.16
Nodes (11): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _fold_totals(), Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка…, Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим. (+3 more)

### Community 45 - "report_service.py"
Cohesion: 0.17
Nodes (13): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, Регламент сбора 15–19 числа, Модуль «Сбор показаний», fill_statement_sheet(), Выгрузка ведомости передачи показаний в Excel (.xlsx)., Заполняет готовый лист ведомостью — используется и в отдельном файле, и как… (+5 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `parse_message()` connect `parse_message` to `test_common_meters.py`, `test_council.py`, `handlers/readings.py`, `reading_service.py`, `build_statement`, `validation.py`, `handle_group_message`, `parser.py`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `init_db`, `test_common_meters.py`, `main_menu`, `models.py`, `task_service.py`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `parse_message`, `test_verification.py`, `handlers/registration.py`, `build_statement`, `handle_group_message`, `test_statements.py`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `config.py`, `repository.py`, `test_common_meters.py`, `parse_message`, `task_service.py`, `test_amounts.py`, `test_council.py`, `tasks_import.py`, `connect`, `test_verification.py`, `build_statement`, `handle_group_message`, `test_statements.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05427905427905428 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05719298245614035 - nodes in this community are weakly interconnected._
- **Should `init_db` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._