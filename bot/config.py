"""Конфигурация DH OS. Значения читаются из файла .env в корне проекта."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _parse_int_list(raw: str) -> tuple[int, ...]:
    return tuple(int(x) for x in raw.replace(";", ",").split(",") if x.strip().lstrip("-").isdigit())


@dataclass(frozen=True)
class Config:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_ids: tuple[int, ...] = field(default_factory=lambda: _parse_int_list(os.getenv("ADMIN_IDS", "")))
    apartments_count: int = int(os.getenv("APARTMENTS_COUNT", "80"))
    nonresidential_count: int = int(os.getenv("NONRESIDENTIAL_COUNT", "2"))
    group_chat_id: int | None = int(os.getenv("GROUP_CHAT_ID")) if os.getenv("GROUP_CHAT_ID") else None
    readings_day_start: int = int(os.getenv("READINGS_DAY_START", "20"))
    readings_day_end: int = int(os.getenv("READINGS_DAY_END", "25"))
    reminder_days: tuple[int, ...] = field(
        default_factory=lambda: _parse_int_list(os.getenv("REMINDER_DAYS", "17,23,25")))

    base_dir: Path = BASE_DIR
    db_path: Path = BASE_DIR / "database" / "dhos.db"
    logs_dir: Path = BASE_DIR / "logs"
    backups_dir: Path = BASE_DIR / "backups"
    reports_dir: Path = BASE_DIR / "reports" / "generated"
    data_dir: Path = BASE_DIR / "data"


config = Config()
