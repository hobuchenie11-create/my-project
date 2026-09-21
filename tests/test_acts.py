"""Акты поверки: приём от жителя и список квартир для письма ресурснику."""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import acts
from bot.keyboards.menu import BTN_METER_ACT, main_menu
from bot.services.act_service import acts_text, flats_line
from database import repository
from database.init_db import init_db

CHAIRMAN = 555
RESIDENT = 777


class FakeState:
    def __init__(self):
        self._data: dict = {}
        self.state = None

    async def set_state(self, state):
        self.state = state

    async def get_data(self):
        return dict(self._data)

    async def update_data(self, **kwargs):
        self._data.update(kwargs)

    async def clear(self):
        self.state = None
        self._data = {}


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []
        self.forwarded: list[tuple[int, int, int]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))

    async def forward_message(self, chat_id, from_chat_id, message_id):
        self.forwarded.append((chat_id, from_chat_id, message_id))


class Msg:
    def __init__(self, text="", tg_id=RESIDENT, photo=False, mime=None,
                 message_id=7):
        self.text = text
        self.message_id = message_id
        self.photo = [SimpleNamespace(file_id="photo-1")] if photo else None
        self.document = (SimpleNamespace(file_id="doc-1", mime_type=mime)
                         if mime else None)
        self.from_user = SimpleNamespace(id=tg_id, username="zhitel",
                                         full_name="Пётр Сидоров")
        self.chat = SimpleNamespace(id=tg_id, type="private")
        self.bot = FakeBot()
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)


class Callback:
    def __init__(self, data, bot=None):
        self.data = data
        self.message = Msg()
        if bot is not None:
            self.message.bot = bot
        self.answered = False

    async def answer(self, *args, **kwargs):
        self.answered = True


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "acts.db"
    init_db(path, apartments_count=80, nonresidential_count=1)
    real_connect = repository.connect
    monkeypatch.setattr(acts.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(acts, "config",
                        replace(acts.config, admin_ids=(CHAIRMAN,)))
    return path


def _run(coro):
    return asyncio.run(coro)


def _submit(state, flat="15", kind="act:kind:hws", photo=True, mime=None):
    _run(acts.take_apartment(Msg(flat), state))
    _run(acts.take_kind(Callback(kind), state))
    last = Msg(photo=photo, mime=mime)
    _run(acts.take_document(last, state))
    return last


def test_button_is_available_to_every_resident():
    labels = [b.text for row in main_menu().keyboard for b in row]
    assert BTN_METER_ACT in labels


def test_act_reaches_the_chairman_and_the_list(db):
    state = FakeState()

    start = Msg(BTN_METER_ACT)
    _run(acts.start_from_menu(start, state))
    assert state.state == acts.MeterAct.apartment
    assert "акт" in start.answers[0].lower()

    last = _submit(state)

    chat_id, summary = last.bot.sent[0]
    assert chat_id == CHAIRMAN
    assert "15" in summary and "ГВС" in summary
    assert last.bot.forwarded == [(CHAIRMAN, RESIDENT, 7)]   # сам документ
    assert "Акт принят" in last.answers[0]
    assert state.state is None

    conn = repository.connect(db)
    try:
        rows = repository.meter_acts(conn)
        assert [row["apartment_number"] for row in rows] == ["15"]
        assert rows[0]["kind"] == "ГВС"
        assert rows[0]["file_id"] == "photo-1"
        assert "кв. 15" in acts_text(conn)
        assert flats_line(conn) == "кв. 15"
    finally:
        conn.close()


def test_pdf_is_accepted_too(db):
    state = FakeState()
    last = _submit(state, flat="7", photo=False, mime="application/pdf")

    assert "Акт принят" in last.answers[0]
    conn = repository.connect(db)
    try:
        assert repository.meter_acts(conn)[0]["file_id"] == "doc-1"
    finally:
        conn.close()


def test_list_keeps_registry_order_and_no_repeats(db):
    for flat in ("12", "5", "12"):
        _submit(FakeState(), flat=flat)

    conn = repository.connect(db)
    try:
        assert flats_line(conn) == "кв. 5, 12"      # по порядку реестра
        assert "Акты поверки (3)" in acts_text(conn)
    finally:
        conn.close()


def test_empty_list_explains_how_it_fills(db):
    conn = repository.connect(db)
    try:
        text = acts_text(conn)
        assert "ни одного акта" in text
        assert BTN_METER_ACT in text
    finally:
        conn.close()


def test_kind_can_be_written_by_words(db):
    state = FakeState()
    _run(acts.take_apartment(Msg("15"), state))

    message = Msg("горячая вода")
    _run(acts.kind_by_text(message, state))

    assert state.state == acts.MeterAct.document
    assert _run(state.get_data())["kind"] == "ГВС"


def test_unknown_flat_is_refused(db):
    state = FakeState()
    message = Msg("999")
    _run(acts.take_apartment(message, state))

    assert state.state is None                 # шаг не пройден
    assert "нет в реестре" in message.answers[0]


def test_text_instead_of_the_act_is_explained(db):
    state = FakeState()
    _run(acts.take_apartment(Msg("15"), state))
    _run(acts.take_kind(Callback("act:kind:cws"), state))

    message = Msg("акт дома, пришлю вечером")
    _run(acts.document_expected(message, state))
    assert state.state == acts.MeterAct.document
    assert "Жду фото акта" in message.answers[0]


def test_cancel_stops_the_flow(db):
    state = FakeState()
    _run(acts.take_apartment(Msg("15"), state))

    message = Msg("отмена")
    _run(acts.kind_by_text(message, state))
    assert state.state is None
    assert "остановились" in message.answers[0]


def test_act_is_saved_even_if_chairman_is_offline(db):
    state = FakeState()
    _run(acts.take_apartment(Msg("15"), state))
    _run(acts.take_kind(Callback("act:kind:all"), state))

    message = Msg(photo=True)

    async def boom(*args, **kwargs):
        from aiogram.exceptions import TelegramAPIError
        raise TelegramAPIError(method=None, message="chat not found")

    message.bot.send_message = boom
    _run(acts.take_document(message, state))

    conn = repository.connect(db)
    try:
        assert flats_line(conn) == "кв. 15"     # квартира в списке осталась
    finally:
        conn.close()
    assert "Акт принят" in message.answers[0]
