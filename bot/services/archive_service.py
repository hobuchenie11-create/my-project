"""Готовые документы — в папку председателя на компьютере.

Ведомость и реестр приходят в Telegram, и каждый месяц их приходилось
скачивать вручную: из чата в «Загрузки», оттуда — в нужную папку, где они
лежат по месяцам. Бот собирает файл на том же компьютере, поэтому может
положить его сразу куда нужно.

Папки задаются в .env двумя строками:

    STATEMENTS_DIR — ведомости дома (передачи и непередавших);
    DOCS_DIR       — заполненные реестры ОЭК.

Стопки разные по смыслу: ведомости остаются домовым архивом, реестры
уходят ресурснику. STATEMENTS_DIR не задан — ведомости идут в DOCS_DIR.
Обе строки пустые — ничего не копируем, бот работает как раньше: это
должен быть осознанный выбор председателя, а не сюрприз в виде файлов,
появившихся неизвестно где.

Ведомости ложатся прямо в свою папку: месяц уже в имени файла
(vedomost_2026-10.xlsx), и подпапки только мешали бы. А реестр ОЭК носит
имя, которое задаёт ресурсник, и каждый месяц оно одно и то же — такой
файл уходит в подпапку месяца, иначе новый затирал бы прошлый.
"""
import logging
import shutil
from pathlib import Path

from bot.config import config

logger = logging.getLogger(__name__)


STATEMENT = "statement"     # ведомости дома
REGISTRY = "registry"       # реестры ресурсника


def folder_for(kind: str) -> Path | None:
    """В какую папку кладём документ этого вида."""
    if kind == REGISTRY:
        return config.docs_dir
    return config.statements_dir or config.docs_dir


def _target(path: Path, period: str | None, folder: Path) -> Path:
    """Куда ляжет файл: месяц в имени — прямо в папку, иначе в подпапку."""
    same_name_each_month = bool(period) and period not in path.stem
    return (folder / period / path.name if same_name_each_month
            else folder / path.name)


def saved_path(path: Path, period: str | None = None,
               kind: str = STATEMENT) -> Path | None:
    """Где лежит копия документа — чтобы назвать путь в сообщении."""
    folder = folder_for(kind)
    if folder is None:
        return None
    target = _target(Path(path), period, folder)
    return target if target.exists() else None


def archive(path: Path, period: str | None = None,
            kind: str = STATEMENT) -> Path | None:
    """Кладёт копию документа в папку председателя. None — папка не задана.

    Ошибку копирования не поднимаем наверх: документ уже готов и уйдёт в
    Telegram, а из-за отключённой флешки или занятого файла терять его
    нельзя. Причина остаётся в журнале.
    """
    folder = folder_for(kind)
    if folder is None:
        return None

    target = _target(Path(path), period, folder)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    except OSError as exc:
        logger.warning("Не удалось сохранить %s в папку %s: %s",
                       path.name, folder, exc)
        return None

    logger.info("Документ сохранён: %s", target)
    return target


def archive_note(target: Path | None) -> str:
    """Строка для сообщения в чат: куда лёг файл. Пусто — папка не задана."""
    if target is None:
        return ""
    return f"\n📁 Сохранено: <code>{target}</code>"
