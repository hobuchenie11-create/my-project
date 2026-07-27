"""Подключение к Telegram через прокси (Nekobox/Hiddify и т.п.).

Для SOCKS-прокси принудительно включаем удаленное определение имени
(rdns): адрес api.telegram.org разрешает сам прокси, а не локальный
компьютер, где имя может быть подменено провайдером. Написание socks5h в
адресе не используем — не все версии библиотек его понимают.
"""
import ssl as _ssl

import certifi


def normalize_proxy_url(proxy_url: str) -> str:
    # socks5h -> socks5 (rdns включаем в коде, а не в схеме адреса)
    return proxy_url.replace("socks5h://", "socks5://").replace("socks4a://", "socks4://")


def _ssl_context() -> _ssl.SSLContext:
    return _ssl.create_default_context(cafile=certifi.where())


def build_socks_connector(proxy_url: str):
    """Свежий ProxyConnector с удаленным DNS (rdns=True)."""
    from aiohttp_socks import ProxyConnector
    return ProxyConnector.from_url(normalize_proxy_url(proxy_url), rdns=True,
                                   ssl=_ssl_context())


def make_session(proxy_url: str | None):
    """AiohttpSession для aiogram с учетом прокси. None -> прямое подключение."""
    from aiogram.client.session.aiohttp import AiohttpSession

    if not proxy_url:
        return AiohttpSession()

    if proxy_url.startswith("socks"):
        session = AiohttpSession()
        url = normalize_proxy_url(proxy_url)
        # aiogram вызывает self._connector_type(**self._connector_init) на каждую
        # сессию — отдаем фабрику, создающую ProxyConnector с rdns=True.
        session._connector_type = lambda **_: build_socks_connector(url)
        session._connector_init = {}
        return session

    # http/https-прокси aiogram обрабатывает штатно
    return AiohttpSession(proxy=proxy_url)
