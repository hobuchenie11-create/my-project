"""Новый собственник: памятки по дому и сбор данных для ворот.

Памятки в `content/faq/` — не документация, а то, что бот отвечает жителю.
Поэтому тест проверяет настоящие файлы дома: что в них остались телефоны
ворот и диспетчера, что вопрос своими словами приводит к нужной памятке
и что сценарий оформления доводит данные до председателя.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import newcomer
from bot.keyboards.faq import memo_action
from bot.services import faq_service
from database import repository
from database.init_db import init_db

CHAIRMAN = 555
RESIDENT = 777

# Номера из плакатов, которые висят в подъездах
GATE_MAGISTRALNAYA = "89026767881"
GATE_HIMIKOV = "89026767880"
MODUS = "372323"


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
    def __init__(self, text="", tg_id=RESIDENT, message_id=1):
        self.text = text
        self.message_id = message_id
        self.from_user = SimpleNamespace(id=tg_id, username="novosel",
                                         full_name="Мария Иванова")
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
    db = tmp_path / "memos.db"
    init_db(db, apartments_count=80, nonresidential_count=1)
    conn = repository.connect(db)
    faq_service.load_memos(conn)          # настоящие content/faq/*.md
    yield conn
    conn.close()


@pytest.fixture()
def db(tmp_path, monkeypatch, conn):
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    real_connect = repository.connect
    monkeypatch.setattr(newcomer.repository, "connect",
                        lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(newcomer, "config",
                        replace(newcomer.config, admin_ids=(CHAIRMAN,)))
    return path


# ---------------------------------------------------------------------------
# Памятки дома
# ---------------------------------------------------------------------------

def test_memos_are_filled_in(conn):
    """Заготовка «ЗАПОЛНИТЬ» в ответе жителю — то же молчание."""
    rows = repository.active_memos(conn)
    assert len(rows) >= 6
    for row in rows:
        assert "ЗАПОЛНИТЬ" not in row["body"], row["code"]
        assert len(row["body"]) > 100, row["code"]


def test_gate_numbers_are_in_place(conn):
    gates = faq_service.by_code(conn, "vorota").body
    assert GATE_MAGISTRALNAYA in gates and GATE_HIMIKOV in gates
    assert "10 секунд" in gates

    gsm = faq_service.by_code(conn, "gsm-modul").body
    assert "10" in gsm and "Теле2" in gsm      # плата за каждый номер ворот
    assert GATE_MAGISTRALNAYA in gsm and GATE_HIMIKOV in gsm

    keys = faq_service.by_code(conn, "klyuchi").body
    assert MODUS in keys and "Модус" in keys


def test_gate_only_opens_from_magistralnaya(conn):
    """Гостя со стороны Химиков из квартиры не впустить — это надо знать."""
    body = faq_service.by_code(conn, "dostup-vo-dvor").body
    assert "Магистральная, 2" in body
    assert "Химиков, 43" in body


@pytest.mark.parametrize("question, code", [
    ("как открыть ворота", "vorota"),
    ("не открываются ворота с моего телефона", "vorota"),
    ("как записать номер телефона в ворота", "gsm-modul"),
    ("сменила номер, надо запрограммировать", "gsm-modul"),
    ("потеряла ключ от калитки", "klyuchi"),
    ("как заказать ключи", "klyuchi"),
    ("как пропустить гостей во двор", "dostup-vo-dvor"),
    ("за что начисляют домофон в квитанции", "oplata"),
    ("купила квартиру, что нужно сделать", "novyy-sobstvennik"),
    ("новый собственник", "novyy-sobstvennik"),
])
def test_question_reaches_the_right_memo(conn, question, code):
    found = faq_service.search(conn, question)
    assert found, question
    assert code in [memo.code for memo in found[:2]], question


def test_newcomer_memo_offers_the_button(conn):
    memo = faq_service.by_code(conn, "novyy-sobstvennik")
    assert memo.action == "newcomer"

    keyboard = memo_action(memo.action)
    assert keyboard.inline_keyboard[0][0].callback_data == "start:newcomer"
    assert memo_action("") is None


# ---------------------------------------------------------------------------
# Сценарий оформления
# ---------------------------------------------------------------------------

def _run(coro):
    return asyncio.run(coro)


def test_full_flow_reaches_the_chairman(db):
    state = FakeState()

    callback = Callback("start:newcomer")
    _run(newcomer.start(callback, state))
    assert state.state == newcomer.Newcomer.apartment
    assert callback.answered

    flat = Msg("15")
    _run(newcomer.take_apartment(flat, state))
    assert state.state == newcomer.Newcomer.contacts
    assert "кв. 15" in flat.answers[0]
    # Вместе с вопросом про телефон уходит памятка про 10 ₽ на каждые ворота
    assert any(GATE_HIMIKOV in text for text in flat.answers)

    contacts = Msg("Иванова Мария Петровна, +7 902 676-78-81")
    _run(newcomer.take_contacts(contacts, state))
    assert state.state == newcomer.Newcomer.car

    car = Msg("1234 АВ-55")
    _run(newcomer.take_car(car, state))

    chat_id, summary = car.bot.sent[0]
    assert chat_id == CHAIRMAN
    assert "15" in summary and "Иванова Мария Петровна" in summary
    assert "1234 АВ-55" in summary
    assert "ЕГРН" in summary                     # ждать выписку от жителя

    # Новосёл сразу получает памятки про ворота и калитку
    tail = "\n".join(car.answers)
    assert GATE_MAGISTRALNAYA in tail and "калитк" in tail.lower()
    assert state.state is None


def test_egrn_goes_to_the_chairman_not_to_the_bot(db, conn):
    """Документ с персональными данными в переписке с ботом не хранится."""
    state = FakeState()
    _run(newcomer.take_apartment(Msg("15"), state))
    _run(newcomer.take_contacts(Msg("Пётр Сидоров, 89021234567"), state))

    car = Msg("нет")
    _run(newcomer.take_car(car, state))

    final = "\n".join(car.answers).lower()
    assert "председателю" in final and "егрн" in final
    assert "присылать не нужно" in final
    assert car.bot.forwarded == []               # бот ничего не пересылает

    memo = faq_service.by_code(conn, "novyy-sobstvennik").body.lower()
    assert "председателю" in memo and "присылать не нужно" in memo


def test_flat_number_must_exist(db):
    state = FakeState()
    message = Msg("999")
    _run(newcomer.take_apartment(message, state))

    assert state.state is None                  # шаг не пройден
    assert "нет в реестре" in message.answers[0]


def test_photo_during_the_flow_is_not_treated_as_readings(db, monkeypatch):
    """Житель всё равно прислал выписку боту — ответ должен быть по делу."""
    from dataclasses import replace as dc_replace

    from bot.handlers import photos
    from tests.test_photos import FakeState as PhotoState, Msg as PhotoMsg

    monkeypatch.setattr(photos, "config",
                        dc_replace(photos.config, admin_ids=(CHAIRMAN,),
                                   council_chat_id=0))
    state = PhotoState()
    state.state = newcomer.Newcomer.contacts

    message = PhotoMsg(tg_id=RESIDENT)
    message.photo = [SimpleNamespace(file_id="x")]
    _run(photos.handle_photo(message, state))

    assert "ЕГРН" in message.answers[0]
    assert "показани" not in message.answers[0].lower()


def test_contacts_without_phone_are_refused(db):
    state = FakeState()
    _run(newcomer.take_apartment(Msg("15"), state))

    message = Msg("Иванова Мария")
    _run(newcomer.take_contacts(message, state))
    assert state.state == newcomer.Newcomer.contacts
    assert "телефон" in message.answers[0]


def test_cancel_stops_the_flow(db):
    state = FakeState()
    _run(newcomer.take_apartment(Msg("15"), state))

    message = Msg("отмена")
    _run(newcomer.take_contacts(message, state))
    assert state.state is None
    assert "остановились" in message.answers[0]


def test_data_is_logged_even_if_chairman_is_offline(db):
    """Личка председателя недоступна — данные жителя не должны пропасть."""
    state = FakeState()
    _run(newcomer.take_apartment(Msg("15"), state))
    _run(newcomer.take_contacts(Msg("Пётр Сидоров, 89021234567"), state))

    car = Msg("нет")

    async def boom(*args, **kwargs):
        from aiogram.exceptions import TelegramAPIError
        raise TelegramAPIError(method=None, message="chat not found")

    car.bot.send_message = boom
    _run(newcomer.take_car(car, state))

    conn = repository.connect(db)
    try:
        events = conn.execute(
            "SELECT * FROM events WHERE action = 'newcomer'").fetchall()
    finally:
        conn.close()
    assert len(events) == 1
    assert "Пётр Сидоров" in events[0]["details"]
