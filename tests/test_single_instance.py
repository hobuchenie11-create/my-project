"""Один Домовед на компьютер: автозапуск и ручной запуск не должны драться."""
import asyncio
from dataclasses import replace

import pytest

from bot import main as bot_main
from bot import single_instance
from bot.config import config


@pytest.fixture()
def with_token(monkeypatch):
    """Токен на месте — проверяем именно сторож запуска, а не настройки."""
    monkeypatch.setattr(bot_main, "config", replace(config, bot_token="test:token"))


def test_second_instance_refuses_to_start(monkeypatch, with_token):
    """Бот уже работает — второй процесс останавливается с внятной причиной.

    Telegram отдаёт getUpdates то одному процессу, то другому (Conflict),
    и часть показаний жителей теряется по дороге.
    """
    monkeypatch.setattr(single_instance, "acquire", lambda *a, **kw: False)

    with pytest.raises(SystemExit) as stop:
        asyncio.run(bot_main.main())

    assert "уже запущен" in str(stop.value)


def test_the_guard_lets_the_only_instance_through():
    """Свободное имя занимается, повторный вызов в том же процессе не мешает."""
    name = "DH_OS_test_single_instance"
    assert single_instance.acquire(name) is True
    # Тот же процесс второй раз себе не мешает — ручка уже у нас
    assert single_instance.acquire(name) is True


def test_a_broken_guard_does_not_block_the_bot(monkeypatch):
    """Сторож сломался — это не повод не запускать бота."""
    monkeypatch.setattr(single_instance, "_handle", None)
    monkeypatch.setattr(single_instance.platform, "system", lambda: "Linux")

    assert single_instance.acquire("whatever") is True
