"""Столбцы готового реестра ОЭК — в консоль или сразу в буфер обмена.

Ресурсник может прислать свою книгу или попросить данные в другом файле.
Перебивать 77 строк руками не нужно: команда достаёт из собранного реестра
показания и дату снятия — в том же порядке строк, в каком они лежат в файле.

    python -m reports.oek_columns                # текущий период, в консоль
    python -m reports.oek_columns 2026-08        # за период
    python -m reports.oek_columns --clip         # сразу в буфер обмена
    python -m reports.oek_columns --paste --clip # блок для вставки одним махом

Два вида вывода:
  • обычный — «Квартира | Показания | Дата», с заголовком: для проверки
    глазами и для переноса в произвольную таблицу;
  • --paste — только колонки от «текущих показаний» до «даты снятия», без
    заголовка и без номеров квартир. Встаньте в целевом файле на первую
    ячейку колонки показаний и вставьте: колонки лягут одна в одну, включая
    пустые между ними (ночь и полупик).
"""
import sys
from pathlib import Path

from bot.config import config
from bot.services.reading_service import current_period, period_title
from excel.oek_registry import DATE_FORMAT, FilledRow, read_filled
from reports.oek_registry import OUT_PREFIX

HEADER = ("Квартира", "Показания", "Дата снятия")


def find_registry(period: str) -> Path | None:
    """Собранный реестр за период: основной файл или самый свежий запасной.

    Запасной появляется, когда основной был открыт в Excel — см.
    reports/oek_registry.py.
    """
    if not config.reports_dir.exists():
        return None
    files = [p for p in config.reports_dir.iterdir()
             if p.is_file() and p.name.startswith(f"{OUT_PREFIX}{period}")
             and p.suffix.lower() in (".xls", ".xlsx", ".xlsm")]
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def _reading(row: FilledRow) -> str:
    if row.reading is None:
        return ""
    value = round(float(row.reading), 3)
    return str(int(value) if value == int(value) else value)


def _date(row: FilledRow) -> str:
    return row.taken_on.strftime("%d.%m.%Y") if row.taken_on else ""


def as_table(rows: list[FilledRow]) -> str:
    """Квартира, показания, дата — через табуляцию: вставляется в любой Excel."""
    lines = ["\t".join(HEADER)]
    lines += ["\t".join((row.apartment, _reading(row), _date(row)))
              for row in rows]
    return "\n".join(lines)


def as_paste_block(rows: list[FilledRow], width: int) -> str:
    """Колонки от показаний до даты — как они лежат в реестре, с пустыми внутри.

    Между «текущими показаниями» и «датой снятия» у ОЭК стоят ночь и полупик:
    их отдаём пустыми, иначе при вставке колонки сдвинутся.
    """
    lines = []
    for row in rows:
        cells = [""] * width
        cells[0] = _reading(row)
        cells[-1] = _date(row)
        lines.append("\t".join(cells))
    return "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    """Кладёт текст в буфер обмена Windows. False — не получилось."""
    import platform

    if platform.system() != "Windows":
        return False

    import ctypes
    from ctypes import wintypes

    CF_UNICODETEXT, GMEM_MOVEABLE = 13, 0x0002
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]

    # Excel ждёт строки, разделённые CRLF, иначе вставит всё в одну ячейку
    buffer = ctypes.create_unicode_buffer(text.replace("\n", "\r\n"))
    size = ctypes.sizeof(buffer)
    handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    if not handle:
        return False
    ctypes.memmove(kernel32.GlobalLock(handle), buffer, size)
    kernel32.GlobalUnlock(handle)

    if not user32.OpenClipboard(None):
        kernel32.GlobalFree(handle)
        return False
    try:
        user32.EmptyClipboard()
        # Удалось — память забирает система, освобождать её нам уже нельзя
        return bool(user32.SetClipboardData(CF_UNICODETEXT, handle))
    finally:
        user32.CloseClipboard()


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    period = args[0] if args else current_period()

    path = find_registry(period)
    if path is None:
        print(f"Реестр за {period_title(period)} ещё не собран. "
              f"Соберите его: python -m reports.oek_registry {period}")
        return 1

    rows, layout = read_filled(path)
    if "--paste" in flags:
        width = ((layout.date_col - layout.reading_col + 1)
                 if layout.date_col is not None else 1)
        text = as_paste_block(rows, width)
    else:
        text = as_table(rows)

    filled = sum(1 for row in rows if row.reading is not None)
    print(f"Реестр: {path.name}")
    print(f"Строк: {len(rows)}, с показаниями: {filled}")
    print(f"Дата снятия: в формате {DATE_FORMAT}\n")

    if "--clip" in flags:
        if copy_to_clipboard(text):
            print("Скопировано в буфер обмена — вставляйте в нужный файл.")
            return 0
        print("Не удалось положить в буфер обмена, вывожу текстом:\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
