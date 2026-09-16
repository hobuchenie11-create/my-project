"""Правка набора счётчиков квартиры прямо из бота.

Расхождение со справочником видно только по показаниям: житель шлёт кухню
и санузел отдельно, а в реестре у него один счётчик — бот не знает, какое
из двух записать, и показания в ведомость не попадают. Раньше это лечилось
только заменой data/apartments.xlsx и перезапуском бота.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import admin
from bot.services import meters_service
from bot.services.parser import parse_message
from bot.services.reading_service import save_parsed_readings
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


class Callback:
    def __init__(self, data):
        self.data = data
        self.from_user = SimpleNamespace(id=CHAIRMAN)
        self.message = Msg("")
        self.acknowledged: list[str] = []

    async def answer(self, text="", **kwargs):
        self.acknowledged.append(text)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "meters.db"
    init_db(path, apartments_count=80, nonresidential_count=1)
    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    monkeypatch.setattr(admin, "config",
                        replace(admin.config, admin_ids=(CHAIRMAN,)))
    return path


def _kinds(db, number):
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, number)
        return [m["kind"] for m in repository.meters_for_apartment(conn, flat["id"])]
    finally:
        conn.close()


def _flat_id(db, number):
    conn = repository.connect(db)
    try:
        return repository.get_apartment_by_number(conn, number)["id"]
    finally:
        conn.close()


def test_split_readings_are_refused_while_the_registry_says_one_meter(db):
    """Исходная жалоба: «прочитал не все показания»."""
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "37")
        parsed = parse_message("КВ.37\nЭл.эн.14161\nХ.в.кух.204\nХ.в.ван.968")
        outcome = save_parsed_readings(conn, flat, parsed, None, period="2026-09")
    finally:
        conn.close()

    assert outcome.saved == {"electricity": 14161.0}
    assert any("один счётчик" in e for e in outcome.errors)


def test_chairman_switches_a_flat_to_two_water_meters(db):
    """Номер — кнопки — готово, без замены справочника и перезапуска."""
    state = FakeState()
    message = Msg("кв. 37")
    asyncio.run(admin.show_apartment_meters(message, state))

    text, keyboard = message.answers[-1]
    assert "кв. 37" in text
    assert "ХВС×1 · ГВС×1" in text
    assert keyboard is not None, "должны появиться кнопки выбора"

    callback = Callback(f"layout:{_flat_id(db, '37')}:2-2")
    asyncio.run(admin.apply_apartment_layout(callback))

    assert _kinds(db, "37") == ["electricity", "cws_kitchen", "cws_bathroom",
                                "hws_kitchen", "hws_bathroom"]
    assert "Реестр обновлён" in callback.message.answers[0][0]


def test_after_the_fix_the_same_message_is_recorded_in_full(db):
    """Те же показания, что бот отверг, теперь встают на свои места."""
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "37")
        meters_service.apply_layout(conn, flat["id"], 2, 2)
        parsed = parse_message("КВ.37\nЭл.эн.14161\nХ.в.кух.204\nХ.в.ван.968\n"
                               "Г.в.кух.130\nГ.в.ван.472\nОбщ.гвс.602")
        outcome = save_parsed_readings(conn, flat, parsed, None, period="2026-09")
    finally:
        conn.close()

    assert outcome.saved == {"electricity": 14161.0, "cws_kitchen": 204.0,
                             "cws_bathroom": 968.0, "hws_kitchen": 130.0,
                             "hws_bathroom": 472.0}
    assert outcome.errors == []


def test_history_survives_the_switch(db):
    """Показания за прошлый месяц остаются в базе — ведомости не «худеют»."""
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "29")
        parsed = parse_message("Кв 29\nХвс 200\nГвс 100")
        save_parsed_readings(conn, flat, parsed, None, period="2026-08")
        meters_service.apply_layout(conn, flat["id"], 2, 2)
        rows = repository.readings_history_for_apartment(conn, flat["id"])
    finally:
        conn.close()

    assert {r["kind"]: r["value"] for r in rows}["cws"] == 200.0
    assert "cws" not in _kinds(db, "29")     # но больше не опрашивается


def test_layout_label_follows_the_registry(db):
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "29")
        meters_service.apply_layout(conn, flat["id"], 2, 1)
        assert meters_service.layout_of(conn, flat["id"]) == (2, 1)
        assert repository.get_apartment_by_number(
            conn, "29")["layout"] == "ХВС×2 · ГВС×1"
    finally:
        conn.close()


def test_unknown_flat_asks_again_without_losing_the_dialog(db):
    state = FakeState()
    message = Msg("кв. 999")
    asyncio.run(admin.show_apartment_meters(message, state))

    assert "Не нашла" in message.answers[-1][0]
    assert not state.cleared, "диалог должен остаться открытым"
