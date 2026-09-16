"""Разбор даты, введённой человеком: «30.09.2026», «30.09.26», «30.09».

Дату в бота вводят руками, в трёх разных местах (срок задачи, дата оплаты,
дата поверки), и раньше каждое место разбирало её само одной строкой
``date(int(year), int(month), int(day))``. На «30.09.26» это давало 30
сентября 26 года — в плане потом стояло «просрочено на 730471 дн.».

Правила здесь одни на всех:

* две цифры года — это двухтысячные: «26» -> 2026;
* года нет вовсе — подставляем подходящий, см. ``prefer``;
* год заведомо не наш (раньше 2000 или дальше чем через 50 лет) — отказ.
  Лучше переспросить, чем молча записать дату из первого века.

Разобранную дату вызывающий код всегда показывает человеку полностью
(«Срок: 30.09.2026»), чтобы подставленный год было видно сразу.
"""
import re
from datetime import date, timedelta

# Разделители: 30.09.2026, 30/09/2026, 30-09-2026, «30 09 2026»
SPLIT_RE = re.compile(r"[.\-/\s]+")

TODAY_WORDS = ("сегодня", "today")
TOMORROW_WORDS = ("завтра",)
YESTERDAY_WORDS = ("вчера",)

# Дальше этих границ дата почти наверняка описка, а не намерение
MIN_YEAR = 2000
MAX_YEARS_AHEAD = 50


def _full_year(raw: int) -> int | None:
    """«26» -> 2026, «2026» -> 2026, всё остальное — отказ."""
    year = 2000 + raw if raw < 100 else raw
    if year < MIN_YEAR or year > date.today().year + MAX_YEARS_AHEAD:
        return None
    return year


def _year_without_year(day: int, month: int, today: date, prefer: str) -> int | None:
    """Год для даты, введённой без года: «30.09».

    ``prefer='future'`` — срок задачи: он всегда впереди, поэтому берём
    ближайший подходящий год вперёд. ``prefer='past'`` — дата оплаты или
    поверки: она уже случилась, берём ближайший назад. ``prefer='nearest'``
    — что ближе к сегодняшнему дню.
    """
    candidates = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidates.append(date(year, month, day))
        except ValueError:            # 29 февраля в невисокосный год
            continue
    if not candidates:
        return None

    if prefer == "future":
        ahead = [d for d in candidates if d >= today]
        return ahead[0].year if ahead else candidates[-1].year
    if prefer == "past":
        behind = [d for d in candidates if d <= today]
        return behind[-1].year if behind else candidates[0].year
    return min(candidates, key=lambda d: abs((d - today).days)).year


def parse_user_date(text: str | None, today: date | None = None,
                    prefer: str = "future") -> date | None:
    """Дата из введённого текста или None, если разобрать не удалось.

    ``prefer`` подсказывает, куда смотреть, когда год не написан:
    «future» — срок задачи, «past» — уже случившееся (оплата, поверка).
    """
    today = today or date.today()
    value = (text or "").strip().lower()

    if value in TODAY_WORDS:
        return today
    if value in TOMORROW_WORDS:
        return today + timedelta(days=1)
    if value in YESTERDAY_WORDS:
        return today - timedelta(days=1)

    parts = [p for p in SPLIT_RE.split(value) if p]
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        return None

    day, month = int(parts[0]), int(parts[1])
    if len(parts) == 3:
        year = _full_year(int(parts[2]))
    else:
        year = _year_without_year(day, month, today, prefer)
    if year is None:
        return None

    try:
        return date(year, month, day)
    except ValueError:                # 31 апреля, 45 месяц и подобное
        return None


def looks_broken(value: str) -> bool:
    """Дата из базы записана «не нашим» годом — 0026-09-30 и подобное."""
    try:
        return date.fromisoformat(value).year < MIN_YEAR
    except (ValueError, TypeError):
        return False


def repair_year(value: str) -> str:
    """«0026-09-30» -> «2026-09-30». Остальное возвращаем как есть."""
    if not looks_broken(value):
        return value
    broken = date.fromisoformat(value)
    return broken.replace(year=broken.year + 2000).isoformat()
