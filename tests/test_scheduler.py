"""Календарь бота: когда что уходит и почему не повторяется.

Объявление о завершении сбора однажды ушло в чат дома трижды: отметка
«сегодня уже отправлено» жила в памяти процесса, а бота в тот день
перезапускали. Теперь отметка в базе, и рассылку проверяем именно на
повторных запусках.
"""
import asyncio
from dataclasses import replace
from datetime import datetime

import pytest

from bot import scheduler
from bot.config import config
from database import repository
from database.init_db import init_db

GROUP_CHAT = -1001111111111


class FakeBot:
    def __init__(self):
        self.sent: list[tuple[int, str]] = []

    async def send_message(self, chat_id, text, **kwargs):
        self.sent.append((chat_id, text))


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """База во временной папке — и планировщик, и отметки идут в неё."""
    path = tmp_path / "scheduler.db"
    init_db(path, apartments_count=2, nonresidential_count=0)
    real_connect = repository.connect
    monkeypatch.setattr(repository, "connect",
                        lambda db_path=None: real_connect(db_path or path))
    return path


@pytest.fixture()
def bot(monkeypatch):
    """Планировщик без Telegram: остаются только рассылки, которые проверяем."""
    async def noop(*args, **kwargs):
        return 0

    for name in ("send_reminders", "send_debtors_statement",
                 "send_monthly_statement", "send_oek_registry",
                 "send_task_reminders"):
        monkeypatch.setattr(scheduler, name, noop)
    # Config заморожен — подменяем целиком, а не отдельное поле
    monkeypatch.setattr(scheduler, "config",
                        replace(config, group_chat_id=GROUP_CHAT))
    return FakeBot()


def _tick(bot, moment):
    asyncio.run(scheduler._tick(bot, moment))


def test_announcement_waits_for_its_hour(db, bot):
    """В 14:00 уходит ведомость председателю, но не объявление жителям."""
    _tick(bot, datetime(2026, 8, config.announce_day, config.statement_hour))
    assert bot.sent == []

    _tick(bot, datetime(2026, 8, config.announce_day, config.announce_hour))
    assert [chat for chat, _ in bot.sent] == [GROUP_CHAT]
    assert "завершён" in bot.sent[0][1]


def test_announcement_is_not_repeated_after_a_restart(db, bot):
    """Тот же день, новый запуск бота — второго объявления в чате быть не должно."""
    moment = datetime(2026, 8, config.announce_day, config.announce_hour)
    _tick(bot, moment)
    _tick(bot, moment.replace(hour=config.announce_hour + 1))   # перезапуск
    _tick(bot, moment.replace(hour=config.announce_hour + 3))   # и ещё один

    assert len(bot.sent) == 1


def test_next_month_announcement_goes_out_again(db, bot):
    _tick(bot, datetime(2026, 8, config.announce_day, config.announce_hour))
    _tick(bot, datetime(2026, 9, config.announce_day, config.announce_hour))

    assert len(bot.sent) == 2


def test_oek_registry_waits_half_an_hour_after_the_statement(db, bot, monkeypatch):
    """Реестр ОЭК уходит 20 числа в 14:30 — минутой раньше ещё рано.

    Из-за минут задача и заставила проверять календарь чаще, чем раз в
    десять минут: при прежнем шаге реестр мог уйти почти в 14:40.
    """
    built = []

    async def fake_registry(_bot):
        built.append(True)

    monkeypatch.setattr(scheduler, "send_oek_registry", fake_registry)
    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour,
                        config.oek_minute - 1))
    assert built == []

    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour,
                        config.oek_minute))
    assert built == [True]

    # Перезапуск в тот же день второй реестр не порождает
    _tick(bot, datetime(2026, 8, config.oek_day, config.oek_hour + 2))
    assert built == [True]


def test_oek_registry_is_not_built_on_other_days(db, bot, monkeypatch):
    built = []

    async def fake_registry(_bot):
        built.append(True)

    monkeypatch.setattr(scheduler, "send_oek_registry", fake_registry)
    _tick(bot, datetime(2026, 8, config.oek_day + 1, config.oek_hour + 1))

    assert built == []


def test_statement_does_not_announce_by_itself(db, bot, monkeypatch):
    """Ведомость уходит председателю молча: объявление — отдельная задача."""
    generated = []

    async def fake_statement(_bot):
        generated.append(True)

    monkeypatch.setattr(scheduler, "send_monthly_statement", fake_statement)
    _tick(bot, datetime(2026, 8, config.statement_day, config.statement_hour))

    assert generated == [True]
    assert bot.sent == []
