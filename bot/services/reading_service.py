"""Сохранение и просмотр показаний."""
import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime

from bot.services.parser import ParsedReadings
from bot.services.validation import CheckResult, check_reading
from database import repository
from database.models import DEFAULT_UNIT, METER_KINDS, METER_UNITS


def current_period(today: date | None = None) -> str:
    today = today or date.today()
    return f"{today.year:04d}-{today.month:02d}"


def is_late(moment: date | datetime | None = None) -> bool:
    """Показание передано после того, как ведомость уже сформирована?

    Сбор идёт с READINGS_DAY_START по READINGS_DAY_END (15–19), но ведомость
    уходит ресурсникам только STATEMENT_DAY в STATEMENT_HOUR (20 числа в 14:00).
    Всё, что пришло до этого момента, в ведомость ещё попадает и «опозданием»
    не считается — иначе утренние показания 20 числа помечались бы зря.
    """
    from bot.config import config

    moment = moment or datetime.now()
    if moment.day != config.statement_day:
        return moment.day > config.statement_day

    # В день формирования решает час: до 14:00 показания ещё попадут в ведомость
    hour = moment.hour if isinstance(moment, datetime) else config.statement_hour
    return hour >= config.statement_hour


def period_title(period: str) -> str:
    months = ["январь", "февраль", "март", "апрель", "май", "июнь", "июль",
              "август", "сентябрь", "октябрь", "ноябрь", "декабрь"]
    year, month = period.split("-")
    return f"{months[int(month) - 1]} {year}"


def unit_for(kind: str) -> str:
    return METER_UNITS.get(kind, DEFAULT_UNIT)


def save_reading(conn: sqlite3.Connection, apartment_id: int, kind: str, value: float,
                 user_id: int | None, source: str = "bot",
                 period: str | None = None, late: bool | None = None,
                 correction: bool = False) -> CheckResult:
    """Проверяет и сохраняет одно показание. Возвращает результат проверки.

    Правка (correction=True) переписывает уже принятое показание за период:
    в ведомость идёт последняя запись, поэтому старую не удаляем — она
    остаётся в истории. Сверяем такую запись не с ошибочной цифрой этого же
    месяца, а с показанием прошлого месяца, иначе исправить завышенное
    показание было бы нечем: «меньше предыдущего» отклоняло бы правку.
    """
    meter = repository.get_meter(conn, apartment_id, kind)
    if meter is None:
        return CheckResult(ok=False, error=f"У помещения нет прибора «{METER_KINDS[kind]}»")

    period = period or current_period()
    previous = repository.reading_for_period(conn, meter["id"], period)
    last = (repository.last_reading_before_period(conn, meter["id"], period)
            if correction else repository.last_reading(conn, meter["id"]))
    result = check_reading(kind, value, last["value"] if last else None)
    if result.ok:
        if late is None:
            # Правка не делает показание опоздавшим: пометку наследуем от той
            # записи, которую переписываем — исправляют обычно уже после срока
            late = (bool(previous["late"]) if correction and previous
                    else is_late())
        repository.add_reading(conn, meter["id"], user_id, period, value,
                               "correction" if correction else source,
                               late=late)
    return result


@dataclass
class SaveOutcome:
    """Итог записи показаний из одного сообщения (общий чат)."""
    saved: dict[str, float] = field(default_factory=dict)  # kind -> value
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    replaced: dict[str, float] = field(default_factory=dict)  # что было до правки

    @property
    def anything_saved(self) -> bool:
        return bool(self.saved)


