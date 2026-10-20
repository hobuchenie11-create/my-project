"""История показаний одной квартиры — для председателя.

Полная история всех квартир лежит в книге Excel, но открывать её ради
одного вопроса «что у кв. 49 было в сентябре» долго. Это та же история,
собранная в сообщение: месяц, показания по приборам, расход за месяц и
откуда показания пришли.

Текст написан так, чтобы его можно было переслать жителю: без служебных
пометок и внутренних примечаний, с адресом дома в заголовке — пересланное
сообщение читается отдельно от переписки.
"""
import sqlite3

from bot.services.reading_service import unit_for
from database import repository
from database.models import METER_KINDS, SOURCE_LABELS, period_title

# Сколько месяцев показываем. Шесть — это полгода, по ним видно и расход,
# и пропуски; больше в одно сообщение Telegram уже не всегда влезает.
MONTHS_SHOWN = 6


def _display(apartment: sqlite3.Row) -> str:
    if apartment["type"] != "residential":
        return apartment["number"]
    return f"кв. {apartment['number']}"


def _kind_order(conn: sqlite3.Connection, apartment_id: int,
                kinds: set[str]) -> list[str]:
    """Приборы в том порядке, в каком они стоят у квартиры.

    Приборы, которых в наборе уже нет (квартиру перевели на другой набор),
    показываем после — показания по ним передавались, и прятать их нельзя.
    """
    order = [m["kind"] for m in repository.meters_for_apartment(conn, apartment_id)
             if m["kind"] in kinds]
    return order + [kind for kind in METER_KINDS if kind in kinds
                    and kind not in order]


def _value(value: float, kind: str) -> str:
    return f"{value:g} {unit_for(kind)}"


def apartment_history_text(conn: sqlite3.Connection, apartment: sqlite3.Row,
                           months: int = MONTHS_SHOWN) -> str:
    """История показаний квартиры за последние месяцы — готовым сообщением."""
    from bot.texts import HOUSE_ADDRESS

    rows = repository.readings_for_apartment(conn, apartment["id"])
    head = (f"📊 <b>История показаний</b> — {_display(apartment)}\n"
            f"{HOUSE_ADDRESS}")
    if not rows:
        return (f"{head}\n\nПоказания через бота не передавались.\n\n"
                "Если житель передавал их на бумаге или напрямую "
                "ресурсоснабжающей организации, в боте их нет.")

    # Последнее показание прибора за месяц — то же, что идёт в ведомость.
    # Исправления остаются в базе, но здесь важна итоговая цифра; то, что
    # показание правили, отмечаем отдельно.
    latest: dict[str, dict[str, float]] = {}       # период -> прибор -> значение
    fixes: dict[tuple[str, str], int] = {}         # сколько раз передавали
    meta: dict[str, sqlite3.Row] = {}              # период -> последняя запись
    for row in rows:
        latest.setdefault(row["period"], {})[row["kind"]] = row["value"]
        fixes[(row["period"], row["kind"])] = fixes.get(
            (row["period"], row["kind"]), 0) + 1
        meta[row["period"]] = row

    periods = sorted(latest, reverse=True)
    lines = [head, ""]
    for period in periods[:months]:
        values = latest[period]
        row = meta[period]
        when = row["created_at"][8:10] + "." + row["created_at"][5:7]
        source = SOURCE_LABELS.get(row["source"], row["source"])
        late = ", после срока" if row["late"] else ""
        lines.append(f"<b>{period_title(period).capitalize()}</b> "
                     f"— передано {when}, {source}{late}:")
        for kind in _kind_order(conn, apartment["id"], set(values)):
            line = f"• {METER_KINDS.get(kind, kind)}: {_value(values[kind], kind)}"
            line += _spent_note(latest, periods, period, kind)
            if fixes[(period, kind)] > 1:
                line += " · исправлялось"
            lines.append(line)
        lines.append("")

    if len(periods) > months:
        lines.append(f"Показаны последние {months} месяцев из "
                     f"{len(periods)}. Вся история — в книге Excel, "
                     "лист «Переданные показания».")
    else:
        lines.append("Расход в скобках — к предыдущему переданному "
                     "показанию этого прибора.")
    return "\n".join(lines).strip()


def _spent_note(latest: dict[str, dict[str, float]], periods: list[str],
                period: str, kind: str) -> str:
    """Расход за месяц в скобках: разница с прошлым показанием прибора.

    Прошлый месяц мог быть пропущен — тогда берём ближайший месяц, когда
    показание по этому прибору было, и так и говорим: расход за два месяца
    и за один выглядят одинаково, а это разные цифры.
    """
    older = [p for p in periods if p < period and kind in latest[p]]
    if not older:
        return ""
    previous = older[0]
    spent = latest[period][kind] - latest[previous][kind]
    if spent < 0:
        # Счётчик заменили или в цифре опечатка. Отрицательный расход —
        # не расход, и выдавать его за расход нельзя
        return " · ниже предыдущего (замена счётчика?)"
    months = _months_between(previous, period)
    tail = f" за {months} мес." if months > 1 else ""
    return f" (+{spent:g}{tail})"


def _months_between(first: str, second: str) -> int:
    year, month = int(first[:4]), int(first[5:7])
    other_year, other_month = int(second[:4]), int(second[5:7])
    return (other_year - year) * 12 + other_month - month
