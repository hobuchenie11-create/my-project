"""Сводка для Совета дома: что в неё попадает и куда она уходит."""
import asyncio
from datetime import date
from types import SimpleNamespace

import pytest

from bot.handlers import tasks as tasks_handler
from bot.services import task_service
from database import repository
from database.init_db import init_db

GROUP_CHAT = -1001111111111      # чат дома: там жители передают показания
COUNCIL_CHAT = -1002222222222    # чат Совета дома: туда сводка


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


class FakeMessage:
    def __init__(self):
        self.bot = FakeBot()
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "council.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    task_service.generate_tasks(conn, months_ahead=0)   # регламент месяца
    yield conn
    conn.close()


def _one_off(conn, title, status="in_progress", done_at="", category="repair"):
    return repository.create_task(
        conn, title, category=category, status=status, source="chairman",
        due_date=date.today().replace(day=28).isoformat(),
        period=task_service._month_period(date.today()), done_at=done_at)


def test_candidates_are_one_off_tasks_only(conn):
    """Ежемесячный регламент Совету не предлагается — только разовые дела."""
    _one_off(conn, "Ремонт отмостки")
    titles = [r["title"] for r in task_service.council_candidates(conn)]

    assert titles == ["Ремонт отмостки"]
    assert not any("выписку из банка" in t.lower() for t in titles)
    assert not any("абонентскую плату" in t.lower() for t in titles)


def test_only_selected_tasks_reach_the_digest(conn):
    chosen = _one_off(conn, "Ремонт отмостки")
    _one_off(conn, "Опиловка тополей")

    digest = task_service.council_digest(conn, task_ids=[chosen])
    assert "Ремонт отмостки" in digest
    assert "Опиловка тополей" not in digest


def test_digest_keeps_amounts_and_notes_out(conn):
    task_id = repository.create_task(
        conn, "Замена двери в подъезде", category="repair",
        status="in_progress", source="chairman", amount=48000.0,
        note="торговались до 48 тыс., подрядчик Иванов",
        due_date="2026-09-20", period="2026-09")

    digest = task_service.council_digest(conn, task_ids=[task_id])
    assert "Замена двери в подъезде" in digest
    assert "48000" not in digest and "48 тыс" not in digest
    assert "Иванов" not in digest


def test_done_task_is_offered_and_shown_as_done(conn):
    task_id = _one_off(conn, "Ремонт двери 3-го подъезда", status="done",
                       done_at=date.today().isoformat())

    assert task_id in [r["id"] for r in task_service.council_candidates(conn)]
    digest = task_service.council_digest(conn, task_ids=[task_id])
    assert "Выполнено" in digest and "Ремонт двери 3-го подъезда" in digest


def test_digest_goes_to_the_council_chat(monkeypatch):
    monkeypatch.setattr(tasks_handler, "config",
                        SimpleNamespace(group_chat_id=GROUP_CHAT,
                                        council_chat_id=COUNCIL_CHAT))
    message = FakeMessage()
    asyncio.run(tasks_handler._deliver_digest(message, "текст сводки", 2))

    assert [chat for chat, _ in message.bot.sent] == [COUNCIL_CHAT]
    assert message.bot.sent[0][1] == "текст сводки"
    assert "Совета дома" in message.answers[0]


def test_digest_never_goes_to_the_readings_chat(monkeypatch):
    """Чат показаний подключён, чат Совета — нет: жителям не пишем."""
    monkeypatch.setattr(tasks_handler, "config",
                        SimpleNamespace(group_chat_id=GROUP_CHAT,
                                        council_chat_id=None))
    message = FakeMessage()
    asyncio.run(tasks_handler._deliver_digest(message, "текст сводки", 1))

    assert message.bot.sent == []                     # в чат дома — ничего
    assert "COUNCIL_CHAT_ID" in message.answers[0]    # подсказка, как подключить
    assert message.answers[-1] == "текст сводки"      # текст — председателю


