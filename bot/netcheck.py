"""Подбор рабочего прокси для подключения к Telegram.

Запуск:  python -m bot.netcheck

Проверяет, какие локальные порты слушает ваш VPN-клиент (Nekobox/Hiddify),
и через какой из них реально открывается api.telegram.org. В конце печатает
готовую строку PROXY_URL, которую нужно вписать в .env.
"""
import asyncio
import socket
from urllib.parse import urlparse

import aiohttp

from bot.config import config
from bot.proxy import build_socks_connector

HOST = "127.0.0.1"
# Порты, которые чаще всего использует Nekobox/xray/v2ray/Hiddify
CANDIDATE_PORTS = [2080, 2081, 10808, 10809, 1080, 7890, 2334, 12334, 20170, 20171]
TEST_URL = "https://api.telegram.org"


def _port_open(host: str, port: int) -> bool:
    try:
        socket.create_connection((host, port), timeout=3).close()
        return True
    except OSError:
        return False


async def _try_socks(url: str) -> str | None:
    try:
        connector = build_socks_connector(url)
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as s:
            async with s.get(TEST_URL) as r:
                return f"ответ {r.status}"
    except Exception:  # noqa: BLE001 - перебор вариантов
        return None


async def _try_http(url: str) -> str | None:
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(TEST_URL, proxy=url) as r:
                return f"ответ {r.status}"
    except Exception:  # noqa: BLE001 - перебор вариантов
        return None


async def check() -> None:
    print("=== Подбор рабочего прокси для Telegram ===\n")

    # 1. Собираем список портов: сначала из .env, потом популярные
    ports: list[int] = []
    if config.proxy_url:
        p = urlparse(config.proxy_url).port
        if p:
            ports.append(p)
    for p in CANDIDATE_PORTS:
        if p not in ports:
            ports.append(p)

    open_ports = [p for p in ports if _port_open(HOST, p)]
    if not open_ports:
        print("[ОШИБКА] Не найдено ни одного открытого локального порта прокси.")
        print("         -> Запустите Nekobox и подключитесь к рабочему серверу")
        print("            (значок зелёный), затем повторите проверку.")
        return

    print("Открытые порты (клиент слушает):", ", ".join(map(str, open_ports)), "\n")

    # 2. Для каждого открытого порта пробуем SOCKS и HTTP
    for port in open_ports:
        for scheme, tester in (("socks5", _try_socks), ("http", _try_http)):
            url = f"{scheme}://{HOST}:{port}"
            print(f"Пробую {url} ... ", end="", flush=True)
            result = await tester(url)
            if result:
                print(f"OK ({result})")
                print("\n================ РАБОЧИЙ ВАРИАНТ ================")
                print(f"Впишите в .env:  PROXY_URL={url}")
                print("================================================")
                return
            print("не подходит")

    print("\n[ОШИБКА] Ни один вариант не открыл Telegram.")
    print("         Возможные причины:")
    print("         - в Nekobox не выбран/не запущен рабочий сервер (значок зелёный);")
    print("         - сервер сам не пропускает api.telegram.org.")
    print("         Проверьте, открывается ли https://api.telegram.org в браузере")
    print("         именно через Nekobox, и пришлите список Inbound-портов Nekobox.")


if __name__ == "__main__":
    asyncio.run(check())
