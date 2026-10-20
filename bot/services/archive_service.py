"""Готовые документы — в папку председателя на компьютере.

Ведомость и реестр приходят в Telegram, и каждый месяц их приходилось
скачивать вручную: из чата в «Загрузки», оттуда — в нужную папку, где они
лежат по месяцам. Бот собирает файл на том же компьютере, поэтому может
положить его сразу куда нужно.

Папка задаётся строкой DOCS_DIR в .env. Пусто — ничего не копируем, бот
работает как раньше: это должен быть осознанный выбор председателя, а не
сюрприз в виде файлов, появившихся неизвестно где.

Ведомости ложатся прямо в указанную папку: месяц уже в имени файла
(vedomost_2026-10.xlsx), и подпапки только мешали бы. А реестр ОЭК носит
имя, которое задаёт ресурсник, и каждый месяц оно одно и то же — такой
файл уходит в подпапку месяца, иначе новый затирал бы прошлый.
"""
import logging
import shutil
from pathlib import Path

from bot.config import config

logger = logging.getLogger(__name__)


def _target(path: Path, period: str | None) -> Path:
    """Куда ляжет файл: месяц в имени — прямо в папку, иначе в подпапку."""
    same_name_each_month = bool(period) and period not in path.stem
    folder = (config.docs_dir / period if same_name_each_month
              else config.docs_dir)
    return folder / path.name


def saved_path(path: Path, period: str | None = None) -> Path | None:
    """Где лежит копия документа — чтобы назвать путь в сообщении."""
    if config.docs_dir is None:
        return None
    target = _target(Path(path), period)
    return target if target.exists() else None


def archive(path: Path, period: str | None = None) -> Path | None:
    """Кладёт копию документа в папку председателя. None — папка не задана.

    Ошибку копирования не поднимаем наверх: документ уже готов и уйдёт в
    Telegram, а из-за отключённой флешки или занятого файла терять его
    нельзя. Причина остаётся в журнале.
    """
    if config.docs_dir is None:
        return None

    target = _target(Path(path), period)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    except OSError as exc:
        logger.warning("Не удалось сохранить %s в папку %s: %s",
                       path.name, config.docs_dir, exc)
        return None

    logger.info("Документ сохранён: %s", target)
    return target


def archive_note(target: Path | None) -> str:
    """Строка для сообщения в чат: куда лёг файл. Пусто — папка не задана."""
    if target is None:
        return ""
    return f"\n📁 Сохранено: <code>{target}</code>"
