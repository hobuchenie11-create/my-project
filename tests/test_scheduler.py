"""Календарь бота: когда что уходит и почему не повторяется.

Объявление о завершении сбора однажды ушло в чат дома трижды: отметка
«сегодня уже отправлено» жила в памяти процесса, а бота в тот день
перезапускали. Теперь отметка в базе, и рассылку проверяем именно на
повторных запусках.
"""
import asyncio
from dataclasses import replace
from datetime import datetime

import pytest

from bot import scheduler
from bot.config import config
from database import repository
from database.init_db import init_db

GROUP_CHAT = -1001111111111


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """База во временной папке — и планировщик, и отметки идут в неё."""
    path = tmp_path / "scheduler.db"
    init_db(path, apartments_count=2, nonresidential_count=0)
    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    return path


@pytest.fixture()
def bot(monkeypatch):
    """Планировщик без Telegram: остаются только рассылки, которые проверяем."""
    async def noop(*args, **kwargs):
        return 0

    for name in ("send_reminders", "send_chat_reminder",
                 "send_debtors_statement", "send_monthly_statement",
                 "send_oek_registry", "send_task_reminders"):
        monkeypatch.setattr(scheduler, name, noop)
    # Config заморожен — подменяем целиком, а не отдельное поле
    monkeypatch.setattr(scheduler, "config",
                        replace(config, group_chat_id=GROUP_CHAT))
    return FakeBot()


def _tick(bot, moment):
    asyncio.run(scheduler._tick(bot, moment))


def test_announcement_waits_for_its_hour(db, bot):
    """В 14:00 уходит ведомость председателю, но не объявление жителям."""
    _tick(bot, datetime(2026, 8, config.announce_day, config.statement_hour))
    assert bot.sent == []

    _tick(bot, datetime(2026, 8, config.announce_day, config.announce_hour))
    assert [chat for chat, _ in bot.sent] == [GROUP_CHAT]
    assert "завершён" in bot.sent[0][1]


def test_announcement_is_not_repeated_after_a_restart(db, bot):
    """Тот же день, новый запуск бота — второго объявления в чате быть не должно."""
    moment = datetime(2026, 8, config.announce_day, config.announce_hour)
    _tick(bot, moment)
    _tick(bot, moment.replace(hour=config.announce_hour + 1))   # перезапуск
    _tick(bot, moment.replace(hour=config.announce_hour + 3))   # и ещё один

    assert len(bot.sent) == 1


def test_next_month_announcement_goes_out_again(db, bot):
    _tick(bot, datetime(2026, 8, config.announce_day, config.announce_hour))
    _tick(bot, datetime(2026, 9, config.announce_day, config.announce_hour))

    assert len(bot.sent) == 2


def test_oek_registry_waits_half_an_hour_after_the_statement(db, bot, monkeypatch):
    """Реестр ОЭК уходит 20 числа в 14:30 — минутой раньше ещё рано.

    Из-за минут задача и заставила проверять календарь чаще, чем раз в
    десять минут: при прежнем шаге реестр мог уйти почти в 14:40.
    """
    built = []

    async def fake_registry(_bot):
        built.append(True)

    monkeypatch.setattr(scheduler, "send_oek_registry", fake_registry)
    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour,
                        config.oek_minute - 1))
    assert built == []

    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour,
                        config.oek_minute))
    assert built == [True]

    # Перезапуск в тот же день второй реестр не порождает
    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour + 2))
    assert built == [True]


def test_oek_registry_is_not_built_on_other_days(db, bot, monkeypatch):
    built = []

    async def fake_registry(_bot):
        built.append(True)

    monkeypatch.setattr(scheduler, "send_oek_registry", fake_registry)
    _tick(bot, datetime(2026, 8, config.oek_day + 1, config.oek_hour + 1))

    assert built == []


def test_statement_does_not_announce_by_itself(db, bot, monkeypatch):
    """Ведомость уходит председателю молча: объявление — отдельная задача."""
    generated = []

    async def fake_statement(_bot):
        generated.append(True)

    monkeypatch.setattr(scheduler, "send_monthly_statement", fake_statement)
    _tick(bot, datetime(2026, 8, config.statement_day, config.statement_hour))

    assert generated == [True]
    assert bot.sent == []


