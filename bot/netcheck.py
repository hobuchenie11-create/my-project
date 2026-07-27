"""Проверка подключения к Telegram — напрямую и через PROXY_URL.

Запуск:  python -m bot.netcheck

Показывает по шагам, где обрывается связь: открыт ли локальный порт прокси
(Nekobox/Hiddify) и доступен ли через него api.telegram.org.
"""
import asyncio
import socket
from urllib.parse import urlparse

from bot.config import config


async def check() -> None:
    print("=== Проверка подключения к Telegram ===")
    print("PROXY_URL:", config.proxy_url or "(не задан — бот идёт напрямую)")
    print()

    # 1. Локальный порт прокси
    if config.proxy_url:
        parsed = urlparse(config.proxy_url)
        host, port = parsed.hostname, parsed.port
        try:
            socket.create_connection((host, port), timeout=5).close()
            print(f"[OK]     Порт прокси {host}:{port} открыт — клиент слушает.")
        except OSError as exc:
            print(f"[ОШИБКА] Не удалось подключиться к прокси {host}:{port}: {exc}")
            print("         -> Проверьте: Nekobox запущен и в состоянии «Подключено»,")
            print("            и что номер порта в PROXY_URL совпадает с портом Nekobox.")
            return

    # 2. Доступ к Telegram
    import aiohttp

    connector = None
    proxy = None
    if config.proxy_url and config.proxy_url.startswith("socks"):
        try:
            from aiohttp_socks import ProxyConnector
        except ImportError:
            print("[ОШИБКА] Не установлен пакет aiohttp-socks.")
            print("         -> Выполните: python -m pip install -r requirements.txt")
            return
        connector = ProxyConnector.from_url(config.proxy_url)
    elif config.proxy_url:  # http/https-прокси
        proxy = config.proxy_url

    timeout = aiohttp.ClientTimeout(total=15)
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get("https://api.telegram.org", proxy=proxy) as resp:
                print(f"[OK]     Telegram доступен (ответ {resp.status}).")
                print()
                print("Готово — можно запускать бота: python run.py")
    except Exception as exc:  # noqa: BLE001 - диагностика
        print(f"[ОШИБКА] Telegram недоступен: {type(exc).__name__}: {exc}")
        print("         -> Если порт прокси открыт (шаг выше [OK]), проверьте, что")
        print("            в Nekobox выбран и запущен рабочий сервер (значок зелёный).")


if __name__ == "__main__":
    asyncio.run(check())
