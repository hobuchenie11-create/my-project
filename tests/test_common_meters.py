"""Нежилые помещения и общедомовой прибор: ввод через бота и попадание в ведомость."""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import manual
from bot.services.parser import parse_message
from bot.services.report_service import build_statement
from database import repository
from database.init_db import init_db
from database.models import COMMON_NUMBER

CHAIRMAN = 555


class FakeMessage:
    """Сообщение председателя в личном чате с ботом."""

    def __init__(self, text):
        self.text = text
        self.chat = SimpleNamespace(id=CHAIRMAN, type="private")
        self.from_user = SimpleNamespace(id=CHAIRMAN, username="chairman")
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "common.db"
    init_db(path, apartments_count=5, nonresidential_count=2)
    real_connect = repository.connect
    monkeypatch.setattr(manual.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(manual, "config",
                        replace(manual.config, admin_ids=(CHAIRMAN,)))
    return path


def _send(text) -> FakeMessage:
    message = FakeMessage(text)
    asyncio.run(manual.manual_readings(message))
    return message


def test_registry_has_the_common_meter_row(db):
    conn = repository.connect(db)
    try:
        common = repository.get_apartment_by_number(conn, COMMON_NUMBER)
        assert common["type"] == "common"
        kinds = [m["kind"] for m in repository.meters_for_apartment(conn, common["id"])]
        assert kinds == ["electricity"]
    finally:
        conn.close()


def test_nonresidential_meter_sets_differ(db):
    """Нежилое №1 — свет и вода, нежилое №2 — только свет."""
    conn = repository.connect(db)
    try:
        first = repository.get_apartment_by_number(conn, "Нежилое помещение №1")
        second = repository.get_apartment_by_number(conn, "Нежилое помещение №2")
        assert [m["kind"] for m in repository.meters_for_apartment(
            conn, first["id"])] == ["electricity", "cws", "hws"]
        assert [m["kind"] for m in repository.meters_for_apartment(
            conn, second["id"])] == ["electricity"]
    finally:
        conn.close()


def test_common_meter_is_recognised_by_name():
    for text in ("Общедомовой\nЭл.эн 123456", "ОДПУ\nЭлектроэнергия 123456",
                 "Общедомовые показания\nЭл.эн 123456",
                 "Общий прибор учета\nЭл.эн 123456"):
        assert parse_message(text).apartment_number == COMMON_NUMBER, text


def test_chairman_submits_the_common_meter(db):
    message = _send("Общедомовой\nЭл.эн 123456")

    assert "Общедомовой прибор учета — показания приняты" in message.answers[0]
    assert "Электроэнергия: 123456" in message.answers[0]
    assert "кв. Общедомовой" not in message.answers[0]

    conn = repository.connect(db)
    try:
        statement = build_statement(conn, _period())
        row = next(r for r in statement.rows if r.number == COMMON_NUMBER)
        assert row.submitted and row.electricity == 123456
        assert "вручную" not in row.note
    finally:
        conn.close()


def test_chairman_submits_both_nonresidential(db):
    _send("Нежилое 1\nЭл.эн 4521\nХвс 340\nГвс 155")
    _send("Нежилое 2\nЭл.эн 980")

    conn = repository.connect(db)
    try:
        statement = build_statement(conn, _period())
        first = next(r for r in statement.rows if r.number.endswith("№1"))
        second = next(r for r in statement.rows if r.number.endswith("№2"))
    finally:
        conn.close()

    assert (first.electricity, first.cws_kitchen, first.hws_sum) == (4521, 340, 155)
    assert second.electricity == 980
    assert (second.cws_kitchen, second.hws_sum) == (None, None)


def test_water_for_the_second_unit_is_refused(db):
    """У нежилого №2 воды нет — молча записывать её некуда."""
    message = _send("Нежилое 2\nЭл.эн 980\nХвс 55")

    assert "Электроэнергия: 980" in message.answers[0]
    assert "нет такого прибора" in message.answers[0]


def test_special_rows_lead_the_statement(db):
    """Нежилые и общедомовой — первыми, чтобы попасть на первую страницу."""
    conn = repository.connect(db)
    try:
        numbers = [r.number for r in build_statement(conn, _period()).rows]
    finally:
        conn.close()

    assert numbers[:3] == ["Нежилое помещение №1", "Нежилое помещение №2",
                          COMMON_NUMBER]
    assert numbers[3:] == ["1", "2", "3", "4", "5"]


def test_chairman_can_enter_a_flat_by_hand(db):
    """Житель передал по телефону — председатель вносит сам."""
    message = _send("Кв. 3\nЭл.эн 15230\nХвс 123\nГвс 88")

    assert "кв. 3 — показания приняты" in message.answers[0]

    conn = repository.connect(db)
    try:
        rows = repository.readings_for_period(conn, _period())
        source = {r["apartment_number"]: r for r in rows}["3"]
    finally:
        conn.close()
    assert source["value"] in (15230, 123, 88)


def test_unknown_room_is_reported(db):
    message = _send("Кв. 99\nЭл.эн 15230")
    assert "нет помещения" in message.answers[0]


def test_ordinary_message_goes_to_the_memos(db):
    """Не показания — значит вопрос: ищем ответ в памятках."""
    answer = _send("Напомнить себе про собрание").answers
    assert answer and "Не нашёл ответа" in answer[0]


def _period() -> str:
    from bot.services.reading_service import current_period
    return current_period()


def test_resident_pastes_readings_without_pressing_the_button(db, monkeypatch):
    """Житель вставил готовый текст в личку — записываем в его квартиру."""
    resident = 777
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "3")
        repository.create_user(conn, resident, "Житель", flat["id"])
    finally:
        conn.close()

    message = FakeMessage("Эл.эн 15230\nХвс 123\nГвс 88")
    message.from_user = SimpleNamespace(id=resident, username="rezident")
    asyncio.run(manual.manual_readings(message))

    assert "кв. 3 — показания приняты" in message.answers[0]


