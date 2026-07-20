"""Разбор показаний из свободного текста (сообщения в общем чате дома).

Словарь распознавания построен на реальных сообщениях жителей. Одни и те же
приборы жители пишут десятками способов, например:

    электроэнергия:  Св · Эл.эн · Э/энер · Электроэнергия · Эл. энерг. · Эл.Эн.
    холодная вода:   Хв · ХВС · Хол · Х.В. · хвс (кухня) · Хол. Кух.
    горячая вода:    Гв · ГВС · Гор · Г.В. · гвс (ванна) · Ван. Гор.
    санузел:         с/у · с/уз · сан.узел · туал · ванна · ван
    кухня:           кух · кухня
    сумма ГВС:       сумма гв · Сумма гвс · гвс (итого)

Разделителем между названием и числом может быть пробел, тире, двоеточие,
точка или запятая. Числа принимаются с ведущими нулями (0000076) и с
запятой в дробной части.

Итог разбора — нормализованные виды приборов:
    electricity, gas,
    cws, cws_kitchen, cws_bathroom,
    hws, hws_kitchen, hws_bathroom, hws_total
Как они ложатся на конкретную квартиру (1-2-комнатную или 3-комнатную) —
решает reading_service по набору приборов квартиры.
"""
import re
from dataclasses import dataclass, field

from bot.services.validation import parse_value

# Номер квартиры: «Кв. 12», «квартира №5», «Кв, 29», «Кв 58»
APARTMENT_RE = re.compile(r"кв\w*\.?\s*[,№]?\s*(\d{1,4})", re.IGNORECASE)
NONRESIDENTIAL_RE = re.compile(r"нежило\w*\s*(?:помещение)?\s*№?\s*(\d+)", re.IGNORECASE)

# Число в конце строки (допускаем ведущие нули и дробную часть).
# Знак не захватываем: тире/дефис в сообщениях жителей — это разделитель
# («Хвс кухня - 6»), а не минус; показания всегда неотрицательны.
VALUE_RE = re.compile(r"\d[\d\s]*(?:[.,]\d+)?\s*$")


def _normalize(label: str) -> str:
    """Убирает разделители, оставляя только буквы, для сопоставления по словарю."""
    return re.sub(r"[^а-яёa-z]", "", label.lower())


# Ключевые слова (по нормализованной подписи). Проверяются как вхождение.
ELECTRICITY_KW = ("электро", "элэн", "эленер", "элэнер", "эенер", "ээнер",
                  "ээн", "эенер", "эдектро", "свет", "св", "эл", "ээ")
GAS_KW = ("газ",)
TOTAL_KW = ("итог", "сумм", "сум")
COLD_KW = ("хвс", "хв", "холод", "хол", "хв")
HOT_KW = ("гвс", "гв", "горяч", "гор", "гв")
KITCHEN_KW = ("кухн", "кух")
BATHROOM_KW = ("сануз", "санузел", "суз", "су", "туал", "ванна", "ванн", "ван", "сан")


def _has(label: str, keywords) -> bool:
    return any(kw in label for kw in keywords)


@dataclass
class ParsedReadings:
    apartment_number: str | None = None
    values: dict[str, float] = field(default_factory=dict)
    ignored: list[str] = field(default_factory=list)   # газ и прочее, что не учитываем
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not self.values


def parse_message(text: str) -> ParsedReadings:
    result = ParsedReadings()

    m = NONRESIDENTIAL_RE.search(text)
    if m:
        result.apartment_number = f"Нежилое помещение №{m.group(1)}"
    else:
        m = APARTMENT_RE.search(text)
        if m:
            result.apartment_number = m.group(1)

    context: str | None = None  # 'cold' | 'hot' — тип воды из предыдущих строк

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        value_match = VALUE_RE.search(line)
        if not value_match:
            continue
        label_part = line[: value_match.start()]
        label = _normalize(label_part)
        if not label:
            continue
        # Строка с номером квартиры — не показание
        if label in ("кв", "квартира", "кварт"):
            continue

        value = parse_value(value_match.group())

        kind, context = _classify(label, context)
        if kind is None:
            continue
        if kind == "gas":
            result.ignored.append(f"газ ({value_match.group().strip()})")
            continue
        if value is None:
            result.errors.append(f"Не удалось разобрать число в строке: «{line}»")
            continue
        if kind in result.values:
            result.errors.append(f"Прибор «{label_part.strip()}» указан дважды")
            continue
        result.values[kind] = value

    return result


def _classify(label: str, context: str | None) -> tuple[str | None, str | None]:
    """Определяет вид прибора по нормализованной подписи.

    Возвращает (вид, новый_контекст_воды). Вид None — строку игнорируем.
    """
    # Электроэнергия и газ — отдельные метки, проверяем первыми
    if _has(label, GAS_KW):
        return "gas", context
    if _has(label, ELECTRICITY_KW) and not _has(label, COLD_KW + HOT_KW):
        return "electricity", context

    is_cold = _has(label, COLD_KW)
    is_hot = _has(label, HOT_KW)
    is_kitchen = _has(label, KITCHEN_KW)
    is_bathroom = _has(label, BATHROOM_KW)
    is_total = _has(label, TOTAL_KW)

    # Тип воды из строки либо из контекста предыдущих строк
    if is_cold and not is_hot:
        water = "cold"
    elif is_hot and not is_cold:
        water = "hot"
    else:
        water = context
    if water is None:
        return None, context  # не поняли строку

    if water == "hot" and is_total:
        return "hws_total", "hot"

    prefix = "cws" if water == "cold" else "hws"
    if is_kitchen:
        return f"{prefix}_kitchen", water
    if is_bathroom:
        return f"{prefix}_bathroom", water
    # Локация не указана — один прибор на квартиру (или итоговый ГВС)
    return prefix, water
