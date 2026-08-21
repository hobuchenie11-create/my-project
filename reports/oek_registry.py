"""Реестр ОЭК: берём шаблон ресурсника и проставляем в него показания.

Из кода:  generate_oek_registry(period)  ->  OekResult
Вручную:  python -m reports.oek_registry [ГГГГ-ММ]

Шаблон бот берёт из папки OEK_TEMPLATE_DIR — самый свежий файл .xls/.xlsx,
кроме уже заполненных им самим. Положить туда файл можно двумя способами:
скопировать руками или прислать боту в личку (см. bot/handlers/oek.py).
"""
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

from bot.config import config
from bot.services.reading_service import current_period
from database import repository
from excel.oek_registry import (TEMPLATE_SUFFIXES, OekFormatError, OekResult,
                                apartment_key, fill_registry)

# Заполненные ботом файлы лежат рядом с шаблонами — по префиксу их видно
OUT_PREFIX = "reestr_oek_"


class NoTemplateError(Exception):
    """Шаблона ОЭК нет — заполнять нечего."""


def templates_dir() -> Path:
    path = config.oek_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def find_template(directory: Path | None = None) -> Path | None:
    """Самый свежий шаблон ресурсника в папке (заполненные ботом пропускаем)."""
    directory = Path(directory) if directory else templates_dir()
    if not directory.exists():
        return None
    candidates = [p for p in directory.iterdir()
                  if p.is_file()
                  and p.suffix.lower() in TEMPLATE_SUFFIXES
                  and not p.name.startswith(OUT_PREFIX)
                  and not p.name.startswith("~$")]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def save_template(source: Path, directory: Path | None = None) -> Path:
    """Кладёт присланный ресурсником файл в папку шаблонов."""
    import shutil

    directory = Path(directory) if directory else templates_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / Path(source).name
    if target.resolve() != Path(source).resolve():
        shutil.copyfile(source, target)
    return target


def electricity_readings(conn: sqlite3.Connection, period: str) -> dict[str, float]:
    """Последние показания электросчётчиков за период: {номер помещения: кВт·ч}.

    Берём то же, что уходит в ведомость 20 числа: последняя запись по каждому
    прибору, включая исправления. Показания, принятые после срока, тоже здесь —
    если они успели прийти до выгрузки, ресурснику лучше отдать их сразу.
    """
    return {apartment_key(row["apartment_number"]): row["value"]
            for row in repository.readings_for_period(conn, period)
            if row["kind"] == "electricity"}


def known_apartments(conn: sqlite3.Connection) -> set[str]:
    return {apartment_key(row["number"])
            for row in repository.list_apartments(conn)}


def generate_oek_registry(period: str | None = None,
                          template: Path | None = None,
                          taken_on: date | None = None) -> OekResult:
    """Заполняет реестр ОЭК за период. Бросает NoTemplateError/OekFormatError."""
    period = period or current_period()
    template = Path(template) if template else find_template()
    if template is None:
        raise NoTemplateError(
            "В папке нет шаблона ОЭК. Пришлите боту файл, который прислал "
            f"ресурсник, или положите его в {templates_dir()}")

    conn = repository.connect()
    try:
        readings = electricity_readings(conn, period)
        known = known_apartments(conn)
    finally:
        conn.close()

    suffix = template.suffix.lower()
    out_path = config.reports_dir / f"{OUT_PREFIX}{period}{suffix}"
    try:
        result = fill_registry(template, readings, out_path,
                               taken_on=taken_on or _taken_on(period),
                               known_apartments=known)
    except PermissionError:
        # Прошлый реестр открыт в Excel — Windows не даёт перезаписать файл.
        # Отказываться из-за этого нельзя: 20 числа в 14:30 реестр нужен
        # председателю, а открытая книга — обычное дело. Сохраняем рядом.
        out_path = (config.reports_dir
                    / f"{OUT_PREFIX}{period}_{datetime.now():%d%m_%H%M}{suffix}")
        result = fill_registry(template, readings, out_path,
                               taken_on=taken_on or _taken_on(period),
                               known_apartments=known)

    conn = repository.connect()
    try:
        repository.save_report(conn, period, str(result.path))
    finally:
        conn.close()
    return result


def _taken_on(period: str) -> date:
    """Дата снятия показаний — день выгрузки ведомости в этом периоде."""
    year, month = (int(part) for part in period.split("-"))
    return date(year, month, config.statement_day)


if __name__ == "__main__":
    period_arg = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        outcome = generate_oek_registry(period_arg)
    except (NoTemplateError, OekFormatError) as exc:
        raise SystemExit(str(exc))
    print(outcome.summary())
    print(f"\nФайл: {outcome.path}")
