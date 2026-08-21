"""Точка входа DH OS. Запуск: python run.py"""
import asyncio
import sys

from bot.keepawake import allow_sleep
from bot.main import main


def _say(text: str) -> None:
    """Сообщение в окно терминала. При автозапуске окна нет — молчим."""
    if sys.stdout is not None:
        print(text)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _say("DH OS остановлен.")
    # SystemExit не перехватываем: Python сам напечатает причину остановки
    # («нет токена», «бот уже запущен»). Раньше её проглатывал общий except,
    # и окно закрывалось молча.
    finally:
        # Бот больше не работает — ноутбук снова может засыпать сам
        allow_sleep()