class KeyboardBot:
    """Запоминает не только текст, но и клавиатуру каждого сообщения."""

    def __init__(self):
        self.sent: list[tuple[int, str, object]] = []

    async def send_message(self, chat_id, text, reply_markup=None, **kwargs):
        self.sent.append((chat_id, text, reply_markup))


def test_task_reminders_come_one_per_task_with_buttons(db, monkeypatch):
    """Ранее всё слипалось в одно сообщение — отметить выполненное было нечем."""
    monkeypatch.setattr(scheduler, "config",
                        replace(config, admin_ids=(777,)))
    conn = repository.connect(db)
    try:
        overdue = repository.create_task(conn, "найти машину погрузчик",
                                         due_date="2026-08-30", source="chairman")
        repository.create_task(conn, "Оплатить абонентскую плату за GSM-модуль",
                               due_date="2026-09-07", source="chairman")
        conn.commit()
    finally:
        conn.close()

    bot = KeyboardBot()
    sent = asyncio.run(scheduler.send_task_reminders(bot))

    assert sent == 1
    header, *tasks = bot.sent
    assert "Задачи на сегодня" in header[1]
    assert len(tasks) >= 2, "каждая задача должна прийти отдельным сообщением"
    assert all(markup is not None for _, _, markup in tasks), \
        "у задачи должны быть свои кнопки"

    # Кнопки ведут именно к этой задаче, а не к первой попавшейся
    buttons = [b.callback_data
               for _, _, markup in tasks
               for row in markup.inline_keyboard for b in row]
    assert any(str(overdue) in data for data in buttons)


def test_no_reminders_means_no_messages(db, monkeypatch):
    """Пустой день — бот молчит, а не присылает пустой заголовок."""
    from bot.services import task_service

    monkeypatch.setattr(scheduler, "config", replace(config, admin_ids=(777,)))
    monkeypatch.setattr(task_service, "reminders_with_rows",
                        lambda conn, today=None: [])
    bot = KeyboardBot()
    assert asyncio.run(scheduler.send_task_reminders(bot)) == 0
    assert bot.sent == []


# ---------------------------------------------------------------------------
# Напоминания жителям
# ---------------------------------------------------------------------------

def test_reminders_wait_for_their_hour(db, bot, monkeypatch):
    """Ночью жителей не будим: до REMINDER_HOUR напоминание не уходит."""
    calls = []

    async def spy(_bot):
        calls.append(True)
        return 1

    monkeypatch.setattr(scheduler, "send_reminders", spy)
    monkeypatch.setattr(scheduler, "config",
                        replace(config, reminder_days=(15,), reminder_hour=10))

    _tick(bot, datetime(2026, 9, 15, 0, 5))
    assert calls == [], "в 00:05 напоминание уходить не должно"

    _tick(bot, datetime(2026, 9, 15, 10, 0))
    assert calls == [True]


def test_reminder_text_carries_the_chairman_wording():
    from bot.services.reminder_service import REMINDER_TEXT, deadline_text

    text = REMINDER_TEXT.format(period="сентябрь 2026", deadline=deadline_text())

    assert text.startswith("Здравствуйте!")
    assert "минимизирует начисления по ОДН" in text
    assert "Заранее благодарю" in text
    assert "20 числа, 12:00" in text


def test_deadline_follows_the_settings(monkeypatch):
    """Срок в тексте берётся из настроек, а не вписан в него намертво."""
    from bot.services import reminder_service

    monkeypatch.setattr(reminder_service, "config",
                        replace(config, statement_day=21,
                                readings_deadline_hour=12))
    assert reminder_service.deadline_text() == "21 числа, 12:00"


def test_reminder_goes_only_to_flats_that_have_not_submitted(db, monkeypatch):
    """Передал показания — напоминание не приходит."""
    from bot.services.parser import parse_message
    from bot.services.reading_service import current_period, save_parsed_readings

    monkeypatch.setattr(scheduler, "config", replace(config, admin_ids=()))
    conn = repository.connect(db)
    try:
        # оба жителя зарегистрированы, показания передал только первый
        first = repository.get_apartment_by_number(conn, "1")
        second = repository.get_apartment_by_number(conn, "2")
        repository.create_user(conn, 111, "Житель кв. 1", first["id"])
        repository.create_user(conn, 222, "Житель кв. 2", second["id"])
        save_parsed_readings(conn, first, parse_message("Кв 1\nЭл.эн 100"),
                             None, period=current_period())
        conn.commit()
    finally:
        conn.close()

    bot = KeyboardBot()
    sent = asyncio.run(scheduler.send_reminders(bot))

    assert sent == ["2"], "напоминание — только не сдавшему"
    assert [chat_id for chat_id, _, _ in bot.sent] == [222]
    assert "минимизирует начисления по ОДН" in bot.sent[0][1]


