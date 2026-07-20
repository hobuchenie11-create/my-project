"""Настройка логирования: консоль + файл с ротацией в logs/."""
import logging
from logging.handlers import RotatingFileHandler

from bot.config import config


def setup_logging() -> None:
    config.logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

    file_handler = RotatingFileHandler(config.logs_dir / "dhos.log",
                                       maxBytes=1_000_000, backupCount=5,
                                       encoding="utf-8")
    file_handler.setFormatter(fmt)

    console = logging.StreamHandler()
    console.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(file_handler)
    root.addHandler(console)
