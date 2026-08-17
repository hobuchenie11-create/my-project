# Graph Report - my-project  (2026-08-17)

## Corpus Check
- 81 files · ~37,972 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 942 nodes · 2468 edges · 51 communities (49 shown, 2 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 33 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `26e79d1f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- admin.py
- repository.py
- build_statement
- test_common_meters.py
- main_menu
- test_statements.py
- generate_tasks
- test_amounts.py
- test_council.py
- handlers/registration.py
- tasks_import.py
- connect
- test_verification.py
- Модуль 1. Задачи (только председатель)
- generate_year
- demo.py
- scheduler.py
- handle_group_message
- TaskView
- CLAUDE.md
- build_debtors_statement
- netcheck.py
- task_service.py
- main.py
- parse_message
- init_db
- validation.py
- workbook.py
- current_period
- reminder_service.py
- test_workbook.py
- get_apartment_by_number
- reading_service.py
- handlers/readings.py
- SaveOutcome
- Ведомость непередавших
- parser.py
- config.py
- group.py
- manual.py
- _normalize

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
10. `handle_group_message()` - 25 edges

## Surprising Connections (you probably didn't know these)
- `test_common_meter_is_recognised_by_name()` --calls--> `parse_message()`  [EXTRACTED]
  tests/test_common_meters.py → bot/services/parser.py
- `show_registry()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `send_workbook()` --calls--> `generate_workbook()`  [EXTRACTED]
  bot/handlers/admin.py → excel/workbook.py
- `show_stats()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py
- `show_debtors()` --calls--> `connect()`  [EXTRACTED]
  bot/handlers/admin.py → database/repository.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Ведомости, формируемые 20 числа** — collection_window, statement_rso, statement_debtors, bot_scheduler [INFERRED 0.90]
- **Путь показания от жителя до ведомости** — intake_group_chat, intake_private_bot, reading_validation, bot_services_reading_service, statement_rso [INFERRED 0.90]

## Communities (51 total, 2 thin omitted)

### Community 0 - "admin.py"
Cohesion: 0.14
Nodes (22): back_to_main(), open_admin_menu(), message, Меню председателя: реестр, ведомость, статистика, пользователи, бэкап., Короткое напоминание о сроке сбора — в общий чат дома., Шаблоны — отдельными сообщениями, чтобы житель копировал нужный., Как передать показания по нежилым помещениям и общедомовому прибору., remind_debtors() (+14 more)

### Community 1 - "repository.py"
Cohesion: 0.05
Nodes (72): make_backup(), Path, Резервное копирование базы данных., Копирует базу в backups/ и возвращает путь к копии., describe(), main(), _parse_date(), Удаление тестовых показаний из базы. При запуске системы показания вводили… (+64 more)

### Community 2 - "build_statement"
Cohesion: 0.16
Nodes (20): is_late(), Показание передано после срока сбора? Сбор идёт с READINGS_DAY_START по…, Проверяет и сохраняет одно показание. Возвращает результат проверки., save_reading(), build_statement(), apartment_meters(), Схема базы данных DH OS и справочник видов приборов учета., Список приборов квартиры в порядке опроса в боте. (+12 more)

### Community 3 - "test_common_meters.py"
Cohesion: 0.12
Nodes (21): db(), FakeMessage, _period(), fixture, Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость., У нежилого №2 воды нет — молча записывать её некуда., Нежилые и общедомовой — первыми, чтобы попасть на первую страницу., Житель передал по телефону — председатель вносит сам. (+13 more)

### Community 4 - "main_menu"
Cohesion: 0.15
Nodes (17): cmd_start(), FSMContext, message, Команда /start и справка., show_help(), cancel_keyboard(), main_menu(), ReplyKeyboardMarkup (+9 more)

### Community 5 - "test_statements.py"
Cohesion: 0.13
Nodes (18): Формирование данных ведомости передачи показаний. Структура печатной ведомости…, Statement, StatementRow, Регламент сбора 15–19 числа, Модуль «Сбор показаний», export_statement(), Path, Выгрузка ведомости передачи показаний в Excel (.xlsx). (+10 more)

### Community 6 - "generate_tasks"
Cohesion: 0.14
Nodes (27): generate_tasks(), Тексты напоминаний председателю на сегодня., Создаёт задачи из шаблонов на текущий и ближайшие месяцы. Уже созданные не…, reminders_for_today(), set_status(), Задачи месяца в хронологическом порядке: по сроку, затем по началу окна., tasks_for_period(), _by_title() (+19 more)

### Community 7 - "test_amounts.py"
Cohesion: 0.13
Nodes (20): complete_task(), Закрывает задачу. Сумма попадает в своё поле: аренда или коммуналка. `note` —…, Amount, parse_amount(), Сумма платежа: итог и, если вводили по частям, расшифровка. Председатель платит…, «Квитанции: 214,33 + 155 + 207» — строка для примечания., Разбирает сумму: одно число или несколько через «+». Принимает…, update_task() (+12 more)

### Community 8 - "test_council.py"
Cohesion: 0.10
Nodes (21): council_candidates(), Задачи, которые есть смысл предложить Совету дома. Совету рассказывают о…, conn(), FakeBot, FakeMessage, _one_off(), fixture, Сводка для Совета дома: что в неё попадает и куда она уходит. (+13 more)

### Community 9 - "handlers/registration.py"
Cohesion: 0.16
Nodes (17): confirm_registration(), process_apartment(), process_name(), FSMContext, message, Сценарий регистрации жителя: квартира -> имя -> подтверждение., restart_registration(), _display_number() (+9 more)

### Community 10 - "tasks_import.py"
Cohesion: 0.07
Nodes (61): get_task(), log_task_event(), one_off_tasks(), Разовые задачи (не из годового цикла) — то, что председатель ставит сам., export_year_plan(), Path, _category_code(), _clean() (+53 more)

### Community 11 - "connect"
Cohesion: 0.06
Nodes (72): back_to_admin(), change_task_status(), council_choose(), council_confirmation(), council_stale(), _deliver_digest(), import_plan_file(), import_plan_hint() (+64 more)

### Community 22 - "test_verification.py"
Cohesion: 0.09
Nodes (40): Общедомовые приборы и сроки их поверки., show_verification(), add_years(), ensure_house_meters(), _fmt(), meters_text(), MeterView, next_due() (+32 more)

### Community 23 - "Модуль 1. Задачи (только председатель)"
Cohesion: 0.11
Nodes (18): DH OS — план следующих модулей, Годовой цикл (реализовано), Итоговое сообщение для Совета дома, Как устроен, Модуль 1. Задачи (только председатель), Модуль 2. Домовед — ответы на частые вопросы, Модуль 3. Вкладка для новосёлов, Обкатка до публикации (+10 more)

### Community 24 - "generate_year"
Cohesion: 0.20
Nodes (12): ensure_templates(), generate_year(), Connection, Заводит шаблоны регулярных задач (при первом запуске и после обновлений)., Разворачивает годовой план: задачи из шаблонов на все 12 месяцев., create_task(), test_digest_keeps_amounts_and_notes_out(), Разовые задачи — на отдельном листе, с автоматическим отсчётом срока. (+4 more)

### Community 25 - "demo.py"
Cohesion: 0.16
Nodes (17): collection_reminder_text(), _days_word(), late_submission_text(), date, Тексты для жителей (памятка/приветствие/уведомления)., Сообщение жителю, передавшему показания после срока сбора., Короткое напоминание в чат дома: до какого числа передать показания. Дата…, welcome_residents_text() (+9 more)

### Community 26 - "scheduler.py"
Cohesion: 0.24
Nodes (14): Bot, datetime, Фоновый планировщик DH OS. Отвечает за автоматические действия по календарю: •…, Сформировать ведомость со всеми собранными показаниями и отправить её., Напоминания председателю по задачам: пора начинать, срок, просрочка., Бесконечный цикл: выполняет задачи дня не более одного раза за сутки., Разослать напоминания должникам за текущий период. Возвращает число…, Сформировать ведомость непередавших и отправить её председателям. (+6 more)

### Community 27 - "handle_group_message"
Cohesion: 0.14
Nodes (21): handle_group_message(), FakeBot, FakeMessage, Приём показаний из общего чата: в чью квартиру они попадают., Чужой чат — предупреждение в лог: так видно смену ID чата дома., Реакции в чате запрещены: показания записаны, но это должно быть видно., Ни реакции, ни лички — отвечаем в чате, иначе житель без подтверждения., Сообщение в общем чате дома от жителя. (+13 more)

### Community 28 - "TaskView"
Cohesion: 0.18
Nodes (3): Окно выполнения уже открылось и ещё не закрыто., До срока осталось TASK_SOON_DAYS дней или меньше — пора поторопиться., TaskView

### Community 30 - "build_debtors_statement"
Cohesion: 0.33
Nodes (8): build_debtors_statement(), generate_debtors_statement(), Path, Ведомость непередавших показания (печатная форма). Формируется по кнопке…, Собирает ведомость непередавших. Возвращает путь и число должников., _setup_print(), _short(), test_debtors_statement()

### Community 31 - "netcheck.py"
Cohesion: 0.18
Nodes (15): check(), _port_open(), Подбор рабочего прокси для подключения к Telegram. Запуск: python -m…, _try_http(), _try_socks(), build_socks_connector(), make_session(), normalize_proxy_url() (+7 more)

### Community 32 - "task_service.py"
Cohesion: 0.16
Nodes (23): _clamp_day(), council_digest(), _digest_text(), _fmt_date(), _month_period(), month_plan_text(), one_off_text(), period_title() (+15 more)

### Community 33 - "main.py"
Cohesion: 0.15
Nodes (17): allow_sleep(), keep_awake(), Не даём компьютеру уснуть, пока бот работает. Показания приходят в чат весь…, Просит систему не уходить в спящий режим. True — просьба принята., Возвращает обычное поведение — вызывается при остановке бота., _apply_registry_if_present(), _log_chats(), main() (+9 more)

### Community 34 - "parse_message"
Cohesion: 0.10
Nodes (34): parse_message(), Тесты разбора реальных сообщений жителей (из шаблонов и чата дома)., Реальное сообщение жителя: всё в строку, подписи со слешем., «кв38» — это 38-я квартира, а не 8-я: цифры номера не съедаются., Запятая между цифрами — дробная часть, а не разделитель приборов., «Кв,, 29» — жители ставят по две запятые, скобки, тире., Сообщение жителя целиком: двойные запятые в каждой строке., Квартиру назвали, но номер не читается — это не «номер не указан». (+26 more)

### Community 35 - "init_db"
Cohesion: 0.07
Nodes (41): init_db(), Connection, Path, Создание схемы БД и первичное заполнение реестра квартир. Запускается…, Общедомовой прибор учёта — такая же строка реестра, со своим счётчиком., _seed_common(), _seed_nonresidential(), _seed_residential() (+33 more)

### Community 36 - "validation.py"
Cohesion: 0.20
Nodes (14): check_reading(), CheckResult, parse_value(), Проверка вводимых показаний., Сверяет новое показание с предыдущим. Меньше предыдущего — ошибка (замену…, Разбирает число из текста пользователя (принимает запятую и точку)., Вопрос посреди передачи показаний должен распознаваться как вопрос., test_first_reading_always_ok() (+6 more)

### Community 37 - "workbook.py"
Cohesion: 0.09
Nodes (43): category_label(), status_label(), DataValidation, fill_statement_sheet(), Заполняет готовый лист ведомостью — используется и в отдельном файле, и как…, Готовит лист к печати: А4 книжная, вписать по ширине, шапка на каждом листе., _setup_print(), Единый визуальный стиль DH OS для всех модулей Excel. Цветовая схема… (+35 more)

### Community 38 - "current_period"
Cohesion: 0.29
Nodes (10): send_statement(), show_stats(), current_period(), period_title(), date, Connection, stats_text(), generate_statement() (+2 more)

### Community 39 - "reminder_service.py"
Cohesion: 0.28
Nodes (8): show_debtors(), debtors_text(), pending_targets(), Connection, Автоматические напоминания о передаче показаний (Этап 7). Схема напоминаний по…, Кому отправить напоминание: зарегистрированные жители-должники., Список должников по передаче показаний для председателя (Этап 6)., ReminderTarget

### Community 40 - "test_workbook.py"
Cohesion: 0.27
Nodes (11): create_user(), db(), fixture, _build(), Книга Excel «Сбор показаний»: состав листов и наполнение., test_control_and_settings(), test_history_and_current_sheets(), test_registry_columns_and_rows() (+3 more)

### Community 41 - "get_apartment_by_number"
Cohesion: 0.19
Nodes (18): _fold_totals(), Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный. Такая строка…, Раскладывает распознанные показания на приборы конкретной квартиры. Один…, _resolve_meter_kind(), save_parsed_readings(), get_apartment_by_number(), test_late_flag_stored_for_parsed_message(), conn() (+10 more)

### Community 42 - "reading_service.py"
Cohesion: 0.18
Nodes (17): _get_user(), Message, Просмотр своих показаний и истории передач., show_history(), show_last(), _display(), history_text(), last_reading_value() (+9 more)

### Community 43 - "handlers/readings.py"
Cohesion: 0.27
Nodes (13): _ask_next_meter(), cancel_submission(), _finish(), _looks_like_question(), process_value(), FSMContext, Message, Передача показаний: бот по очереди опрашивает приборы квартиры. (+5 more)

### Community 44 - "SaveOutcome"
Cohesion: 0.20
Nodes (7): ParsedReadings, Квартиру назвали, но номер не разобрали — подставлять чужую нельзя., _check_hws_total(), _check_total(), Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим., Итог записи показаний из одного сообщения (общий чат)., SaveOutcome

### Community 45 - "Ведомость непередавших"
Cohesion: 0.50
Nodes (5): Панель председателя, Цветовая схема DH OS, Напоминания жителям, Ведомость непередавших, Книга Excel из 5 листов

### Community 46 - "parser.py"
Cohesion: 0.17
Nodes (12): Реестр квартир, _classify(), _has(), Разбор показаний из свободного текста (сообщения в общем чате дома). Словарь…, Определяет вид прибора по нормализованной подписи. Возвращает (вид,…, Правило суммы ГВС, Приём показаний из общего чата, Приём показаний через бота (+4 more)

### Community 47 - "config.py"
Cohesion: 0.22
Nodes (6): Config, Конфигурация DH OS. Значения читаются из файла .env в корне проекта., cmd_chatid(), message, Служебные команды, доступные в любом чате., Показывает ID чата — нужен для GROUP_CHAT_ID и COUNCIL_CHAT_ID в .env. Команды…

### Community 48 - "group.py"
Cohesion: 0.31
Nodes (8): _dm(), _guidance(), Message, Прием показаний из общего чата дома. Бот разбирает сообщения по шаблонам…, Подсказку шлём в личку; если не дошла — отвечаем в чате (житель должен её…, Пробует отправить сообщение отправителю в личку. True, если получилось., Тихая отметка в чате, что показание принято (без текстового сообщения)., _react_ok()

### Community 49 - "manual.py"
Cohesion: 0.50
Nodes (3): manual_readings(), message, Ручной ввод показаний председателем — в личном чате с ботом. Нежилые помещения…

## Knowledge Gaps
- **16 isolated node(s):** `Config`, `graphify`, `Что хранится`, `Что умеет (меню председателя в боте)`, `Итоговое сообщение для Совета дома` (+11 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `connect()` connect `connect` to `admin.py`, `repository.py`, `build_statement`, `test_common_meters.py`, `main_menu`, `test_statements.py`, `test_amounts.py`, `test_council.py`, `handlers/registration.py`, `tasks_import.py`, `test_verification.py`, `demo.py`, `scheduler.py`, `handle_group_message`, `build_debtors_statement`, `init_db`, `workbook.py`, `current_period`, `reminder_service.py`, `test_workbook.py`, `get_apartment_by_number`, `reading_service.py`, `handlers/readings.py`, `manual.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `parse_message()` connect `parse_message` to `build_statement`, `test_common_meters.py`, `validation.py`, `test_council.py`, `get_apartment_by_number`, `test_workbook.py`, `SaveOutcome`, `parser.py`, `group.py`, `manual.py`, `_normalize`, `demo.py`, `handle_group_message`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Why does `init_db()` connect `init_db` to `main.py`, `repository.py`, `test_common_meters.py`, `build_statement`, `test_statements.py`, `generate_tasks`, `test_amounts.py`, `test_council.py`, `test_workbook.py`, `get_apartment_by_number`, `connect`, `tasks_import.py`, `test_verification.py`, `demo.py`, `handle_group_message`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **What connects `Config`, `graphify`, `Что хранится` to the rest of the system?**
  _16 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `admin.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1422924901185771 - nodes in this community are weakly interconnected._
- **Should `repository.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05473684210526316 - nodes in this community are weakly interconnected._
- **Should `test_common_meters.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12318840579710146 - nodes in this community are weakly interconnected._