def test_reminder_days_and_hour_come_from_settings():
    """18 и 19 — зовём передать, 23 и 25 — объясняем опоздавшим. В 20:00."""
    from bot.config import Config

    fresh = Config()
    assert fresh.reminder_days == (18, 19, 23, 25)
    assert fresh.reminder_hour == 20
    assert fresh.chat_reminder_days == (17, 18, 19, 20)
    assert fresh.chat_reminder_hour == 10


# ---------------------------------------------------------------------------
# Напоминание в чат дома
# ---------------------------------------------------------------------------

def test_chat_reminder_goes_out_on_its_days_at_its_hour(db, bot, monkeypatch):
    """17–20 числа в 10:00 — и ни ночью, ни в другие дни."""
    sent = []

    async def spy(_bot):
        sent.append(True)
        return True

    monkeypatch.setattr(scheduler, "send_chat_reminder", spy)
    monkeypatch.setattr(scheduler, "config",
                        replace(config, group_chat_id=GROUP_CHAT,
                                chat_reminder_days=(17, 18, 19, 20),
                                chat_reminder_hour=10))

    _tick(bot, datetime(2026, 9, 17, 3, 0))     # ночью — молчим
    assert sent == []

    _tick(bot, datetime(2026, 9, 17, 10, 0))
    assert sent == [True]

    _tick(bot, datetime(2026, 9, 17, 18, 0))    # второй раз за сутки — нет
    assert sent == [True]

    _tick(bot, datetime(2026, 9, 18, 10, 0))    # на следующий день — снова
    assert sent == [True, True]

    _tick(bot, datetime(2026, 9, 21, 10, 0))    # 21 числа уже не шлём
    assert sent == [True, True]


def test_chat_reminder_text_goes_to_the_house_chat(db, monkeypatch):
    monkeypatch.setattr(scheduler, "config",
                        replace(config, group_chat_id=GROUP_CHAT))
    bot = FakeBot()

    assert asyncio.run(scheduler.send_chat_reminder(bot)) is True
    chat_id, text = bot.sent[0]
    assert chat_id == GROUP_CHAT
    assert "Показания счётчиков" in text
    assert "минимизирует начисления по ОДН" in text


def test_chat_reminder_needs_a_chat(db, monkeypatch):
    """Чат дома не подключён — писать некуда, но и падать не из-за чего."""
    monkeypatch.setattr(scheduler, "config",
                        replace(config, group_chat_id=None))
    bot = FakeBot()

    assert asyncio.run(scheduler.send_chat_reminder(bot)) is False
    assert bot.sent == []


def test_statement_day_morning_still_invites_to_submit():
    """В 10 утра 20 числа показания ещё попадут в ведомость — так и пишем."""
    from datetime import date as _date

    from bot.texts import collection_reminder_text

    text = collection_reminder_text(_date(2026, 9, 20))
    assert "Сегодня до 12:00 — последний срок" in text
    assert "Срок сбора завершён" not in text

    later = collection_reminder_text(_date(2026, 9, 21))
    assert "Срок сбора завершён" in later


def test_reminder_after_the_deadline_switches_the_wording():
    """23 и 25 числа звать «успеть до 20-го» поздно и неправдиво."""
    from datetime import date as _date

    from bot.services.reminder_service import reminder_text

    in_time = reminder_text("2026-09", _date(2026, 9, 19))
    assert "пора передать показания" in in_time
    assert "до 20 числа, 12:00" in in_time

    late = reminder_text("2026-09", _date(2026, 9, 23))
    assert "уже переданы ресурсоснабжающим" in late
    assert "в следующем месяце" in late
    assert "до 25 числа" in late            # как успеть в текущий расчёт
    assert "с 15 по 19 число" in late       # и когда передавать впредь
    assert "Заранее благодарю" not in late


def test_statement_day_itself_still_invites_to_submit():
    """20 числа ведомость уходит в 14:00 — утром ещё зовём передать."""
    from datetime import date as _date

    from bot.services.reminder_service import reminder_text

    assert "пора передать показания" in reminder_text("2026-09", _date(2026, 9, 20))
