"""Подсказка при обрыве связи: председатель должна понять, что делать.

Самый частый отказ запуска — выключенный клиент VPN: порт из PROXY_URL
никто не слушает. Раньше это выглядело как стек ошибок из недр aiohttp.
"""
import asyncio
from dataclasses import replace

import pytest

from bot import main as bot_main
from bot.config import config

PROXY_ERROR = "[Errno 22] Couldn't connect to proxy 127.0.0.1:12334"


@pytest.fixture()
def with_proxy(monkeypatch):
    monkeypatch.setattr(bot_main, "config",
                        replace(config, proxy_url="socks5://127.0.0.1:12334"))


@pytest.fixture()
def without_proxy(monkeypatch):
    monkeypatch.setattr(bot_main, "config", replace(config, proxy_url=None))


def test_proxy_failure_names_the_vpn_client(with_proxy):
    hint = bot_main._connection_hint(ConnectionError(PROXY_ERROR))

    assert "127.0.0.1:12334" in hint
    assert "VPN" in hint                    # что именно не запущено
    assert "PROXY_URL" in hint              # где сверить порт
    assert ".env" in hint


def test_hint_keeps_the_original_error(with_proxy):
    hint = bot_main._connection_hint(ConnectionError(PROXY_ERROR))
    assert "ConnectionError" in hint and PROXY_ERROR in hint


def test_without_proxy_the_hint_is_about_the_internet(without_proxy):
    hint = bot_main._connection_hint(OSError("Network is unreachable"))

    assert "PROXY_URL" not in hint
    assert "интернет" in hint.lower()
    assert "Network is unreachable" in hint


# ---------------------------------------------------------------------------
# Прокси не отвечает: пробуем прямое подключение
# ---------------------------------------------------------------------------

class FakeSession:
    def __init__(self):
        self.closed = False

    async def close(self):
        self.closed = True


class FakeMe:
    username = "domoved_bot"


class FakeBot:
    """Бот, у которого первый запрос падает, а после смены сессии — проходит."""

    def __init__(self, direct_works: bool):
        self.direct_works = direct_works
        self.session = FakeSession()
        self.calls = 0

    async def get_me(self):
        self.calls += 1
        if self.calls == 1 or not self.direct_works:
            raise ConnectionError(PROXY_ERROR)
        return FakeMe()


def test_direct_connection_saves_the_start(with_proxy, monkeypatch):
    """Порт из .env закрыт, но VPN работает системно — бот всё равно стартует."""
    monkeypatch.setattr(bot_main, "make_session", lambda url: FakeSession())
    bot = FakeBot(direct_works=True)
    session = bot.session

    asyncio.run(bot_main._check_connection(bot, session))

    assert session.closed is True          # прокси-сессию закрыли
    assert bot.calls == 2                  # вторая попытка — напрямую


def test_both_paths_dead_reports_the_proxy_reason(with_proxy, monkeypatch):
    """Прямое подключение тоже не вышло — объясняем про прокси, а не про него."""
    monkeypatch.setattr(bot_main, "make_session", lambda url: FakeSession())
    bot = FakeBot(direct_works=False)

    with pytest.raises(SystemExit) as exc:
        asyncio.run(bot_main._check_connection(bot, bot.session))

    assert "127.0.0.1:12334" in str(exc.value)
    assert "VPN" in str(exc.value)


def test_without_proxy_there_is_nothing_to_fall_back_to(without_proxy):
    bot = FakeBot(direct_works=False)

    with pytest.raises(SystemExit) as exc:
        asyncio.run(bot_main._check_connection(bot, bot.session))

    assert bot.calls == 1                  # второй попытки не было
    assert "интернет" in str(exc.value).lower()
