# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 79 files · ~35,247 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 878 nodes · 2305 edges · 36 communities (35 shown, 1 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2b6bfbe2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- test_cleanup.py
- workbook.py
- demo.py
- init_db
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
- group.py
- task_line
- CLAUDE.md
- council_digest
- task_service.py
- main.py
- parse_message
- reading_service.py
- parser.py
- test_workbook.py

## God Nodes (most connected - your core abstractions)
1. `connect()` - 64 edges
2. `parse_message()` - 41 edges
3. `init_db()` - 37 edges
4. `get_apartment_by_number()` - 31 edges
5. `generate_tasks()` - 30 edges
6. `current_period()` - 29 edges
7. `save_reading()` - 29 edges
8. `build_statement()` - 29 edges
9. `save_parsed_readings()` - 26 edges
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

## Communities (36 total, 1 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.06
Nodes (66): Bot, back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., remind_debtors(), send_backup() (+58 more)

### Community 1 - "repository.py"
Cohesion: 0.09
Nodes (47): active_task_templates(), add_reading(), add_verification(), all_readings(), apartments_submitted(), _apply_migrations(), create_schema(), current_readings_rows() (+39 more)

### Community 2 - "test_cleanup.py"
Cohesion: 0.12
Nodes (26): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+18 more)

### Community 3 - "workbook.py"
Cohesion: 0.10
Nodes (38): status_label(), Лист «Реестр квартир»: квартира + житель + последняя передача., registry_rows(), DataValidation, Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема…, Оформляет строку заголовков таблицы и задаёт ширину колонок., room_fill(), room_label() (+30 more)

### Community 4 - "demo.py"
Cohesion: 0.07
Nodes (39): Реестр квартир, collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, Сообщение жителю, передавшему показания после срока сбора. (+31 more)

### Community 5 - "init_db"
Cohesion: 0.07
Nodes (56): Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), Connection, Statement, StatementRow, init_db(), Connection (+48 more)

### Community 6 - "generate_tasks"
Cohesion: 0.16
Nodes (23): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), _by_title(), Модуль «Задачи председателя»: годовой цикл, статусы, напоминания, сводки., Аренда и коммуналка — разные задачи и разные поля сумм., Коммуналка до 18-го: с 15 числа задача считается горящей. (+15 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.09
Nodes (31): Amount, check_reading(), CheckResult, parse_amount(), parse_value(), Проверка вводимых показаний., Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания. (+23 more)

### Community 8 - "test_council.py"
Cohesion: 0.14
Nodes (12): conn(), FakeBot, FakeMessage, fixture, Сводка для Совета дома: что в неё попадает и куда она уходит., Чат показаний подключён, чат Совета — нет: жителям не пишем., Обсуждения Совета не разбираются как показания., Напоминание в чат: срок берётся из настроек и текущего месяца. (+4 more)

### Community 9 - "handlers/readings.py"
Cohesion: 0.06
Nodes (49): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext (+41 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.08
Nodes (60): get_task(), log_task_event(), update_task(), export_year_plan(), Path, _category_code(), _clean(), _create_one_off() (+52 more)

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
Cohesion: 0.18
Nodes (12): ensure_templates(), generate_year(), Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), task_exists(), test_digest_keeps_amounts_and_notes_out(), Разовые задачи — на отдельном листе, с автоматическим отсчётом срока. (+4 more)

### Community 25 - "reports.py"
Cohesion: 0.42
Nodes (8): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), history_text(), my_last_readings_text(), Connection

### Community 27 - "group.py"
Cohesion: 0.10
Nodes (26): _dm(), _guidance(), handle_group_message(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения). (+18 more)

### Community 28 - "task_line"
Cohesion: 0.19
Nodes (15): Каждую открытую задачу отправляем отдельно — с кнопками управления., Разовые задачи председателя — с кнопками управления у каждой., show_one_off(), show_urgent(), category_label(), one_off_text(), Одна строка задачи для списка в боте., Разовые задачи председателя — то, что он планирует сам. (+7 more)

### Community 31 - "council_digest"
Cohesion: 0.18
Nodes (16): complete_task(), council_candidates(), council_digest(), _month_period(), Connection, Row, Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, Информационная сводка для Совета дома. Только заголовки, сроки и статусы —… (+8 more)

### Community 32 - "task_service.py"
Cohesion: 0.11
Nodes (16): _clamp_day(), _digest_text(), _fmt_date(), month_plan_text(), period_title(), date, Задачи председателя: годовой цикл, статусы, напоминания, сводки. Регулярные…, Окно выполнения уже открылось и ещё не закрыто. (+8 more)

### Community 33 - "main.py"
Cohesion: 0.07
Nodes (36): cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env., allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята. (+28 more)

### Community 34 - "parse_message"
Cohesion: 0.12
Nodes (28): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+20 more)

### Community 35 - "reading_service.py"
Cohesion: 0.16
Nodes (18): _check_hws_total(), _display(), last_reading_value(), datetime, Row, Сохранение и просмотр показаний., Квитанция-подтверждение после передачи показаний (Этап 5)., Итог записи показаний из одного сообщения (общий чат). (+10 more)

### Community 40 - "parser.py"
Cohesion: 0.20
Nodes (8): _classify(), _has(), _normalize(), ParsedReadings, Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Убирает разделители, оставляя только буквы, для сопоставления по словарю., Квартиру назвали, но номер не разобрали — подставлять чужую нельзя.

### Community 41 - "test_workbook.py"
Cohesion: 0.36
Nodes (9): create_user(), _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows(), test_sheets_present(), test_status_no_telegram_and_not_submitted() (+1 more)

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `test_cleanup.py`, `demo.py`, `init_db`, `test_amounts.py`, `test_council.py`, `handlers/readings.py`, `tasks_import.py`, `test_verification.py`, `reports.py`, `group.py`, `task_line`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `reading_service.py`, `demo.py`, `init_db`, `test_amounts.py`, `parser.py`, `test_workbook.py`, `group.py`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `test_cleanup.py`, `demo.py`, `reading_service.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `test_workbook.py`, `tasks_import.py`, `connect`, `test_verification.py`, `group.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0624048706240487 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08687943262411348 - nodes in this community are weakly interconnected._
- **Should `test_cleanup.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1206896551724138 - nodes in this community are weakly interconnected._