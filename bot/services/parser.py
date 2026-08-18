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
from database.models import COMMON_NUMBER

# Номер квартиры: «Кв. 12», «квартира №5», «Кв, 29», «Кв 58», «кв38», «Кв,, 29».
# После «кв» допускаем только буквы: \w* съедал цифры номера, и «кв38»
# превращалось в квартиру 8 — показания уходили не тому дому. Разделителей
# между «кв» и номером может быть сколько угодно: жители ставят по две
# запятые, точку с запятой, скобку.
APARTMENT_RE = re.compile(r"кв[а-яё]*[\s.,;:№()-]*(\d{1,4})", re.IGNORECASE)

# Слово «квартира» в тексте — чтобы отличить «номер не разобрали»
# от «номер вообще не указан»
APARTMENT_WORD_RE = re.compile(r"\bкв", re.IGNORECASE)
NONRESIDENTIAL_RE = re.compile(r"нежило\w*\s*(?:помещение)?\s*№?\s*(\d+)", re.IGNORECASE)

# Общедомовой прибор учёта: «Общедомовой», «ОДПУ», «общий прибор», «ОДН»
COMMON_RE = re.compile(r"общедом\w*|одпу|общ\w*\s+прибор|\bодн\b", re.IGNORECASE)

# Число в конце строки (допускаем ведущие нули и дробную часть).
# Знак не захватываем: тире/дефис в сообщениях жителей — это разделитель
# («Хвс кухня - 6»), а не минус; показания всегда неотрицательны.
VALUE_RE = re.compile(r"\d[\d\s]*(?:[.,]\d+)?\s*$")

# Обратный порядок: сначала показание, потом прибор — «11882 - Эл.эн».
# Подпись обязана начинаться с буквы, иначе это просто число.
LEADING_VALUE_RE = re.compile(
    r"^\s*(\d[\d\s]*(?:[.,]\d+)?)\s*[-–—:=.,]*\s*([а-яёa-z].*)$", re.IGNORECASE)

# Часть жителей пишет всё одной строкой: «кв38,Х/В30,Г/В 42,Эл/э 15873».
# Режем такую строку на приборы по запятой (или точке с запятой) — но только
# перед буквой, чтобы не порвать дробное число «56,78».
SEGMENT_RE = re.compile(r"[;,](?=\s*[а-яёa-z])", re.IGNORECASE)


def _normalize(label: str) -> str:
    """Убирает разделители, оставляя только буквы, для сопоставления по словарю."""
    return re.sub(r"[^а-яёa-z]", "", label.lower())


# Ключевые слова (по нормализованной подписи). Проверяются как вхождение.
ELECTRICITY_KW = ("электро", "элэн", "эленер", "элэнер", "эенер", "ээнер",
                  "ээн", "эенер", "эдектро", "свет", "св", "эл", "ээ")
GAS_KW = ("газ",)
# «Общ. ГВС» жители пишут как итог по горячей воде — наравне с «сумма»
TOTAL_KW = ("итог", "сумм", "сум", "общ")
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
    mentions_apartment: bool = False   # в тексте есть «кв», номер мог не читаться

    @property
    def is_empty(self) -> bool:
        return not self.values

    @property
    def apartment_unreadable(self) -> bool:
        """Квартиру назвали, но номер не разобрали — подставлять чужую нельзя."""
        return self.mentions_apartment and self.apartment_number is None


def parse_message(text: str) -> ParsedReadings:
    result = ParsedReadings()

    m = NONRESIDENTIAL_RE.search(text)
    if m:
        result.apartment_number = f"Нежилое помещение №{m.group(1)}"
    elif COMMON_RE.search(text):
        result.apartment_number = COMMON_NUMBER
    else:
        result.mentions_apartment = bool(APARTMENT_WORD_RE.search(text))
        m = APARTMENT_RE.search(text)
        if m:
            result.apartment_number = m.group(1)

    context: str | None = None  # 'cold' | 'hot' — тип воды из предыдущих строк

    # Пара «подпись — показание» бывает разорвана: запятой («Сумма» + «гв,292»,
    # «1234» + «Эл.эн») или переводом строки — жители пишут подпись на одной
    # строке, а число на следующей. Держим половинку до её пары.
    pending_label = ""
    pending_value = ""

    for raw_line in text.splitlines():
        for segment in SEGMENT_RE.split(raw_line):
            line = segment.strip()
            if not line:
                continue

            value_match = VALUE_RE.search(line)
            reversed_match = None if value_match else LEADING_VALUE_RE.match(line)
            if value_match:
                raw_value, label_part = value_match.group(), line[: value_match.start()]
            elif reversed_match:
                raw_value, label_part = reversed_match.group(1), reversed_match.group(2)
            else:
                raw_value, label_part = "", line

            own_label = _normalize(label_part)
            # Строка с номером квартиры — не показание. Проверяем по её
            # собственной подписи, чтобы заодно сбросить всё недособранное.
            if own_label in ("кв", "квартира", "кварт"):
                pending_label = pending_value = ""
                continue

            label = pending_label + own_label

            if not raw_value:
                if pending_value and label:
                    raw_value, pending_value = pending_value, ""
                else:
                    pending_label = label       # подпись без числа — ждём число
                    continue
            elif not label:
                pending_value = raw_value       # число без подписи — ждём подпись
                continue

            pending_label = ""
            value = parse_value(raw_value)

            kind, context = _classify(label, context)
            if kind is None:
                continue
            if kind == "gas":
                result.ignored.append(f"газ ({raw_value.strip()})")
                continue
            if value is None:
                result.errors.append(
                    f"Не удалось разобрать число в строке: «{line}»")
                continue
            if kind in result.values:
                result.errors.append(
                    f"Прибор «{label_part.strip()}» указан дважды")
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

    # Одна буква вместо «хвс»/«гвс»: «Х. Кух», «Г. Ван». Саму по себе букву
    # в словарь не добавить — она встретится в любом слове, поэтому
    # засчитываем её только рядом с местом установки прибора.
    if not is_cold and not is_hot and (is_kitchen or is_bathroom):
        if label.startswith("х"):
            is_cold = True
        elif label.startswith("г"):
            is_hot = True

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
