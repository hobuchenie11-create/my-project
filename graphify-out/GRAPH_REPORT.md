# Graph Report - my-project  (2026-08-19)

## Corpus Check
- 90 files · ~42,463 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1066 nodes · 2770 edges · 52 communities (49 shown, 3 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e481396c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- scheduler.py
- repository.py
- admin.py
- test_common_meters.py
- handlers/readings.py
- import_registry
- generate_tasks
- task_service.py
- test_council.py
- demo.py
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
- export_year_plan
- TaskView
- main.py
- parse_message
- build_statement
- test_workbook.py
- workbook.py
- Ведомость непередавших
- init_db
- verification_service.py
- texts.py
- reading_service.py
- current_period
- reminder_service.py
- test_statements.py
- MeterView
- README.md

## God Nodes (most connected - your core abstractions)
1. `connect()` - 85 edges
2. `parse_message()` - 67 edges
3. `get_apartment_by_number()` - 44 edges
4. `init_db()` - 42 edges
5. `save_parsed_readings()` - 39 edges
6. `current_period()` - 33 edges
7. `build_statement()` - 33 edges
8. `generate_tasks()` - 30 edges
9. `save_reading()` - 29 edges
10. `handle_group_message()` - 26 edges

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

## Communities (52 total, 3 thin omitted)

### Community 0 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 1 - "repository.py"
Cohesion: 0.07
Nodes (61): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), last_reading_value(), my_last_readings_text() (+53 more)

### Community 2 - "admin.py"
Cohesion: 0.13
Nodes (24): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., О чём спрашивали жители, а памятки для ответа нет. (+16 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.07
Nodes (39): _answer_as_question(), manual_readings(), message, Показания текстом в личном чате с ботом — без диалога по кнопке. Житель…, Свободный текст, не похожий на показания, — вопрос к Домоведу., Помещение, в которое пойдут показания, либо текст с объяснением. Житель может…, _resolve(), db() (+31 more)

### Community 4 - "handlers/readings.py"
Cohesion: 0.06
Nodes (55): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+47 more)

### Community 5 - "import_registry"
Cohesion: 0.11
Nodes (24): Реестр квартир, layout_label(), Короткая подпись планировки для реестра, например «ХВС×2 · ГВС×2»., _counts_from_label(), _find_header_row(), generate_template(), import_registry(), _is_apartment_number() (+16 more)

### Community 6 - "generate_tasks"
Cohesion: 0.15
Nodes (25): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки. (+17 more)

### Community 7 - "task_service.py"
Cohesion: 0.14
Nodes (28): complete_task(), council_candidates(), council_digest(), _digest_text(), _fmt_date(), _month_period(), month_plan_text(), one_off_text() (+20 more)

### Community 8 - "test_council.py"
Cohesion: 0.11
Nodes (19): conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания. (+11 more)