def test_resident_cannot_submit_for_another_flat(db):
    """Номер чужой квартиры в тексте — не повод записать соседу."""
    resident = 778
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "3")
        repository.create_user(conn, resident, "Житель", flat["id"])
    finally:
        conn.close()

    message = FakeMessage("Кв. 4\nЭл.эн 15230")
    message.from_user = SimpleNamespace(id=resident, username="rezident")
    asyncio.run(manual.manual_readings(message))

    assert "только по своей квартире" in message.answers[0]
    conn = repository.connect(db)
    try:
        other = repository.get_apartment_by_number(conn, "4")
        assert repository.readings_history_for_apartment(conn, other["id"]) == []
    finally:
        conn.close()


def test_unregistered_sender_is_asked_to_register(db):
    message = FakeMessage("Эл.эн 15230")
    message.from_user = SimpleNamespace(id=999, username="new")
    asyncio.run(manual.manual_readings(message))

    assert "/start" in message.answers[0]


def test_pasted_message_inside_the_dialog(db, monkeypatch):
    """Вставили сообщение целиком в диалог «Передать показания»."""
    from bot.handlers import readings as readings_handler

    resident = 780
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "3")
        user_id = repository.create_user(conn, resident, "Житель", flat["id"])
    finally:
        conn.close()

    real_connect = repository.connect
    monkeypatch.setattr(readings_handler.repository, "connect",
                        lambda *a, **kw: real_connect(db))

    class State:
        def __init__(self, data):
            self.data, self.cleared = data, False

        async def get_data(self):
            return dict(self.data)

        async def clear(self):
            self.cleared = True

    message = FakeMessage("Кв. 3\nЭл.эн 15230\nХвс 123\nГвс 88")
    message.from_user = SimpleNamespace(id=resident, username="rezident")
    state = State({"apartment_id": flat["id"], "user_id": user_id,
                   "queue": ["electricity", "cws", "hws"], "saved": {},
                   "warnings": []})

    asyncio.run(readings_handler.process_value(message, state))

    assert "кв. 3 — показания приняты" in message.answers[0]
    assert "Электроэнергия: 15230" in message.answers[0]
    assert state.cleared                       # диалог закрыт, дальше не спрашиваем


def test_pasted_message_for_another_flat_is_refused_in_the_dialog(db, monkeypatch):
    from bot.handlers import readings as readings_handler

    resident = 781
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "3")
        user_id = repository.create_user(conn, resident, "Житель", flat["id"])
    finally:
        conn.close()

    real_connect = repository.connect
    monkeypatch.setattr(readings_handler.repository, "connect",
                        lambda *a, **kw: real_connect(db))

    class State:
        def __init__(self, data):
            self.data, self.cleared = data, False

        async def get_data(self):
            return dict(self.data)

        async def clear(self):
            self.cleared = True

    message = FakeMessage("Кв. 4\nЭл.эн 15230")
    message.from_user = SimpleNamespace(id=resident, username="rezident")
    state = State({"apartment_id": flat["id"], "user_id": user_id,
                   "queue": ["electricity"], "saved": {}, "warnings": []})

    asyncio.run(readings_handler.process_value(message, state))

    assert "вводим показания по кв. 3" in message.answers[0]
    assert not state.cleared                   # остаёмся в диалоге
