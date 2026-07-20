"""Резервное копирование базы данных."""
import shutil
from datetime import datetime
from pathlib import Path

from bot.config import config


def make_backup() -> Path:
    """Копирует базу в backups/ и возвращает путь к копии."""
    config.backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = config.backups_dir / f"dhos_{stamp}.db"
    shutil.copy2(config.db_path, target)
    return target


if __name__ == "__main__":
    print(f"Резервная копия: {make_backup()}")
