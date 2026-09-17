"""Фото бумажного бланка: полуавтомат вместо распознавания.

Цифры с фотографии бот не читает. Он принимает снимок, спрашивает
квартиру и отдаёт форму под её приборы с прошлыми показаниями рядом —
переписать остаётся только цифры. Молчать в ответ на фото нельзя: это
неотличимо от «принял», а показаний в ведомости потом нет.
"""
import asyncio
from dataclasses import replace
from types import SimpleNamespace

import pytest

from bot.handlers import photos
from bot.services.reading_service import save_parsed_readings
from bot.services.parser import parse_message
from database import repository
from database.init_db import init_db
from database.models import apartment_meters

CHAIRMAN = 555
RESIDENT = 777


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
    def __init__(self, text=None, chat_type="private", tg_id=CHAIRMAN,
                 chat_id=None, mime=None, caption=None):
        self.text = text
        self.caption = caption
        self.from_user = SimpleNamespace(id=tg_id, full_name="Житель",
                                         username="u")
        self.chat = SimpleNamespace(
            id=chat_id if chat_id is not None else -100123,
            type=chat_type, title="Дом")
        self.document = SimpleNamespace(mime_type=mime) if mime else None
        self.answers: list[str] = []
        self.replies: list[str] = []

    async def answer(self, text, **kwargs):
        self.answers.append(text)

    async def reply(self, text, **kwargs):
        self.replies.append(text)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    path = tmp_path / "photos.db"
    init_db(path, apartments_count=80, nonresidential_count=1)
    conn = repository.connect(path)
    # кв. 9 — трёхкомнатная, четыре счётчика воды
    flat = repository.get_apartment_by_number(conn, "9")
    repository.set_meters(conn, flat["id"], apartment_meters(2, 2))
    # у кв. 54 есть прошлый месяц — форма должна его показать
    fifty_four = repository.get_apartment_by_number(conn, "54")
    save_parsed_readings(conn, fifty_four,
                         parse_message("Кв 54\nЭл.эн 16000\nХвс 250\nГвс 200"),
                         None, period="2026-08")
    conn.commit()
    conn.close()

    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    monkeypatch.setattr(photos, "config",
                        replace(photos.config, admin_ids=(CHAIRMAN,),
                                council_chat_id=-500))
    return path


# ---------------------------------------------------------------------------
# Кто что слышит в ответ на фото
# ---------------------------------------------------------------------------

def test_resident_is_told_the_photo_was_not_read(db):
    message = Msg(tg_id=RESIDENT)
    asyncio.run(photos.handle_photo(message, FakeState()))

    answer = message.answers[0]
    assert "не записаны" in answer
    assert "Хвс 267" in answer            # готовый образец под рукой
    assert "кухня" in answer              # и подсказка про четыре счётчика


def test_photo_in_the_house_chat_gets_a_short_reply(db):
    message = Msg(chat_type="supergroup", tg_id=RESIDENT)
    asyncio.run(photos.handle_photo(message, FakeState()))

    assert message.replies and "не записаны" in message.replies[0]
    assert message.answers == []


def test_council_chat_is_left_alone(db):
    """В чате Совета свои фотографии — актов, счетов, подъездов."""
    message = Msg(chat_type="supergroup", tg_id=CHAIRMAN, chat_id=-500)
    asyncio.run(photos.handle_photo(message, FakeState()))

    assert message.replies == [] and message.answers == []


def test_a_deleted_message_in_the_chat_does_not_break_the_bot(db):
    from aiogram.exceptions import TelegramBadRequest

    message = Msg(chat_type="supergroup", tg_id=RESIDENT)

    async def refuse(text, **kwargs):
        raise TelegramBadRequest(method=SimpleNamespace(),
                                 message="message to be replied not found")

    message.reply = refuse
    asyncio.run(photos.handle_photo(message, FakeState()))   # не должно упасть


@pytest.mark.parametrize("mime, expected", [
    ("image/jpeg", True),
    ("image/png", True),
    ("application/vnd.ms-excel", False),
    (None, False),
])
def test_image_sent_as_a_file_is_recognised(mime, expected):
    """Фото «без сжатия» приходит документом — иначе его заберёт модуль задач."""
    assert photos._is_image_document(Msg(mime=mime)) is expected


# ---------------------------------------------------------------------------
# Полуавтомат: снимок — номер — форма
# ---------------------------------------------------------------------------

def test_chairman_is_asked_for_the_apartment(db):
    state = FakeState()
    message = Msg(tg_id=CHAIRMAN)
    asyncio.run(photos.handle_photo(message, state))

    assert "По какой квартире" in message.answers[0]
    assert state.state is not None, "бот должен ждать номер"


def test_form_lists_the_meters_and_the_previous_month(db):
    state = FakeState()
    asyncio.run(photos.handle_photo(Msg(tg_id=CHAIRMAN), state))

    answer = Msg("54", tg_id=CHAIRMAN)
    asyncio.run(photos.blank_apartment_number(answer, state))

    form = answer.answers[0]
    assert "кв. 54" in form
    assert "Кв. 54\nЭл.эн\nХвс\nГвс" in form        # готова к заполнению
    assert "Прошлые показания" in form
    assert "16000" in form and "250" in form
    assert state.cleared


