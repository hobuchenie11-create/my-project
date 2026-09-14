"""Подсказка при обрыве связи: председатель должна понять, что делать.

Самый частый отказ запуска — выключенный клиент VPN: порт из PROXY_URL
никто не слушает. Раньше это выглядело как стек ошибок из недр aiohttp.
"""
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
