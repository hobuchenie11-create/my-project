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
class Amount:
    """Сумма платежа: итог и, если вводили по частям, расшифровка.

    Председатель платит по нескольким квитанциям сразу, поэтому сумму удобно
    вводить так, как она сложилась: 214,33+155+207. Бот считает итог сам,
    а разбивку сохраняет — иначе потом не вспомнить, из чего сложилось.
    """
    total: float
    parts: list[float]

    @property
    def is_split(self) -> bool:
        return len(self.parts) > 1

    def breakdown(self, label: str) -> str:
        """«Квитанции: 214,33 + 155 + 207» — строка для примечания."""
        if not self.is_split:
            return ""
        return f"{label}: " + " + ".join(money(p) for p in self.parts)


def money(value: float) -> str:
    """1234.5 -> «1234,5»: запятая привычнее в рублях."""
    return f"{value:g}".replace(".", ",")


def parse_amount(text: str) -> Amount | None:
    """Разбирает сумму: одно число или несколько через «+».

    Принимает «214,33+155,0+207», «214.33 + 155 + 207», «4520,30».
    """
    cleaned = (text or "").strip().replace(" ", "").rstrip("+")
    if not cleaned:
        return None

    parts = []
    for chunk in cleaned.split("+"):
        value = parse_value(chunk)
        if value is None:
            return None
        parts.append(value)

    total = round(sum(parts), 2)
    if total > 10_000_000:
        return None
    return Amount(total=total, parts=parts)


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