def save_parsed_readings(conn: sqlite3.Connection, apartment: sqlite3.Row,
                         parsed: ParsedReadings, user_id: int | None,
                         source: str = "chat", period: str | None = None,
                         late: bool | None = None,
                         correction: bool = False) -> SaveOutcome:
    """Раскладывает распознанные показания на приборы конкретной квартиры.

    Один ХВС/ГВС (compact-планировка, нежилое) и раздельный учет (full-планировка)
    поддерживаются одновременно — исходя из набора приборов квартиры.
    «Сумма/итого ГВС» для 3-комнатных не хранится отдельно (она выводится как
    кухня + ванна), но используется для сверки.
    """
    outcome = SaveOutcome()
    available = {m["kind"] for m in repository.meters_for_apartment(conn, apartment["id"])}
    values = dict(parsed.values)

    hws_total = values.pop("hws_total", None)
    # В квартире с раздельным учётом строка «ГВС» без кухни/ванны — это итог,
    # а не отдельный прибор: жители часто дописывают его для проверки.
    folded = _fold_totals(values, available)
    hws_total = hws_total if hws_total is not None else folded.get("hws")
    # Обратный случай: прибор один, а показание подписано местом установки
    _fold_locations(values, available, outcome, apartment)

    for kind, value in values.items():
        target = _resolve_meter_kind(kind, available)
        if target is None:
            outcome.errors.append(
                f"«{METER_KINDS.get(kind, kind)}»: у {_display(apartment)} нет такого прибора"
            )
            continue
        was = (_current_value(conn, apartment["id"], target,
                              period or current_period())
               if correction else None)
        result = save_reading(conn, apartment["id"], target, value, user_id,
                              source=source, period=period, late=late,
                              correction=correction)
        if result.ok:
            outcome.saved[target] = value
            if was is not None and was != value:
                outcome.replaced[target] = was
            if result.warning:
                outcome.warnings.append(f"{METER_KINDS[target]}: {result.warning}")
        else:
            outcome.errors.append(result.error)

    _check_hws_total(outcome, hws_total, values, available)
    _check_total(outcome, "ХВС", folded.get("cws"), values,
                 ("cws_kitchen", "cws_bathroom"))
    return outcome


def _current_value(conn: sqlite3.Connection, apartment_id: int, kind: str,
                   period: str) -> float | None:
    """Показание, которое сейчас стоит в ведомости за период (до правки)."""
    meter = repository.get_meter(conn, apartment_id, kind)
    if meter is None:
        return None
    row = repository.reading_for_period(conn, meter["id"], period)
    return row["value"] if row else None


def _fold_totals(values: dict[str, float],
                 available: set[str]) -> dict[str, float]:
    """Забирает из показаний общие «ГВС»/«ХВС» там, где учёт раздельный.

    Такая строка — не прибор, а итог для сверки: считать её отсутствующим
    прибором и пугать жителя ошибкой не за что.
    """
    totals = {}
    for single, kitchen in (("hws", "hws_kitchen"), ("cws", "cws_kitchen")):
        if single in values and single not in available and kitchen in available:
            totals[single] = values.pop(single)
    return totals


def _fold_locations(values: dict[str, float], available: set[str],
                    outcome: SaveOutcome, apartment: sqlite3.Row) -> None:
    """Прибор один, а показание подписано местом: «ХВС сан.узел» = «ХВС».

    В однокомнатной счётчики обычно стоят в санузле, и жители пишут именно
    место. Пока показание одно, двусмысленности нет — записываем в
    единственный прибор. Если мест названо два, а прибор один, это уже
    расхождение со справочником: молча выбирать одно из значений нельзя.
    """
    for single, parts in (("cws", ("cws_kitchen", "cws_bathroom")),
                          ("hws", ("hws_kitchen", "hws_bathroom"))):
        if single not in available or single in values:
            continue
        present = [kind for kind in parts if kind in values]
        if len(present) == 1:
            values[single] = values.pop(present[0])
        elif len(present) > 1:
            named = " и ".join(f"«{METER_KINDS[kind]}»" for kind in present)
            outcome.errors.append(
                f"{named}: у {_display(apartment)} один счётчик "
                f"{METER_KINDS[single]} — уточните, какое показание записать")
            for kind in present:
                values.pop(kind)


def _resolve_meter_kind(kind: str, available: set[str]) -> str | None:
    if kind in available:
        return kind
    # Один ГВС на квартиру, а прислали раздельно (или наоборот) — не сходится
    if kind == "cws" and "cws" not in available:
        return None
    if kind == "hws" and "hws" not in available:
        return None
    return None


