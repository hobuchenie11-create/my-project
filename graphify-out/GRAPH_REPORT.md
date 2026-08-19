# Graph Report - my-project  (2026-08-19)

## Corpus Check
- 92 files · ~43,900 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1106 nodes · 2882 edges · 61 communities (55 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a846b6f3`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- scheduler.py
- repository.py
- admin.py
- test_common_meters.py
- main_menu
- test_batch.py
- generate_tasks
- task_service.py
- test_council.py
- build_debtors_statement
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- faq_service.py
- get_apartment_by_number
- test_amounts.py
- handle_group_message
- test_cleanup.py
- CLAUDE.md
- generate_year
- task_line
- date
- main.py
- parse_message
- init_db
- test_workbook.py
- workbook.py
- Ведомость для ресурсоснабжающих организаций
- handlers/registration.py
- handlers/readings.py
- demo.py
- reading_service.py
- config.py
- reminder_service.py
- group.py
- manual.py
- README.md
- import_batch
- reports.py
- parser.py
- is_late
- FakeBot
- ParsedReadings
- states/readings.py
- test_bare_number_after_a_flat_number_is_not_a_reading
- test_single_letter_needs_a_location_to_count

## God Nodes (most connected - your core abstractions)
1. `connect()` - 91 edges
2. `parse_message()` - 69 edges
3. `get_apartment_by_number()` - 47 edges
4. `init_db()` - 44 edges
5. `save_parsed_readings()` - 41 edges
6. `current_period()` - 35 edges
7. `build_statement()` - 33 edges
8. `handle_group_message()` - 30 edges
9. `generate_tasks()` - 30 edges
10. `save_reading()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `test_common_meter_is_recognised_by_name()` --calls--> `parse_message()`  [EXTRACTED]
  tests/test_common_meters.py → bot/services/parser.py
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_statement()` --calls--> `generate_statement()`  [EXTRACTED]
  bot/handlers/admin.py → reports/monthly_statement.py
- `send_workbook()` --calls--> `generate_workbook()`  [EXTRACTED]
  bot/handlers/admin.py → excel/workbook.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (61 total, 6 thin omitted)

### Community 0 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 1 - "repository.py"
Cohesion: 0.07
Nodes (60): last_reading_value(), Connection, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), active_memos(), active_task_templates(), add_faq_gap() (+52 more)

### Community 2 - "admin.py"
Cohesion: 0.12
Nodes (31): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., О чём спрашивали жители, а памятки для ответа нет. (+23 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.10
Nodes (28): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+20 more)

### Community 4 - "main_menu"
Cohesion: 0.15
Nodes (17): cmd_start(), FSMContext, message, Команда /start и справка., show_help(), cancel_keyboard(), main_menu(), ReplyKeyboardMarkup (+9 more)

### Community 5 - "test_batch.py"
Cohesion: 0.14
Nodes (17): Убирает из строки дату, время и имя автора скопированного сообщения., Делит вставленную пачку на отдельные сообщения — по строке с квартирой.…, split_messages(), strip_chat_meta(), Msg, Перенос показаний из WhatsApp: вставленная пачка сообщений., Вставили в чат показаний — тоже разносим, сводка уходит в личку., У жителя пачка — это чужие квартиры: просим прислать свою. (+9 more)

### Community 6 - "generate_tasks"
Cohesion: 0.13
Nodes (28): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), conn() (+20 more)

### Community 7 - "task_service.py"
Cohesion: 0.18
Nodes (13): council_candidates(), ensure_templates(), month_plan_text(), period_title(), Connection, Row, Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные…, Заводит шаблоны регулярных задач (при первом запуске и после обновлений). (+5 more)

### Community 8 - "test_council.py"
Cohesion: 0.09
Nodes (26): council_digest(), _month_period(), Информационная сводка для Совета дома. Только заголовки, сроки и статусы —…, create_task(), conn(), FakeBot, FakeMessage, _one_off() (+18 more)

### Community 9 - "build_debtors_statement"
Cohesion: 0.33
Nodes (8): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short(), test_debtors_statement()

### Community 10 - "tasks_import.py"
Cohesion: 0.06
Nodes (72): get_task(), log_task_event(), export_year_plan(), _fmt(), _hide_service_column(), _list_validation(), Connection, Path (+64 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (68): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+60 more)

### Community 22 - "test_verification.py"
Cohesion: 0.08
Nodes (43): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+35 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "faq_service.py"
Cohesion: 0.07
Nodes (52): answer_question(), back_to_categories(), callback_query, CallbackQuery, message, Памятки Домоведа: разделы, тексты и ответы на вопросы жителей., Ищет ответ на вопрос жителя. False — вопрос остался без ответа. Вызывается из…, Отправляет памятку — с картинкой, если она к ней приложена. (+44 more)

### Community 25 - "get_apartment_by_number"
Cohesion: 0.17
Nodes (22): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., Прибор один, а мест названо два — записывать наугад нельзя. (+14 more)

### Community 26 - "test_amounts.py"
Cohesion: 0.06
Nodes (41): Реестр квартир, complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), parse_amount(), parse_value(), Проверка вводимых показаний. (+33 more)

### Community 27 - "handle_group_message"
Cohesion: 0.19
Nodes (21): handle_group_message(), FakeMessage, Приём показаний из общего чата: в чью квартиру они попадают., Чужой чат — предупреждение в лог: так видно смену ID чата дома., Реакции в чате запрещены: показания записаны, но это должно быть видно., Реакции в чате запрещены — подтверждаем короткой строкой (CHAT_CONFIRM=auto)., Сообщение в общем чате дома от жителя., «Кв,, 29» от жителя кв. 49 — записываем в 29-ю, а не в квартиру автора. (+13 more)

### Community 28 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

### Community 30 - "generate_year"
Cohesion: 0.25
Nodes (8): _clamp_day(), generate_year(), День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., Разовые задачи — на отдельном листе, с автоматическим отсчётом срока., test_generate_year_covers_twelve_months(), test_one_off_sheet_lists_my_tasks(), test_year_plan_export()

### Community 31 - "task_line"
Cohesion: 0.23
Nodes (13): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), one_off_text(), Одна строка задачи для списка в боте., Разовые задачи председателя — то, что он планирует сам. (+5 more)

### Community 32 - "date"
Cohesion: 0.14
Nodes (10): _digest_text(), _fmt_date(), date, Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., Просроченные и текущие задачи — то, чем заняться сейчас., Собирает текст сводки из трёх групп задач., TaskView (+2 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (40): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note(), allow_sleep(), keep_awake() (+32 more)

### Community 34 - "parse_message"
Cohesion: 0.07
Nodes (45): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+37 more)

### Community 35 - "init_db"
Cohesion: 0.06
Nodes (61): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, stats_text() (+53 more)

### Community 36 - "test_workbook.py"
Cohesion: 0.22
Nodes (13): create_user(), db(), fixture, db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings() (+5 more)

### Community 37 - "workbook.py"
Cohesion: 0.16
Nodes (25): current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill() (+17 more)

### Community 38 - "Ведомость для ресурсоснабжающих организаций"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

### Community 39 - "handlers/registration.py"
Cohesion: 0.16
Nodes (17): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+9 more)

### Community 40 - "handlers/readings.py"
Cohesion: 0.31
Nodes (13): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+5 more)

### Community 41 - "demo.py"
Cohesion: 0.16
Nodes (17): collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, welcome_residents_text() (+9 more)

### Community 42 - "reading_service.py"
Cohesion: 0.16
Nodes (17): _check_hws_total(), _check_total(), _display(), _fold_locations(), _fold_totals(), datetime, Row, Сохранение и просмотр показаний. (+9 more)

### Community 43 - "config.py"
Cohesion: 0.17
Nodes (9): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., save_report(), generate_workbook(), Path, Собирает книгу из базы и возвращает путь к файлу., generate_statement(), Path (+1 more)

### Community 44 - "reminder_service.py"
Cohesion: 0.32
Nodes (7): debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 45 - "group.py"
Cohesion: 0.26
Nodes (12): _confirm_in_chat(), _dm(), _guidance(), _handle_batch(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Пачка сообщений в чате. Разносит её только председатель. У жителя такое… (+4 more)

### Community 46 - "manual.py"
Cohesion: 0.24
Nodes (12): _answer_as_question(), _import_batch(), manual_readings(), message, Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, Свободный текст, не похожий на показания, — вопрос к Домоведу., Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, Разносит вставленную пачку сообщений и отвечает одной сводкой. (+4 more)

### Community 52 - "import_batch"
Cohesion: 0.24
Nodes (9): BatchResult, import_batch(), Connection, Row, Разбор пачки сообщений: несколько квартир одним текстом. Часть жителей пишет…, Записывает показания из каждого сообщения пачки., «кв. 5» или короткое имя помещения — для строки отчёта., readings_word() (+1 more)

### Community 53 - "reports.py"
Cohesion: 0.36
Nodes (9): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), my_last_readings_text(), Connection (+1 more)

### Community 54 - "parser.py"
Cohesion: 0.33
Nodes (6): _classify(), _has(), _normalize(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., Определяет вид прибора по нормализованной подписи. Возвращает (вид,…

### Community 55 - "is_late"
Cohesion: 0.40
Nodes (5): is_late(), date, Показание передано после срока сбора? Сбор идёт с READINGS_DAY_START по…, parametrize, test_is_late_by_day()

### Community 58 - "states/readings.py"
Cohesion: 0.50
Nodes (3): StatesGroup, Состояния сценария передачи показаний., SubmitReadings

## Knowledge Gaps
- **17 isolated node(s):** `Config`, `graphify`, `Памятки Домоведа`, `Что хранится`, `Что умеет (меню председателя в боте)` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `scheduler.py`, `repository.py`, `admin.py`, `test_common_meters.py`, `main_menu`, `test_batch.py`, `generate_tasks`, `test_council.py`, `build_debtors_statement`, `tasks_import.py`, `test_verification.py`, `faq_service.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`, `test_cleanup.py`, `task_line`, `main.py`, `init_db`, `test_workbook.py`, `handlers/registration.py`, `handlers/readings.py`, `demo.py`, `config.py`, `group.py`, `manual.py`, `reports.py`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `test_common_meters.py`, `init_db`, `test_workbook.py`, `handlers/readings.py`, `demo.py`, `test_council.py`, `test_bare_number_after_a_flat_number_is_not_a_reading`, `group.py`, `manual.py`, `import_batch`, `parser.py`, `ParsedReadings`, `test_amounts.py`, `handle_group_message`, `test_single_letter_needs_a_location_to_count`, `get_apartment_by_number`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `test_common_meters.py`, `test_workbook.py`, `test_batch.py`, `generate_tasks`, `test_council.py`, `demo.py`, `tasks_import.py`, `connect`, `test_verification.py`, `faq_service.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`, `test_cleanup.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Памятки Домоведа` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06775956284153005 - nodes in this community are weakly interconnected._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12121212121212122 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0967741935483871 - nodes in this community are weakly interconnected._