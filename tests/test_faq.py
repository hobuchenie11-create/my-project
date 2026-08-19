"""Памятки Домоведа: загрузка из файлов, поиск ответа, журнал пробелов."""
import asyncio
from types import SimpleNamespace

import pytest

from bot.services import faq_service
from database import repository
from database.init_db import init_db

MEMO = """---
title: Как оплатить квитанцию
category: payments
keywords: оплата, оплатить, квитанция, реквизиты, спецсчёт
order: 10
---
Оплатить можно в банке или через приложение.
"""

GATES = """---
title: Как пользоваться воротами
category: gates
keywords: ворота, шлагбаум, пульт, брелок, заехать
image: vorota.jpg
order: 10
---
Ворота открываются пультом или звонком с вашего номера.
"""


@pytest.fixture()
def conn(tmp_path):
    db = tmp_path / "faq.db"
    init_db(db, apartments_count=2, nonresidential_count=1)
    conn = repository.connect(db)
    yield conn
    conn.close()


@pytest.fixture()
def memos(tmp_path, conn):
    directory = tmp_path / "faq"
    directory.mkdir()
    (directory / "oplata.md").write_text(MEMO, encoding="utf-8")
    (directory / "vorota.md").write_text(GATES, encoding="utf-8")
    (directory / "README.md").write_text("# описание формата", encoding="utf-8")
    faq_service.load_memos(conn, directory)
    return directory


def test_files_become_memos(conn, memos):
    rows = repository.active_memos(conn)
    assert [row["code"] for row in rows] == ["oplata", "vorota"]  # README пропущен

    memo = faq_service.by_code(conn, "oplata")
    assert memo.title == "Как оплатить квитанцию"
    assert memo.category == "payments"
    assert memo.body == "Оплатить можно в банке или через приложение."
    assert "Как оплатить квитанцию" in memo.text()


def test_reload_updates_instead_of_duplicating(conn, memos):
    (memos / "oplata.md").write_text(
        MEMO.replace("в банке или через приложение", "только через банк"),
        encoding="utf-8")
    faq_service.load_memos(conn, memos)

    assert len(repository.active_memos(conn)) == 2
    assert "только через банк" in faq_service.by_code(conn, "oplata").body


def test_removed_file_leaves_the_menu(conn, memos):
    (memos / "vorota.md").unlink()
    faq_service.load_memos(conn, memos)

    assert [row["code"] for row in repository.active_memos(conn)] == ["oplata"]
    assert faq_service.by_code(conn, "vorota") is None


def test_question_finds_the_memo(conn, memos):
    for question in ("как оплатить квитанцию?",
                     "куда платить взносы, подскажите реквизиты",
                     "оплата"):
        found = faq_service.search(conn, question)
        assert found and found[0].code == "oplata", question

    found = faq_service.search(conn, "не открываются ворота, где взять пульт")
    assert found and found[0].code == "vorota"


def test_categories_only_where_memos_exist(conn, memos):
    assert faq_service.categories(conn) == ["payments", "gates"]
    assert [m.code for m in faq_service.by_category(conn, "gates")] == ["vorota"]


def test_unknown_question_is_remembered(conn, memos):
    assert faq_service.search(conn, "когда покрасят качели во дворе") == []

    faq_service.remember_gap(conn, 555, "12", "когда покрасят качели во дворе")
    text = faq_service.gaps_text(conn)
    assert "качели" in text and "кв. 12" in text


def test_gaps_text_when_everything_is_answered(conn):
    assert "Вопросов без ответа нет" in faq_service.gaps_text(conn)


def test_question_without_meaningful_words_is_not_searched(conn, memos):
    """«Здравствуйте!» — не вопрос к базе знаний."""
    assert faq_service.search(conn, "Здравствуйте!") == []
    assert faq_service.search(conn, "а как же так") == []


def test_readings_are_not_treated_as_a_question(conn, memos, monkeypatch):
    """Показания разбираются раньше — до памяток они доходить не должны."""
    from bot.handlers import manual

    real_connect = repository.connect
    monkeypatch.setattr(manual.repository, "connect",
                        lambda *a, **kw: real_connect(conn.execute(
                            "PRAGMA database_list").fetchone()[2]))

    asked = []

    async def fake_answer(message, tg_id, apartment=""):
        asked.append(message.text)

    monkeypatch.setattr("bot.handlers.faq.answer_question", fake_answer)

    class Msg:
        def __init__(self, text):
            self.text = text
            self.chat = SimpleNamespace(id=1, type="private")
            self.from_user = SimpleNamespace(id=1, username="u")
            self.answers = []

        async def answer(self, text, **kwargs):
            self.answers.append(text)

    asyncio.run(manual.manual_readings(Msg("Кв. 1\nЭл.эн 100\nХвс 5\nГвс 7")))
    assert asked == []                       # показания в памятки не ушли

    asyncio.run(manual.manual_readings(Msg("где взять пульт от ворот")))
    assert asked == ["где взять пульт от ворот"]
