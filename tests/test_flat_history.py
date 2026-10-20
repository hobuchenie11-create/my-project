"""История показаний одной квартиры — кнопка «📊 История квартиры».

Вопрос «а что у них было в сентябре» возникает при каждом разговоре
с жителем и с ресурсником. Полная история есть в книге Excel, но ради
одной квартиры её открывать долго — бот присылает историю сообщением,
и это сообщение можно переслать жителю.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import admin
from bot.services.history_service import apartment_history_text
from bot.services.reading_service import save_reading
from database import repository
from database.init_db import init_db

CHAIRMAN = 555


class FakeState:
    def __init__(self):
        self.state = None
        self.cleared = False

    async def set_state(self, state):
        self.state = state

    async def clear(self):
        self.cleared = True
        self.state = None


class Msg:
    def __init__(self, text, tg_id=CHAIRMAN):
        self.text = text
        self.from_user = SimpleNamespace(id=tg_id, username="u")
        self.chat = SimpleNamespace(id=tg_id, type="private")
        self.answers: list[tuple[str, object]] = []

    async def answer(self, text, reply_markup=None, **kwargs):
        self.answers.append((text, reply_markup))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "history.db"
    init_db(path, apartments_count=80, nonresidential_count=1)
    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    monkeypatch.setattr(admin, "config",
                        replace(admin.config, admin_ids=(CHAIRMAN,)))
    return path


def _flat(conn, number="49"):
    return repository.get_apartment_by_number(conn, number)


def _history(db, number="49", **kwargs):
    conn = repository.connect(db)
    try:
        return apartment_history_text(conn, _flat(conn, number), **kwargs)
    finally:
        conn.close()


def _save(db, number, kind, value, period, source="bot", **kwargs):
    conn = repository.connect(db)
    try:
        flat = _flat(conn, number)
        save_reading(conn, flat["id"], kind, value, None, source=source,
                     period=period, **kwargs)
    finally:
        conn.close()


def test_history_shows_months_newest_first(db):
    _save(db, "49", "electricity", 34200, "2026-08")
    _save(db, "49", "electricity", 34450, "2026-09")
    _save(db, "49", "electricity", 34651, "2026-10")

    text = _history(db)

    assert text.index("Октябрь 2026") < text.index("Сентябрь 2026")
    assert "34651 кВт·ч" in text


def test_monthly_use_is_counted_from_the_previous_reading(db):
    _save(db, "49", "electricity", 34450, "2026-09")
    _save(db, "49", "electricity", 34651, "2026-10")

    text = _history(db)

    assert "(+201)" in text


def test_a_skipped_month_says_how_many_months_the_use_covers(db):
    """Расход за два месяца и за один выглядят одинаково — это разные цифры."""
    _save(db, "49", "electricity", 34200, "2026-08")
    _save(db, "49", "electricity", 34651, "2026-10")

    text = _history(db)

    assert "(+451 за 2 мес.)" in text


def test_a_lower_reading_is_not_passed_off_as_use(db):
    """Счётчик заменили — отрицательный расход расходом называть нельзя."""
    _save(db, "49", "hws", 812, "2026-09")
    _save(db, "49", "hws", 3, "2026-10", replaced=True)

    text = _history(db)

    assert "ниже предыдущего" in text
    assert "+-" not in text


def test_the_source_of_the_readings_is_named(db):
    _save(db, "49", "electricity", 34651, "2026-10", source="chat")

    assert "Telegram (чат)" in _history(db)


def test_a_corrected_reading_is_marked(db):
    """Исправление не затирает историю — по сообщению это видно."""
    _save(db, "49", "electricity", 34000, "2026-10")
    _save(db, "49", "electricity", 34651, "2026-10")

    text = _history(db)

    assert "34651" in text and "исправлялось" in text


def test_the_message_can_be_forwarded_to_the_resident(db):
    """Пересланное сообщение читается отдельно: нужен адрес и номер квартиры."""
    _save(db, "49", "electricity", 34651, "2026-10")

    text = _history(db)

    assert "кв. 49" in text
    assert "ул. Магистральная, 2" in text


def test_only_the_asked_months_are_shown(db):
    for month in range(5, 11):
        _save(db, "49", "electricity", 34000 + month, f"2026-{month:02d}")

    text = _history(db, months=3)

    assert "Октябрь 2026" in text and "Май 2026" not in text
    assert "Показаны последние 3 месяцев из 6" in text
    assert "книге Excel" in text


def test_an_empty_history_does_not_look_like_a_failure(db):
    text = _history(db, "7")

    assert "не передавались" in text
    assert "на бумаге" in text          # показания могли прийти и не в бот


def test_nonresidential_rooms_are_named_without_kv(db):
    room = "Нежилое помещение №1"
    _save(db, room, "electricity", 500, "2026-10")

    text = _history(db, room)

    assert room in text
    assert "кв. Нежилое" not in text


def test_the_chairman_asks_by_flat_number(db):
    _save(db, "49", "electricity", 34651, "2026-10")
    state = FakeState()

    message = Msg("кв. 49")
    asyncio.run(admin.show_apartment_history(message, state))

    text, keyboard = message.answers[-1]
    assert "История показаний" in text and "34651" in text
    assert keyboard is not None            # меню возвращается на место
    assert state.cleared


def test_a_wrong_number_keeps_the_dialog_open(db):
    state = FakeState()

    message = Msg("кв. 999")
    asyncio.run(admin.show_apartment_history(message, state))

    assert "Не нашла" in message.answers[-1][0]
    assert not state.cleared              # ждём номер ещё раз


def test_the_dialog_can_be_cancelled(db):
    state = FakeState()

    message = Msg("отмена")
    asyncio.run(admin.show_apartment_history(message, state))

    assert "Отменено" in message.answers[-1][0]
    assert state.cleared
