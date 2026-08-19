"""Перенос показаний из WhatsApp: вставленная пачка сообщений."""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import group, manual
from bot.services.batch_service import import_batch
from bot.services.parser import split_messages, strip_chat_meta
from database import repository
from database.init_db import init_db

CHAIRMAN = 555
RESIDENT = 777

# Как выглядит скопированный кусок переписки WhatsApp
PASTE = """[19.08.2026, 21:03] Мария Иванова: Кв. 5
Эл.эн 15230
Хвс 123
Гвс 88
[19.08.2026, 21:14] Пётр: Кв 12
Св 20820
Хв 1048
Гв 490
19.08.2026, 22:01 - Светлана:
кв38,Х/В30,Г/В 42,Эл/э 15873
[19.08.2026, 22:30] Иван: Добрый вечер, соседи! Когда собрание?
[20.08.2026, 08:00] Мария: Кв. 60
Х. Кух-277
Г. Ван. - 513"""


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "batch.db"
    init_db(path, apartments_count=80, nonresidential_count=2)
    conn = repository.connect(path)
    # кв. 60 — с раздельным учётом, как в реальном справочнике
    flat = repository.get_apartment_by_number(conn, "60")
    repository.set_meters(conn, flat["id"], ["electricity", "cws_kitchen",
                                             "cws_bathroom", "hws_kitchen",
                                             "hws_bathroom"])
    repository.create_user(conn, CHAIRMAN, "Председатель",
                           repository.get_apartment_by_number(conn, "1")["id"])
    conn.close()

    real_connect = repository.connect
    for module in (manual, group):
        monkeypatch.setattr(module.repository, "connect",
                            lambda *a, **kw: real_connect(path))
    monkeypatch.setattr(manual, "config",
                        replace(manual.config, admin_ids=(CHAIRMAN,)))
    monkeypatch.setattr(group, "config",
                        replace(group.config, admin_ids=(CHAIRMAN,),
                                group_chat_id=-100123))
    return path


def _values(db, number):
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, number)
        rows = repository.readings_history_for_apartment(conn, flat["id"])
        return {r["kind"]: r["value"] for r in rows}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Разбор вставленного текста
# ---------------------------------------------------------------------------

def test_chat_metadata_is_stripped():
    assert strip_chat_meta("[19.08.2026, 21:03] Мария Иванова: Кв. 5") == "Кв. 5"
    assert strip_chat_meta("19.08.2026, 22:01 - Светлана:") == ""
    assert strip_chat_meta("Кв. 5") == "Кв. 5"        # обычную строку не трогаем
    assert strip_chat_meta("Эл.эн 15230") == "Эл.эн 15230"


def test_paste_splits_into_messages():
    blocks = split_messages(PASTE)
    assert len(blocks) == 4                          # болтовня не в счёт
    assert blocks[0].startswith("Кв. 5")
    assert "Гвс 88" in blocks[0]
    assert "Добрый вечер" not in "\n".join(blocks)


def test_single_message_is_not_a_batch():
    assert len(split_messages("Кв. 5\nЭл.эн 15230\nХвс 123")) == 1
    assert split_messages("Добрый день, когда собрание?") == []


# ---------------------------------------------------------------------------
# Запись пачки
# ---------------------------------------------------------------------------

def test_batch_writes_every_flat(db):
    conn = repository.connect(db)
    try:
        result = import_batch(conn, split_messages(PASTE), tg_id=CHAIRMAN)
    finally:
        conn.close()

    assert result.messages == 4
    assert result.saved == 11
    assert _values(db, "5") == {"electricity": 15230.0, "cws": 123.0, "hws": 88.0}
    assert _values(db, "12") == {"electricity": 20820.0, "cws": 1048.0, "hws": 490.0}
    assert _values(db, "38")["electricity"] == 15873.0
    assert _values(db, "60") == {"cws_kitchen": 277.0, "hws_bathroom": 513.0}

    report = result.text()
    assert "Разобрано сообщений: 4" in report
    assert "кв. 5 — 3 показания" in report
    assert "кв. 38 — 3 показания" in report


def test_unknown_flat_is_reported_not_dropped(db):
    conn = repository.connect(db)
    try:
        result = import_batch(conn, split_messages("Кв. 99\nЭл.эн 100\n"
                                                   "Кв. 5\nЭл.эн 200"),
                              tg_id=CHAIRMAN)
    finally:
        conn.close()

    assert result.saved == 1
    assert any("помещение не найдено" in line for line in result.lines)
    assert _values(db, "5")["electricity"] == 200.0


