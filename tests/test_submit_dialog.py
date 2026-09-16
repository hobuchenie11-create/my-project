"""Диалог «🏠 Передать показания»: что делать с вставленным текстом.

В диалог вставляют не число, а готовое сообщение целиком — из чата дома,
из WhatsApp. Одну квартиру бот разбирает и записывает. Пачку из нескольких
квартир раньше принимал так же: номер брался из первой строки, показания
соседей превращались в «прибор указан дважды» и пропадали.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import readings
from database import repository
from database.init_db import init_db

CHAIRMAN = 555


class FakeState:
    """FSM-контекст в памяти — состояние и данные диалога."""

    def __init__(self, data):
        self._data = dict(data)
        self.cleared = False

    async def get_data(self):
        return dict(self._data)

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self.cleared = True
        self._data = {}


class Msg:
    def __init__(self, text, tg_id=CHAIRMAN):
        self.text = text
        self.from_user = SimpleNamespace(id=tg_id, username="u")
        self.chat = SimpleNamespace(id=tg_id, type="private")
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "dialog.db"
    init_db(path, apartments_count=80, nonresidential_count=1)
    real_connect = repository.connect
    monkeypatch.setattr(readings.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(readings, "config",
                        replace(readings.config, admin_ids=(CHAIRMAN,)))
    return path


def _state(db, number):
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, number)
    finally:
        conn.close()
    return FakeState({"apartment_id": flat["id"], "user_id": None,
                      "queue": [], "saved": {}, "warnings": []})


def _values(db, number):
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, number)
        rows = repository.readings_history_for_apartment(conn, flat["id"])
        return {r["kind"]: r["value"] for r in rows}
    finally:
        conn.close()


def test_own_readings_pasted_into_the_dialog_are_saved(db):
    """Обычный случай не сломался: своя квартира записывается как раньше."""
    message = Msg("Кв 34\nЭл.эн 16553\nХвс 267\nГвс 215")
    state = _state(db, "34")

    handled = asyncio.run(readings._try_whole_message(message, state))

    assert handled is True
    assert _values(db, "34") == {"electricity": 16553.0, "cws": 267.0,
                                 "hws": 215.0}


def test_several_flats_pasted_into_the_dialog_are_not_written(db):
    """Пачка в диалоге: ввод отменяется, ни одна квартира не записывается."""
    message = Msg("Кв 34\nЭл.эн 16553\nХвс 267\n\nКв 37\nЭл.эн 14161\nХвс 204")
    state = _state(db, "34")

    handled = asyncio.run(readings._try_whole_message(message, state))

    assert handled is True
    assert state.cleared, "диалог должен закрыться, а не ждать число дальше"
    assert _values(db, "34") == {}
    assert _values(db, "37") == {}
    answer = message.answers[0]
    assert "нескольких квартир" in answer
    assert "обычным сообщением" in answer
