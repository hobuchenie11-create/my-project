# Graph Report - my-project  (2026-08-19)

## Corpus Check
- 92 files · ~44,279 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1113 nodes · 2907 edges · 63 communities (57 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 34 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `eb9f0566`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- scheduler.py
- repository.py
- admin.py
- test_common_meters.py
- handlers/readings.py
- test_batch.py
- generate_tasks
- task_service.py
- test_council.py
- build_debtors_statement
- tasks_import.py
- connect
- verification_service.py
- Модуль 1. Задачи (только председатель)
- faq_service.py
- get_apartment_by_number
- test_amounts.py
- handle_group_message
- test_cleanup.py
- CLAUDE.md
- generate_year
- task_line
- TaskView
- main.py
- parse_message
- test_statements.py
- test_workbook.py
- workbook.py
- Ведомость для ресурсоснабжающих организаций
- registry_summary
- export_year_plan
- demo.py
- save_parsed_readings
- test_verification.py
- init_db.py
- group.py
- manual_readings
- README.md
- manual.py
- init_db
- _normalize
- build_statement
- FakeBot
- import_registry
- Msg
- MeterView
- template_messages
- show_special
- main

## God Nodes (most connected - your core abstractions)
1. `connect()` - 93 edges
2. `parse_message()` - 69 edges
3. `get_apartment_by_number()` - 49 edges
4. `init_db()` - 44 edges
5. `save_parsed_readings()` - 41 edges
6. `current_period()` - 35 edges
7. `build_statement()` - 33 edges
8. `handle_group_message()` - 32 edges
9. `generate_tasks()` - 30 edges
10. `save_reading()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `test_common_meter_is_recognised_by_name()` --calls--> `parse_message()`  [EXTRACTED]
  tests/test_common_meters.py → bot/services/parser.py
- `test_default_house_meters()` --calls--> `house_meters()`  [EXTRACTED]
  tests/test_verification.py → database/repository.py
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_debtors()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (63 total, 6 thin omitted)

### Community 0 - "scheduler.py"
Cohesion: 0.15
Nodes (21): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+13 more)

### Community 1 - "repository.py"
Cohesion: 0.07
Nodes (59): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+51 more)

### Community 2 - "admin.py"
Cohesion: 0.15
Nodes (27): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., О чём спрашивали жители, а памятки для ответа нет., remind_debtors(), send_backup(), send_debtors_doc() (+19 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.10
Nodes (28): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+20 more)

### Community 4 - "handlers/readings.py"
Cohesion: 0.06
Nodes (52): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+44 more)

### Community 5 - "test_batch.py"
Cohesion: 0.14
Nodes (21): _classify(), _has(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает из строки дату, время и имя автора скопированного сообщения., Делит вставленную пачку на отдельные сообщения — по строке с квартирой.…, split_messages(), strip_chat_meta() (+13 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "task_service.py"
Cohesion: 0.22
Nodes (13): _clamp_day(), council_digest(), _digest_text(), _month_period(), month_plan_text(), period_title(), date, Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные… (+5 more)

### Community 8 - "test_council.py"
Cohesion: 0.10
Nodes (21): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+13 more)

### Community 9 - "build_debtors_statement"
Cohesion: 0.33
Nodes (8): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short(), test_debtors_statement()

### Community 10 - "tasks_import.py"
Cohesion: 0.15
Nodes (30): _category_code(), _clean(), _create_one_off(), _header_map(), _import_meters(), _import_one_off(), _import_tasks(), ImportResult (+22 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (72): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+64 more)

### Community 22 - "verification_service.py"
Cohesion: 0.16
Nodes (21): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), next_due(), Connection (+13 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "faq_service.py"
Cohesion: 0.07
Nodes (52): answer_question(), back_to_categories(), callback_query, CallbackQuery, message, Памятки Домоведа: разделы, тексты и ответы на вопросы жителей., Ищет ответ на вопрос жителя. False — вопрос остался без ответа. Вызывается из…, Отправляет памятку — с картинкой, если она к ней приложена. (+44 more)

### Community 25 - "get_apartment_by_number"
Cohesion: 0.14
Nodes (20): get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn(), fixture, Раскладка распознанных показаний на приборы конкретной квартиры., Прибор один, а мест названо два — записывать наугад нельзя., У кв. 1 учёт раздельный — подписи по местам работают как раньше., Прибор один, названо одно место — это он и есть (счётчик в санузле). (+12 more)

### Community 26 - "test_amounts.py"
Cohesion: 0.07
Nodes (39): Реестр квартир, complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, check_reading(), CheckResult, parse_amount(), parse_value() (+31 more)

### Community 27 - "handle_group_message"
Cohesion: 0.19
Nodes (21): handle_group_message(), FakeMessage, Приём показаний из общего чата: в чью квартиру они попадают., Чужой чат — предупреждение в лог: так видно смену ID чата дома., Реакции в чате запрещены: показания записаны, но это должно быть видно., Реакции в чате запрещены — подтверждаем короткой строкой (CHAT_CONFIRM=auto)., Сообщение в общем чате дома от жителя., «Кв,, 29» от жителя кв. 49 — записываем в 29-ю, а не в квартиру автора. (+13 more)

### Community 28 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

### Community 30 - "generate_year"
Cohesion: 0.20
Nodes (12): ensure_templates(), generate_year(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., set_status(), create_task(), test_digest_keeps_amounts_and_notes_out() (+4 more)

### Community 31 - "task_line"
Cohesion: 0.22
Nodes (13): _fmt_date(), one_off_text(), Row, Одна строка задачи для списка в боте., Просроченные и текущие задачи — то, чем заняться сейчас., Разовые задачи председателя — то, что он планирует сам., task_line(), urgent_text() (+5 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (40): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note(), allow_sleep(), keep_awake() (+32 more)

### Community 34 - "parse_message"
Cohesion: 0.07
Nodes (49): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+41 more)

### Community 35 - "test_statements.py"
Cohesion: 0.13
Nodes (18): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx)., Отдельный файл ведомости — его председатель отправляет ресурсникам. (+10 more)

### Community 36 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (41): category_label(), status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+33 more)

### Community 38 - "Ведомость для ресурсоснабжающих организаций"
Cohesion: 0.31
Nodes (9): Панель председателя, Регламент сбора 15–19 числа, Цветовая схема DH OS, Модуль «Сбор показаний», Передача после срока, Напоминания жителям, Ведомость непередавших, Ведомость для ресурсоснабжающих организаций (+1 more)

### Community 39 - "registry_summary"
Cohesion: 0.36
Nodes (7): _display_number(), find_apartment(), Connection, Row, Операции с реестром квартир., Текстовый реестр квартир с отметкой о сдаче показаний за период., registry_summary()

### Community 40 - "export_year_plan"
Cohesion: 0.15
Nodes (29): get_task(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, import_year_plan(), Path, Переносит правки из файла в базу. Файл не изменяется. (+21 more)

### Community 41 - "demo.py"
Cohesion: 0.14
Nodes (19): Короткое напоминание о сроке сбора — в общий чат дома., send_chat_reminder(), collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора. (+11 more)

### Community 42 - "save_parsed_readings"
Cohesion: 0.15
Nodes (16): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), _display(), _fold_locations(), _fold_totals(), Row (+8 more)

### Community 43 - "test_verification.py"
Cohesion: 0.22
Nodes (18): Записывает проведённую поверку и пересчитывает следующий срок., register_verification(), get_house_meter(), update_house_meter(), _meter(), Поверка общедомовых приборов: автоматический расчёт сроков., У каждого прибора свой межповерочный интервал., После проведённой поверки срок пересчитывается на следующий цикл. (+10 more)

### Community 44 - "init_db.py"
Cohesion: 0.19
Nodes (16): Connection, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential(), apartment_meters(), layout_label() (+8 more)

### Community 45 - "group.py"
Cohesion: 0.19
Nodes (15): _confirm_in_chat(), _dm(), _guidance(), _handle_batch(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Пачка сообщений в чате. Разносит её только председатель. У жителя такое… (+7 more)

### Community 46 - "manual_readings"
Cohesion: 0.25
Nodes (11): _answer_as_question(), _import_batch(), manual_readings(), message, Свободный текст, не похожий на показания, — вопрос к Домоведу., Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, Разносит вставленную пачку сообщений и отвечает одной сводкой., _resolve() (+3 more)

### Community 52 - "manual.py"
Cohesion: 0.21
Nodes (10): Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, BatchResult, import_batch(), Connection, Row, Разбор пачки сообщений: несколько квартир одним текстом. Часть жителей пишет…, Записывает показания из каждого сообщения пачки., «кв. 5» или короткое имя помещения — для строки отчёта. (+2 more)

### Community 53 - "init_db"
Cohesion: 0.13
Nodes (15): init_db(), Path, db(), fixture, test_export_statement(), conn(), fixture, conn() (+7 more)

### Community 55 - "build_statement"
Cohesion: 0.22
Nodes (15): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, stats_text(), parametrize, Регламент сбора: 15–19 — срок, с 20 числа — «после срока сбора»., test_is_late_by_day() (+7 more)

### Community 57 - "import_registry"
Cohesion: 0.21
Nodes (14): _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number(), _pick_sheet(), Connection, Path (+6 more)

### Community 58 - "Msg"
Cohesion: 0.17
Nodes (7): Msg, Вставили в чат показаний — тоже разносим, сводка уходит в личку., У жителя подстановка своей квартиры остаётся — это привычный ввод., test_chairman_pastes_into_the_readings_chat(), test_resident_message_without_a_number_still_uses_their_flat(), Показания разбираются раньше — до памяток они доходить не должны., test_readings_are_not_treated_as_a_question()

### Community 60 - "template_messages"
Cohesion: 0.33
Nodes (6): Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., send_templates(), Три сообщения для чата: пояснение и два шаблона по отдельности., template_messages(), Шаблоны уходят по отдельности — чтобы житель копировал нужный., test_templates_are_separate_messages()

### Community 61 - "show_special"
Cohesion: 0.50
Nodes (4): Как передать показания по нежилым помещениям и общедомовому прибору., show_special(), Подсказка председателю: как передать нежилые и общедомовой прибор., special_readings_text()

## Knowledge Gaps
- **17 isolated node(s):** `Config`, `graphify`, `Памятки Домоведа`, `Что хранится`, `Что умеет (меню председателя в боте)` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `scheduler.py`, `repository.py`, `admin.py`, `test_common_meters.py`, `handlers/readings.py`, `test_batch.py`, `test_council.py`, `build_debtors_statement`, `verification_service.py`, `faq_service.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`, `test_cleanup.py`, `main.py`, `test_statements.py`, `test_workbook.py`, `demo.py`, `init_db.py`, `group.py`, `manual_readings`, `init_db`, `import_registry`, `Msg`, `main`?**
  _High betweenness centrality (0.137) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `test_common_meters.py`, `handlers/readings.py`, `test_batch.py`, `test_workbook.py`, `test_council.py`, `demo.py`, `save_parsed_readings`, `group.py`, `manual_readings`, `manual.py`, `_normalize`, `build_statement`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Why does `handle_group_message()` connect `handle_group_message` to `repository.py`, `admin.py`, `parse_message`, `handlers/readings.py`, `test_batch.py`, `demo.py`, `save_parsed_readings`, `connect`, `group.py`, `manual_readings`, `get_apartment_by_number`, `Msg`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Памятки Домоведа` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `scheduler.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06994535519125683 - nodes in this community are weakly interconnected._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14838709677419354 - nodes in this community are weakly interconnected._