def test_form_for_a_flat_with_four_water_meters(db):
    """Трёхкомнатная: в форме места счётчиков, чтобы не гадать при вводе."""
    state = FakeState()
    asyncio.run(photos.handle_photo(Msg(tg_id=CHAIRMAN), state))

    answer = Msg("кв. 9", tg_id=CHAIRMAN)
    asyncio.run(photos.blank_apartment_number(answer, state))

    form = answer.answers[0]
    assert "Хвс кухня" in form and "Хвс санузел" in form
    assert "Гвс кухня" in form and "Гвс санузел" in form
    assert "Прошлых показаний по этой квартире нет" in form


def test_number_in_the_caption_skips_the_question(db):
    """Подписали снимок «кв. 54» — форма приходит сразу."""
    state = FakeState()
    message = Msg(tg_id=CHAIRMAN, caption="кв. 54")
    asyncio.run(photos.handle_photo(message, state))

    assert "Бланк · кв. 54" in message.answers[0]
    assert state.state is None, "спрашивать номер незачем"


def test_unknown_number_asks_again(db):
    state = FakeState()
    answer = Msg("999", tg_id=CHAIRMAN)
    asyncio.run(photos.blank_apartment_number(answer, state))

    assert "Не нашла" in answer.answers[0]
    assert not state.cleared, "диалог должен остаться открытым"


def test_cancel_closes_the_dialog(db):
    state = FakeState()
    answer = Msg("отмена", tg_id=CHAIRMAN)
    asyncio.run(photos.blank_apartment_number(answer, state))

    assert state.cleared
    assert "отложила" in answer.answers[0]


def test_readings_instead_of_a_number_are_recorded(db, monkeypatch):
    """Переписала цифры сразу, не отвечая на вопрос, — записываем их."""
    from bot.handlers import manual
    monkeypatch.setattr(manual, "config",
                        replace(manual.config, admin_ids=(CHAIRMAN,)))

    state = FakeState()
    answer = Msg("Кв 54\nЭл.эн 16553\nХвс 267\nГвс 215", tg_id=CHAIRMAN)
    asyncio.run(photos.blank_apartment_number(answer, state))

    assert state.cleared
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "54")
        rows = repository.readings_history_for_apartment(conn, flat["id"])
        values = [r["value"] for r in rows]
    finally:
        conn.close()
    assert 16553.0 in values, "показания с переписанного бланка должны записаться"


# ---------------------------------------------------------------------------
# Карточка помещения: один номер без цифр
# ---------------------------------------------------------------------------

def test_history_card_shows_every_meter_by_month(db, monkeypatch):
    """«Показание меньше предыдущего» — решить, чья цифра неверна, можно
    только увидев обе."""
    from bot.handlers import manual
    from bot.services import blank_service

    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "54")
        save_parsed_readings(conn, flat,
                             parse_message("Кв 54\nЭл.эн 16553\nХвс 267\nГвс 215"),
                             None, period="2026-09")
        conn.commit()
        card = blank_service.history_text(conn, flat)
    finally:
        conn.close()

    assert "кв. 54" in card
    assert "09.2026 — 16553" in card and "08.2026 — 16000" in card
    assert "09.2026 — 267" in card and "08.2026 — 250" in card
    assert "Исправить" in card


def test_chairman_sees_the_card_for_a_bare_number(db, monkeypatch):
    from bot.handlers import manual
    monkeypatch.setattr(manual, "config",
                        replace(manual.config, admin_ids=(CHAIRMAN,)))

    message = Msg("Кв. 54", tg_id=CHAIRMAN)
    asyncio.run(manual.manual_readings(message))

    assert "кв. 54" in message.answers[0]
    assert "08.2026 — 16000" in message.answers[0]


def test_resident_still_gets_the_old_hint(db, monkeypatch):
    """Жителю карточка соседа ни к чему — ему нужна подсказка про формат."""
    from bot.handlers import manual
    monkeypatch.setattr(manual, "config",
                        replace(manual.config, admin_ids=(CHAIRMAN,)))

    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "54")
        repository.create_user(conn, RESIDENT, "Житель", flat["id"])
        conn.commit()
    finally:
        conn.close()

    message = Msg("Кв. 54", tg_id=RESIDENT)
    asyncio.run(manual.manual_readings(message))

    assert "Напишите прибор и число" in message.answers[0]


def test_card_for_a_flat_without_readings(db):
    from bot.services import blank_service

    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "9")
        card = blank_service.history_text(conn, flat)
    finally:
        conn.close()

    assert "показаний по этому помещению ещё не было" in card.lower()


def test_form_asks_for_the_hot_water_total_as_a_check(db):
    """На бланке житель пишет итог по ГВС — пусть служит контрольной цифрой."""
    from bot.services import blank_service

    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "9")   # четыре счётчика
        form = blank_service.form_text(conn, flat)
    finally:
        conn.close()

    assert "Сумма гвс" in form
    assert "в ведомость она не записывается" in form


def test_no_total_line_when_hot_water_is_one_meter(db):
    """Один ГВС — складывать нечего, лишняя строка только запутает."""
    from bot.services import blank_service

    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "54")
        form = blank_service.form_text(conn, flat)
    finally:
        conn.close()

    assert "Сумма гвс" not in form


def test_the_total_is_checked_not_stored(db):
    """Итог в приборы не идёт, но расхождение бот называет."""
    conn = repository.connect(db)
    try:
        flat = repository.get_apartment_by_number(conn, "9")
        outcome = save_parsed_readings(conn, flat, parse_message(
            "Кв 9\nГвс кухня 435\nГвс санузел 300\nСумма гвс 999"),
            None, period="2026-09")
    finally:
        conn.close()

    assert outcome.saved == {"hws_kitchen": 435.0, "hws_bathroom": 300.0}
    assert any("не сходится" in w for w in outcome.warnings)