### Community 9 - "demo.py"
Cohesion: 0.20
Nodes (16): send_debtors_doc(), period_title(), late_submission_text(), Сообщение жителю, передавшему показания после срока сбора., build_demo(), _checklist(), _plain(), _print_summary() (+8 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.13
Nodes (32): _category_code(), _clean(), _create_one_off(), _header_map(), _import_meters(), _import_one_off(), _import_tasks(), ImportResult (+24 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (76): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+68 more)

### Community 22 - "test_verification.py"
Cohesion: 0.20
Nodes (20): Row, Записывает проведённую поверку и пересчитывает следующий срок., register_verification(), view(), get_house_meter(), update_house_meter(), _meter(), Поверка общедомовых приборов: автоматический расчёт сроков. (+12 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "faq_service.py"
Cohesion: 0.07
Nodes (53): answer_question(), back_to_categories(), callback_query, CallbackQuery, message, Памятки Домоведа: разделы, тексты и ответы на вопросы жителей., Ищет ответ на вопрос жителя. False — вопрос остался без ответа. Вызывается из…, Отправляет памятку — с картинкой, если она к ней приложена. (+45 more)

### Community 25 - "get_apartment_by_number"
Cohesion: 0.19
Nodes (20): Раскладывает распознанные показания на приборы конкретной квартиры. Один…, save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), Раскладка распознанных показаний на приборы конкретной квартиры., Прибор один, а мест названо два — записывать наугад нельзя., У кв. 1 учёт раздельный — подписи по местам работают как раньше., Прибор один, названо одно место — это он и есть (счётчик в санузле). (+12 more)

### Community 26 - "test_amounts.py"
Cohesion: 0.09
Nodes (31): Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания. (+23 more)

### Community 27 - "handle_group_message"
Cohesion: 0.10
Nodes (32): _confirm_in_chat(), _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подтверждение приёма в чате — способом из CHAT_CONFIRM. Реакции в группе можно…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её… (+24 more)

### Community 28 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

### Community 30 - "generate_year"
Cohesion: 0.17
Nodes (13): _clamp_day(), ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., День месяца с учётом коротких месяцев (30 февраля не бывает)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out() (+5 more)

### Community 31 - "export_year_plan"
Cohesion: 0.16
Nodes (28): get_task(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, import_year_plan(), Path, Переносит правки из файла в базу. Файл не изменяется. (+20 more)

### Community 32 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 33 - "main.py"
Cohesion: 0.06
Nodes (42): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…, Видит ли бот обычные сообщения именно в этом чате. Одного…, _visibility_note() (+34 more)

### Community 34 - "parse_message"
Cohesion: 0.05
Nodes (59): _classify(), _has(), _normalize(), parse_message(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю. (+51 more)

### Community 35 - "build_statement"
Cohesion: 0.17
Nodes (18): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Формирование данных ведомости передачи показаний. Структура печатной ведомости…, StatementRow, stats_text(), apartment_meters() (+10 more)

### Community 36 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 37 - "workbook.py"
Cohesion: 0.10
Nodes (41): category_label(), status_label(), current_readings_rows(), Лист «Реестр квартир»: квартира + житель + последняя передача., Лист «Текущие показания»: последнее значение каждого прибора., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+33 more)

### Community 38 - "Ведомость непередавших"
Cohesion: 0.50
Nodes (5): Панель председателя, Цветовая схема DH OS, Напоминания жителям, Ведомость непередавших, Книга Excel из 5 листов

### Community 39 - "init_db"
Cohesion: 0.15
Nodes (20): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential() (+12 more)

### Community 40 - "verification_service.py"
Cohesion: 0.16
Nodes (18): add_years(), ensure_house_meters(), _fmt(), meters_text(), next_due(), Connection, date, Поверка общедомовых приборов учёта (тепло, ГВС, ХВС). У каждого прибора свой… (+10 more)

### Community 41 - "texts.py"
Cohesion: 0.19
Nodes (12): collection_reminder_text(), _days_word(), date, Тексты для жителей (памятка/приветствие/уведомления)., Три сообщения для чата: пояснение и два шаблона по отдельности., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, template_messages(), welcome_residents_text() (+4 more)

### Community 42 - "reading_service.py"
Cohesion: 0.18
Nodes (13): _check_hws_total(), _check_total(), _display(), _fold_locations(), _fold_totals(), Row, Сохранение и просмотр показаний., Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка… (+5 more)

### Community 43 - "current_period"
Cohesion: 0.25
Nodes (10): send_statement(), send_workbook(), current_period(), save_report(), generate_workbook(), Собирает книгу из базы и возвращает путь к файлу., generate_statement(), Path (+2 more)

### Community 44 - "reminder_service.py"
Cohesion: 0.28
Nodes (8): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 45 - "test_statements.py"
Cohesion: 0.11
Nodes (24): Statement, Регламент сбора 15–19 числа, Модуль «Сбор показаний», export_statement(), fill_statement_sheet(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx)., Отдельный файл ведомости — его председатель отправляет ресурсникам. (+16 more)

## Knowledge Gaps
- **17 isolated node(s):** `Config`, `graphify`, `Памятки Домоведа`, `Что хранится`, `Что умеет (меню председателя в боте)` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `scheduler.py`, `repository.py`, `admin.py`, `test_common_meters.py`, `handlers/readings.py`, `import_registry`, `test_council.py`, `demo.py`, `tasks_import.py`, `faq_service.py`, `test_amounts.py`, `handle_group_message`, `test_cleanup.py`, `main.py`, `test_workbook.py`, `init_db`, `verification_service.py`, `current_period`, `reminder_service.py`, `test_statements.py`?**
  _High betweenness centrality (0.116) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `test_common_meters.py`, `handlers/readings.py`, `build_statement`, `test_workbook.py`, `test_council.py`, `demo.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `test_common_meters.py`, `test_workbook.py`, `build_statement`, `generate_tasks`, `test_council.py`, `demo.py`, `verification_service.py`, `connect`, `test_statements.py`, `test_verification.py`, `faq_service.py`, `get_apartment_by_number`, `test_amounts.py`, `handle_group_message`, `test_cleanup.py`, `export_year_plan`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Памятки Домоведа` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06861239119303636 - nodes in this community are weakly interconnected._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12666666666666668 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07198228128460686 - nodes in this community are weakly interconnected._