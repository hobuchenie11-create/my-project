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
    proxy_url: str | None = os.getenv("PROXY_URL") or None
    # Период сбора показаний: с 15 по 19 число включительно
    readings_day_start: int = int(os.getenv("READINGS_DAY_START", "15"))
    readings_day_end: int = int(os.getenv("READINGS_DAY_END", "19"))
    # Ведомость со всеми собранными показаниями: 20 числа в 10:00
    statement_day: int = int(os.getenv("STATEMENT_DAY", "20"))
    statement_hour: int = int(os.getenv("STATEMENT_HOUR", "10"))
    reminder_days: tuple[int, ...] = field(
        default_factory=lambda: _parse_int_list(os.getenv("REMINDER_DAYS", "15,17,19")))
    # Когда автоматически формировать ведомость непередавших
    debtors_day: int = int(os.getenv("DEBTORS_DAY", "20"))
    debtors_hour: int = int(os.getenv("DEBTORS_HOUR", "9"))

    base_dir: Path = BASE_DIR
    db_path: Path = BASE_DIR / "database" / "dhos.db"
    logs_dir: Path = BASE_DIR / "logs"
    backups_dir: Path = BASE_DIR / "backups"
    reports_dir: Path = BASE_DIR / "reports" / "generated"
    data_dir: Path = BASE_DIR / "data"


config = Config()
