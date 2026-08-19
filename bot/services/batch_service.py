"""Разбор пачки сообщений: несколько квартир одним текстом.

Часть жителей пишет показания в чат WhatsApp, и председатель переносит их
в систему. Копировать по одному сообщению — долго, поэтому бот принимает
вставленный кусок переписки целиком: делит его на сообщения по строке
с номером квартиры и разносит каждое.

Ответ — одна сводка на всю пачку: отдельная квитанция на каждую из тридцати
квартир только мешала бы.
"""
import sqlite3
from dataclasses import dataclass, field

from bot.services.parser import parse_message
from bot.services.reading_service import current_period, save_parsed_readings
from database import repository


@dataclass
class BatchResult:
    messages: int = 0
    saved: int = 0
    lines: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def text(self) -> str:
        report = (f"📥 <b>Разобрано сообщений: {self.messages}</b>\n"
                  f"Записано показаний: {self.saved}\n\n"
                  + "\n".join(self.lines))
        if self.problems:
            report += "\n\n⚠️ <b>Требуют внимания:</b>\n" + "\n".join(
                f"• {p}" for p in self.problems)
        return report


def import_batch(conn: sqlite3.Connection, blocks: list[str],
                 user_id: int | None = None, tg_id: int | None = None,
                 source: str = "admin") -> BatchResult:
    """Записывает показания из каждого сообщения пачки."""
    result = BatchResult(messages=len(blocks))

    for block in blocks:
        parsed = parse_message(block)
        apartment = (repository.get_apartment_by_number(
            conn, parsed.apartment_number) if parsed.apartment_number else None)

        if apartment is None:
            head = block.splitlines()[0][:40]
            result.lines.append(f"❌ «{head}» — помещение не найдено")
            continue
        if parsed.is_empty:
            result.lines.append(f"❌ {short_name(apartment)} — "
                                "не разобрал показания")
            continue

        outcome = save_parsed_readings(conn, apartment, parsed, user_id,
                                       source=source)
        result.saved += len(outcome.saved)
        mark = "✅" if outcome.anything_saved and not outcome.errors else "⚠️"
        result.lines.append(f"{mark} {short_name(apartment)} — "
                            f"{readings_word(len(outcome.saved))}")
        result.problems += [f"{short_name(apartment)}: {p}"
                            for p in list(outcome.errors) + list(outcome.warnings)]

    repository.log_event(conn, tg_id, "reading_batch",
                         f"пачкой: {result.messages} сообщений, "
                         f"{result.saved} показаний за {current_period()}")
    return result


def short_name(apartment: sqlite3.Row) -> str:
    """«кв. 5» или короткое имя помещения — для строки отчёта."""
    if apartment["type"] == "residential":
        return f"кв. {apartment['number']}"
    return apartment["number"].replace("Нежилое помещение ", "Нежилое ")


def readings_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return f"{count} показание"
    if count % 10 in (2, 3, 4) and count % 100 not in (12, 13, 14):
        return f"{count} показания"
    return f"{count} показаний"
