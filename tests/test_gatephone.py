"""Заявка «Сменить номер на воротах» — доступна любому жителю, в любой день."""
import asyncio
import re
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import gatephone
from bot.keyboards.faq import memo_action
from bot.keyboards.menu import BTN_GATE_PHONE, main_menu
from bot.services import faq_service
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

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


class Msg:
    def __init__(self, text="", tg_id=RESIDENT):
        self.text = text
        self.from_user = SimpleNamespace(id=tg_id, username="zhitel",
                                         full_name="Пётр Сидоров")
        self.chat = SimpleNamespace(id=tg_id, type="private")
        self.bot = FakeBot()
        self.answers: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)

    async def answer_photo(self, photo, caption="", **kwargs):
        self.answers.append(caption)


class Callback:
    def __init__(self, data):
        self.data = data
        self.message = Msg()
        self.answered = False

    async def answer(self, *args, **kwargs):
        self.answered = True


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "gates.db"
    init_db(db, apartments_count=80, nonresidential_count=1)
    conn = repository.connect(db)
    faq_service.load_memos(conn)          # настоящие content/faq/*.md
    yield conn
    conn.close()


@pytest.fixture()
def db(monkeypatch, conn):
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    real_connect = repository.connect
    monkeypatch.setattr(gatephone.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(gatephone, "config",
                        replace(gatephone.config, admin_ids=(CHAIRMAN,)))
    return path


def _run(coro):
    return asyncio.run(coro)


def _ask_all(state, name="Сидоров Пётр Иванович", flat="15",
             phone="+7 902 123-45-67"):
    _run(gatephone.take_name(Msg(name), state))
    _run(gatephone.take_apartment(Msg(flat), state))
    last = Msg(phone)
    _run(gatephone.take_phone(last, state))
    return last


def test_button_is_in_the_menu_for_every_resident():
    labels = [button.text for row in main_menu().keyboard for button in row]
    assert BTN_GATE_PHONE in labels
    # и у председателя тоже — она такой же житель
    assert BTN_GATE_PHONE in [button.text
                              for row in main_menu(True).keyboard
                              for button in row]


def test_request_reaches_the_chairman(db):
    state = FakeState()

    start = Msg(BTN_GATE_PHONE)
    _run(gatephone.start_from_menu(start, state))
    assert state.state == gatephone.GatePhone.name
    assert "три вопроса" in start.answers[0]

    last = _ask_all(state)

    chat_id, summary = last.bot.sent[0]
    assert chat_id == CHAIRMAN
    assert "15" in summary
    assert "Сидоров Пётр Иванович" in summary
    assert "+7 902 123-45-67" in summary
    assert state.state is None

    # Житель видит подтверждение и памятку про оплату 10 ₽
    text = "\n".join(last.answers)
    assert "Заявка передана председателю" in text
    # Номер ворот сверяем по цифрам: оформление в памятке может меняться
    assert "10 ₽" in text and "9026767881" in re.sub(r"\D", "", text)


def test_memo_offers_the_button(conn):
    memo = faq_service.by_code(conn, "gsm-modul")
    assert memo.action == "gatephone"
    assert memo_action(memo.action).inline_keyboard[0][0].callback_data == \
        "start:gatephone"


def test_memo_inside_the_dialog_has_no_button(db):
    """Кнопка под памяткой увела бы жителя в начало того же разговора."""
    sent = []

    async def fake_send_memo(message, memo, with_action=True):
        sent.append(with_action)

    import bot.handlers.faq as faq_module
    original = faq_module.send_memo
    faq_module.send_memo = fake_send_memo
    try:
        _ask_all(FakeState())
    finally:
        faq_module.send_memo = original

    assert sent == [False]


def test_memo_button_starts_the_same_dialog(db):
    state = FakeState()
    callback = Callback("start:gatephone")
    _run(gatephone.start_from_memo(callback, state))

    assert state.state == gatephone.GatePhone.name
    assert callback.answered


def test_unknown_flat_is_refused(db):
    state = FakeState()
    _run(gatephone.take_name(Msg("Сидоров Пётр Иванович"), state))

    message = Msg("999")
    _run(gatephone.take_apartment(message, state))
    assert state.state == gatephone.GatePhone.apartment
    assert "нет в реестре" in message.answers[0]


def test_short_phone_is_refused(db):
    state = FakeState()
    _run(gatephone.take_name(Msg("Сидоров Пётр Иванович"), state))
    _run(gatephone.take_apartment(Msg("15"), state))

    message = Msg("123-45")
    _run(gatephone.take_phone(message, state))
    assert state.state == gatephone.GatePhone.phone
    assert "не похоже на номер" in message.answers[0]
    assert message.bot.sent == []               # заявка не ушла


def test_short_name_is_refused(db):
    state = FakeState()
    _run(gatephone.start_from_menu(Msg(BTN_GATE_PHONE), state))

    message = Msg("Пётр")
    _run(gatephone.take_name(message, state))

    assert state.state == gatephone.GatePhone.name
    assert "ФИО полностью" in message.answers[0]


def test_cancel_stops_the_request(db):
    state = FakeState()
    _run(gatephone.take_name(Msg("Сидоров Пётр Иванович"), state))

    message = Msg("отмена")
    _run(gatephone.take_apartment(message, state))
    assert state.state is None
    assert "отменила" in message.answers[0]


def test_request_is_logged_even_if_chairman_is_offline(db):
    state = FakeState()
    _run(gatephone.take_name(Msg("Сидоров Пётр Иванович"), state))
    _run(gatephone.take_apartment(Msg("15"), state))

    message = Msg("89021234567")

    async def boom(*args, **kwargs):
        from aiogram.exceptions import TelegramAPIError
        raise TelegramAPIError(method=None, message="chat not found")

    message.bot.send_message = boom
    _run(gatephone.take_phone(message, state))

    conn = repository.connect(db)
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE action = 'gatephone'").fetchall()
    finally:
        conn.close()
    assert len(rows) == 1
    assert "89021234567" in rows[0]["details"]
    assert "кв. 15" in rows[0]["details"]
