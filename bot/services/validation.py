"""Проверка вводимых показаний."""
from dataclasses import dataclass

from database.models import DELTA_WARN_DEFAULT, DELTA_WARN_LIMITS


def parse_value(text: str) -> float | None:
    """Разбирает число из текста пользователя (принимает запятую и точку)."""
    cleaned = text.strip().replace(",", ".").replace(" ", "")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value < 0 or value > 10_000_000:
        return None
    return value


@dataclass
class CheckResult:
    ok: bool
    error: str = ""
    warning: str = ""


def check_reading(kind: str, new_value: float, last_value: float | None) -> CheckResult:
    """Сверяет новое показание с предыдущим.

    Меньше предыдущего — ошибка (замену счетчика оформляет председатель).
    Аномально большой расход — принимается, но с предупреждением.
    """
    if last_value is None:
        return CheckResult(ok=True)

    if new_value < last_value:
        return CheckResult(
            ok=False,
            error=(f"Показание {new_value:g} меньше предыдущего ({last_value:g}). "
                   "Проверьте цифры. Если счетчик заменили — сообщите председателю."),
        )

    delta = new_value - last_value
    limit = DELTA_WARN_LIMITS.get(kind, DELTA_WARN_DEFAULT)
    if delta > limit:
        return CheckResult(
            ok=True,
            warning=(f"Расход за месяц получился {delta:g} — это необычно много. "
                     "Показание записано, но проверьте, нет ли опечатки."),
        )
    return CheckResult(ok=True)