def _check_total(outcome: SaveOutcome, label: str, total: float | None,
                 values: dict[str, float], parts: tuple[str, str]) -> None:
    """Сверяет присланный итог с суммой кухня+санузел. Сходится — молчим."""
    if total is None:
        return
    numbers = [values.get(key) for key in parts]
    if any(n is None for n in numbers):
        return
    calc = sum(numbers)
    if abs(calc - total) > 0.001:
        outcome.warnings.append(
            f"Сумма {label} ({total:g}) не сходится с кухня+санузел "
            f"({calc:g}) — проверьте")


def _check_hws_total(outcome: SaveOutcome, hws_total: float | None,
                     values: dict[str, float], available: set[str]) -> None:
    if hws_total is None:
        return
    if "hws_kitchen" in available:
        parts = [values.get("hws_kitchen"), values.get("hws_bathroom")]
        if all(p is not None for p in parts):
            calc = sum(parts)
            if abs(calc - hws_total) > 0.001:
                outcome.warnings.append(
                    f"Сумма ГВС ({hws_total:g}) не сходится с кухня+ванна ({calc:g}) — проверьте"
                )
    elif "hws" in available and "hws" not in outcome.saved:
        # compact-квартира прислала только «сумму ГВС» — засчитываем как ГВС
        outcome.warnings.append("Сумма ГВС записана как показание ГВС")


def _display(apartment: sqlite3.Row) -> str:
    # Нежилые помещения и общедомовой прибор называются полностью,
    # приписка «кв.» им не нужна
    if apartment["type"] != "residential":
        return apartment["number"]
    return f"кв. {apartment['number']}"


def receipt_text(conn: sqlite3.Connection, apartment: sqlite3.Row,
                 saved: dict[str, float], when: datetime | None = None,
                 replaced: dict[str, float] | None = None) -> str:
    """Квитанция-подтверждение после передачи показаний (Этап 5).

    Для правки показываем и прежнюю цифру: по квитанции сразу видно, что
    именно ушло в ведомость вместо ошибочного показания.
    """
    when = when or datetime.now()
    replaced = replaced or {}
    header = ("✏️ {} — показания исправлены" if replaced
              else "✅ {} — показания приняты")
    lines = [header.format(_display(apartment)), ""]
    for meter in repository.meters_for_apartment(conn, apartment["id"]):
        kind = meter["kind"]
        if kind not in saved:
            continue
        line = f"{METER_KINDS[kind]}: {saved[kind]:g}"
        if kind in replaced:
            line += f"  (было {replaced[kind]:g})"
        lines.append(line)
    lines.append("")
    lines.append(f"{'Исправлено' if replaced else 'Передано'}: "
                 f"{when.strftime('%d.%m.%Y %H:%M')}")
    return "\n".join(lines)


def last_reading_value(conn: sqlite3.Connection, apartment_id: int, kind: str) -> float | None:
    meter = repository.get_meter(conn, apartment_id, kind)
    if meter is None:
        return None
    last = repository.last_reading(conn, meter["id"])
    return last["value"] if last else None


def my_last_readings_text(conn: sqlite3.Connection, apartment_id: int) -> str:
    lines = ["📄 Последние показания:", ""]
    found = False
    for meter in repository.meters_for_apartment(conn, apartment_id):
        last = repository.last_reading(conn, meter["id"])
        if last:
            found = True
            lines.append(f"{METER_KINDS[meter['kind']]}: {last['value']:g} "
                         f"{unit_for(meter['kind'])} (за {last['period']})")
        else:
            lines.append(f"{METER_KINDS[meter['kind']]}: показаний еще нет")
    if not found:
        return "Показания еще не передавались."
    return "\n".join(lines)


def history_text(conn: sqlite3.Connection, apartment_id: int) -> str:
    rows = repository.readings_history_for_apartment(conn, apartment_id)
    if not rows:
        return "История пуста — показания еще не передавались."
    lines = ["📊 История передач (последние записи):", ""]
    for row in rows:
        lines.append(f"{row['created_at'][:16]} · {row['period']} · "
                     f"{METER_KINDS[row['kind']]}: {row['value']:g}")
    return "\n".join(lines)