class Msg:
    def __init__(self, text, tg_id=CHAIRMAN, chat_type="private"):
        self.text = text
        self.message_id = 1
        self.chat = SimpleNamespace(id=-100123 if chat_type != "private" else tg_id,
                                    type=chat_type, title="Дом")
        self.from_user = SimpleNamespace(id=tg_id, username="u")
        self.answers: list[str] = []
        self.replies: list[str] = []
        self.bot = SimpleNamespace(
            send_message=self._dm,
            set_message_reaction=self._reaction)
        self.dm: list[str] = []

    async def _dm(self, chat_id, text, **kwargs):
        self.dm.append(text)

    async def _reaction(self, **kwargs):
        pass

    async def answer(self, text, **kwargs):
        self.answers.append(text)

    async def reply(self, text, **kwargs):
        self.replies.append(text)


def test_chairman_pastes_into_the_private_chat(db):
    message = Msg(PASTE)
    asyncio.run(manual.manual_readings(message))

    assert "Разобрано сообщений: 4" in message.answers[0]
    assert _values(db, "12")["cws"] == 1048.0


def test_chairman_pastes_into_the_readings_chat(db):
    """Вставили в чат показаний — тоже разносим, сводка уходит в личку."""
    message = Msg(PASTE, chat_type="supergroup")
    asyncio.run(group.handle_group_message(message))

    assert _values(db, "5")["electricity"] == 15230.0
    assert message.dm and "Разобрано сообщений: 4" in message.dm[0]
    assert message.replies == []              # чат не засоряем


def test_resident_cannot_paste_several_flats_into_the_chat(db):
    """У жителя пачка — это чужие квартиры: просим прислать свою."""
    message = Msg(PASTE, tg_id=RESIDENT, chat_type="supergroup")
    asyncio.run(group.handle_group_message(message))

    assert _values(db, "5") == {}
    assert message.dm and "только по своей" in message.dm[0]


# ---------------------------------------------------------------------------
# Показания председателя не должны попадать в её собственную квартиру
# ---------------------------------------------------------------------------

def test_chairman_message_without_a_flat_number_is_refused_in_chat(db):
    """Без номера квартиры показания председателя не идут в её строку."""
    message = Msg("Эл.эн 15230\nХвс 123\nГвс 88", chat_type="supergroup")
    asyncio.run(group.handle_group_message(message))

    assert _values(db, "1") == {}                  # квартира председателя пуста
    assert message.dm and "без номера квартиры" in message.dm[0]


def test_resident_message_without_a_number_still_uses_their_flat(db):
    """У жителя подстановка своей квартиры остаётся — это привычный ввод."""
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "7")
        repository.create_user(conn, RESIDENT, "Житель", flat["id"])
    finally:
        conn.close()

    message = Msg("Эл.эн 15230\nХвс 123", tg_id=RESIDENT, chat_type="supergroup")
    asyncio.run(group.handle_group_message(message))

    assert _values(db, "7")["electricity"] == 15230.0


def test_chairman_message_without_a_number_is_refused_in_private(db):
    message = Msg("Эл.эн 15230\nХвс 123")
    asyncio.run(manual.manual_readings(message))

    assert _values(db, "1") == {}
    assert "Не понял, к какому помещению" in message.answers[0]


def test_pasted_readings_in_the_dialog_need_a_flat_number(db, monkeypatch):
    """Открыт диалог по своей квартире, а вставлены чужие показания."""
    from bot.handlers import readings as readings_handler

    real_connect = repository.connect
    monkeypatch.setattr(readings_handler.repository, "connect",
                        lambda *a, **kw: real_connect(db))
    monkeypatch.setattr(readings_handler, "config",
                        replace(readings_handler.config, admin_ids=(CHAIRMAN,)))

    conn = repository.connect(db)
    try:
        own = repository.get_apartment_by_number(conn, "1")
    finally:
        conn.close()

    class State:
        def __init__(self):
            self.cleared = False

        async def get_data(self):
            return {"apartment_id": own["id"], "user_id": None,
                    "queue": ["electricity"], "saved": {}, "warnings": []}

        async def clear(self):
            self.cleared = True

    message, state = Msg("Эл.эн 15230\nХвс 123\nГвс 88"), State()
    asyncio.run(readings_handler.process_value(message, state))

    assert _values(db, "1") == {}                  # ничего не записали
    assert "нет номера квартиры" in message.answers[0]
    assert not state.cleared                       # диалог не закрыт
