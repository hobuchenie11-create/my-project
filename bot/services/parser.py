"""Разбор показаний из свободного текста (сообщения в общем чате).

Ожидаемый формат сообщения:

    Кв. 12
    Свет: 15230
    ХВС кухня: 123,45
    ХВС санузел: 89.1
    ГВС кухня: 44.2
    ГВС ванна: 51.0

Название прибора допускается в разных вариантах (см. KIND_ALIASES).
"""
import re
from dataclasses import dataclass, field

from bot.services.validation import parse_value

# Варианты написания -> вид прибора. Проверяются по порядку,
# более конкретные (двухсловные) должны идти раньше коротких.
KIND_ALIASES: list[tuple[str, str]] = [
    (r"хвс\s*кухн\w*", "cws_kitchen"),
    (r"хвс\s*(сан\.?\s*узел|санузел|ванн\w*|туалет)", "cws_bathroom"),
    (r"гвс\s*кухн\w*", "hws_kitchen"),
    (r"гвс\s*(сан\.?\s*узел|санузел|ванн\w*)", "hws_bathroom"),
    (r"(электро\w*|свет|эл\.?\s*энерг\w*|^э\b)", "electricity"),
    (r"хвс|холодн\w*", "cws"),
    (r"гвс|горяч\w*", "hws"),
]

APARTMENT_RE = re.compile(r"(?:кв\.?|квартира)\s*№?\s*(\d+)", re.IGNORECASE)
NONRESIDENTIAL_RE = re.compile(r"нежило\w*\s*(?:помещение)?\s*№?\s*(\d+)", re.IGNORECASE)
VALUE_RE = re.compile(r"[-+]?\d[\d\s]*(?:[.,]\d+)?\s*$")


@dataclass
class ParsedReadings:
    apartment_number: str | None = None
    values: dict[str, float] = field(default_factory=dict)
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

    for line in text.splitlines():
        line = line.strip()
        if not line or APARTMENT_RE.fullmatch(line):
            continue
        value_match = VALUE_RE.search(line)
        if not value_match:
            continue
        label = line[: value_match.start()].strip(" :=-—\t").lower()
        if not label:
            continue
        kind = _match_kind(label)
        if kind is None:
            continue
        value = parse_value(value_match.group())
        if value is None:
            result.errors.append(f"Не удалось разобрать число в строке: «{line}»")
            continue
        if kind in result.values:
            result.errors.append(f"Прибор «{label}» указан дважды")
            continue
        result.values[kind] = value

    return result


def _match_kind(label: str) -> str | None:
    for pattern, kind in KIND_ALIASES:
        if re.search(pattern, label, re.IGNORECASE):
            return kind
    return None