def test_task_count_is_declined_correctly():
    assert tasks_handler._tasks_word(1) == "1 задача"
    assert tasks_handler._tasks_word(3) == "3 задачи"
    assert tasks_handler._tasks_word(5) == "5 задач"
    assert tasks_handler._tasks_word(11) == "11 задач"
    assert tasks_handler._tasks_word(22) == "22 задачи"


def test_readings_are_not_collected_in_the_council_chat():
    """Обсуждения Совета не разбираются как показания."""
    import inspect

    from bot.handlers import group

    assert "council_chat_id" in inspect.getsource(group.handle_group_message)


def test_chat_reminder_names_the_deadline():
    """Напоминание в чат: срок берётся из настроек и текущего месяца."""
    from bot.texts import collection_reminder_text

    text = collection_reminder_text(date(2026, 8, 16))
    assert "<b>до 19 августа</b>" in text
    assert "Остаётся 3 дня" in text
    assert "Домовед" in text
    assert "Хвс кухня" in text              # шаблон для 3-комнатных
    assert "15230" not in text              # в шаблонах без чисел-примеров
    assert "обходить квартиры" not in text

    assert "Сегодня последний день" in collection_reminder_text(date(2026, 8, 19))
    assert "Срок сбора завершён" in collection_reminder_text(date(2026, 8, 21))
    assert "1 день" in collection_reminder_text(date(2026, 8, 18))
    assert "<b>до 19 сентября</b>" in collection_reminder_text(date(2026, 9, 15))


def test_invite_and_reminder_speak_the_same_way():
    """Памятка и напоминание — одна формулировка и шаблоны без чисел."""
    from bot.texts import collection_reminder_text, welcome_residents_text

    invite = welcome_residents_text("domoved_bot")
    assert "автоматическом режиме" in invite
    assert "обходить квартиры" not in invite
    assert "15230" not in invite and "Хвс кухня 120" not in invite
    assert "Хвс санузел" in invite            # шаблон остался

    for text in (invite, collection_reminder_text(date(2026, 8, 16))):
        assert "Домовед" in text
        assert "в первой строке" in text
        assert text.rstrip().endswith("участие в процессе сбора показаний "
                                      "по нашему дому. 🙏")
        assert "расход по ОДН" in text


def test_templates_are_separate_messages():
    """Шаблоны уходят по отдельности — чтобы житель копировал нужный."""
    from bot.texts import (TEMPLATE_LARGE, TEMPLATE_SMALL, template_messages,
                           welcome_residents_text)

    messages = template_messages()
    assert len(messages) == 3

    small = [m for m in messages if TEMPLATE_SMALL in m]
    large = [m for m in messages if TEMPLATE_LARGE in m]
    assert len(small) == 1 and len(large) == 1
    assert small[0] is not large[0]           # каждый — в своём сообщении

    for message in small + large:
        assert message.count("<code>") == 1   # копируется только шаблон

    # Памятка использует те же константы — шаблоны не разъедутся
    assert TEMPLATE_LARGE in welcome_residents_text("domoved_bot")


def test_large_template_asks_for_the_hot_water_total():
    """Строка «Сумма ГВ» — её бот сверяет с кухня+ванна."""
    from bot.services.parser import parse_message
    from bot.texts import TEMPLATE_LARGE

    assert TEMPLATE_LARGE.endswith("Сумма ГВ")

    filled = TEMPLATE_LARGE.replace("Кв.", "Кв. 5")
    for label, value in (("Эл.эн", 21694), ("Хвс кухня", 138),
                         ("Хвс санузел", 617), ("Гвс кухня", 206),
                         ("Гвс ванна", 622), ("Сумма ГВ", 828)):
        filled = filled.replace(f"\n{label}", f"\n{label} {value}")

    parsed = parse_message(filled)
    assert parsed.apartment_number == "5"
    assert parsed.values["hws_total"] == 828        # сумма распознана
    assert parsed.values["hws_kitchen"] == 206
