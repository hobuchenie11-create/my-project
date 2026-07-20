"""Точка входа DH OS. Запуск: python run.py"""
import asyncio

from bot.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("DH OS остановлен.")
