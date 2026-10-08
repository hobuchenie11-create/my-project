"""Сборка приложения к письму: одна квартира — одна страница.

Сотрудник ресурсника разбирает письмо глазами: если акт, фотографии прибора
и скриншот из реестра лежат вперемешку, он сопоставляет их по заводским
номерам и бросает это занятие на третьей квартире. Поэтому документы
складываются по квартирам: страница — квартира, сверху номер, под каждым
снимком подпись, что это.

Запуск (нужны pillow и python-docx, в требованиях бота их нет — скрипт
разовый, запускается руками):

    python -m scripts.attachments --out Приложение2.docx

Состав приложения описан в FLATS: путь к файлу, подпись и роль. Роль
решает, какого размера снимок на странице: акт нужно читать, фотографию
прибора — разглядывать, скриншот обычно узкий и широкий.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt
from PIL import Image

# Поля страницы и то, что остаётся под содержимое (А4: 21 × 29,7 см)
PAGE_W, PAGE_H = Cm(21), Cm(29.7)
MARGIN = Cm(1.5)
USABLE_W = 21 - 1.5 * 2          # см
USABLE_H = 29.7 - 1.5 * 2

# Ширина снимка в сантиметрах по его роли на странице
WIDTH = {
    "act": 13.0,          # акт читают — он самый крупный
    "meter": 5.6,         # приборы идут в ряд по двое-трое
    "screen": 17.0,       # скриншот реестра: широкий и низкий
}


@dataclass
class Item:
    path: str
    caption: str
    role: str = "meter"
    rotate: int = 0       # градусы против часовой; 90 — лежащий на боку акт


@dataclass
class Flat:
    number: str
    note: str = ""
    items: list[Item] = field(default_factory=list)


def _prepared(item: Item, work: Path) -> Path:
    """Снимок в нужном повороте. Боком снятый акт на странице не читается."""
    source = Path(item.path)
    if not item.rotate:
        return source

    work.mkdir(parents=True, exist_ok=True)
    target = work / f"{source.stem}-rot{item.rotate}{source.suffix}"
    if not target.exists():
        with Image.open(source) as image:
            image.rotate(item.rotate, expand=True).save(target, quality=92)
    return target


def _size(path: Path, width_cm: float) -> tuple[float, float]:
    with Image.open(path) as image:
        w, h = image.size
    return width_cm, width_cm * h / w


def _caption(doc, text: str) -> None:
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(8)
    run = para.add_run(text)
    run.italic = True
    run.font.size = Pt(9)


def _picture_row(doc, items: list[tuple[Path, Item, float]]) -> None:
    """Снимки в один ряд: таблица без рамок, под каждым — подпись."""
    table = doc.add_table(rows=2, cols=len(items))
    table.autofit = False
    for index, (path, item, width_cm) in enumerate(items):
        cell = table.cell(0, index)
        cell.width = Cm(width_cm + 0.4)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.add_run().add_picture(str(path), width=Cm(width_cm))

        cell = table.cell(1, index)
        cell.width = Cm(width_cm + 0.4)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(10)
        run = para.add_run(item.caption)
        run.italic = True
        run.font.size = Pt(9)


def build(flats: list[Flat], out: Path, work: Path,
          letter_date: str = "«____» ____________ 2026 г.") -> Path:
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = PAGE_W, PAGE_H
    for side in ("top", "bottom", "left", "right"):
        setattr(section, f"{side}_margin", MARGIN)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)

    for position, flat in enumerate(flats):
        if position:
            doc.add_section(WD_SECTION.NEW_PAGE)
            section = doc.sections[-1]
            section.page_width, section.page_height = PAGE_W, PAGE_H
            for side in ("top", "bottom", "left", "right"):
                setattr(section, f"{side}_margin", MARGIN)

        head = doc.add_paragraph()
        head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        head.paragraph_format.space_after = Pt(0)
        run = head.add_run(f"Приложение № 2 к письму от {letter_date}")
        run.italic = True
        run.font.size = Pt(9)

        title = doc.add_paragraph()
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.paragraph_format.space_after = Pt(6)
        run = title.add_run(f"Квартира № {flat.number}")
        run.bold = True
        run.font.size = Pt(14)

        if flat.note:
            note = doc.add_paragraph()
            note.alignment = WD_ALIGN_PARAGRAPH.CENTER
            note.paragraph_format.space_after = Pt(8)
            run = note.add_run(flat.note)
            run.font.size = Pt(10)

        # Снимки одной роли идут одним рядом: акт сам по себе, приборы — вместе
        row: list[tuple[Path, Item, float]] = []
        current_role = None
        for item in flat.items:
            path = _prepared(item, work)
            width_cm = WIDTH.get(item.role, WIDTH["meter"])
            if item.role != current_role and row:
                _picture_row(doc, row)
                row = []
            current_role = item.role
            row.append((path, item, width_cm))
            if item.role != "meter":          # акт и скриншот — по одному в ряд
                _picture_row(doc, row)
                row = []
                current_role = None
        if row:
            _picture_row(doc, row)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return out


# ---------------------------------------------------------------------------
# Состав приложения. Файлы жителей лежат вне репозитория — в переписке
# председателя; путь задаётся при запуске через --images.
# ---------------------------------------------------------------------------

def flats_for(images: Path) -> list[Flat]:
    return [
        Flat(
            number="24",
            note="Акт обследования приборов учёта ГВС от 18.06.2026 "
                 "(АО «Омск РТС», отдел продаж САО)",
            items=[
                Item(str(images / "1.jpg"),
                     "Акт обследования приборов учёта горячей воды "
                     "от 18.06.2026", role="act", rotate=-90),
                Item(str(images / "3.jpg"),
                     "ИПУ ГВС, кухня, зав. № 250335153, "
                     "поверка до 06.01.2032"),
                Item(str(images / "2.jpg"),
                     "ИПУ ГВС, ванная, зав. № 51727507, "
                     "поверка до 03.01.2029"),
                Item(str(images / "4.png"),
                     "Сведения по кв. 24 в общедомовом реестре приборов учёта",
                     role="screen"),
            ],
        ),
        Flat(
            number="29",
            items=[
                Item(str(images / "5.jpg"),
                     "ИПУ ГВС, ванная, зав. № С293923811, показание 179, "
                     "поверка до 23.03.2028"),
            ],
        ),
    ]


def build_pdf(flats: list[Flat], out: Path, work: Path,
              letter_date: str = "«____» ____________ 2026 г.") -> Path:
    """Тот же состав, но PDF: его отправляют письмом, и он никуда не поедет.

    В Word страница зависит от шрифтов и настроек на чужом компьютере —
    снимок может переползти на следующую. Для вложения в письмо это важнее
    возможности править подписи, поэтому собираем оба файла.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfgen import canvas

    font, bold = _register_fonts(pdfmetrics, TTFont)
    cm = 28.3464567
    page_w, page_h = A4
    margin = 1.5 * cm
    usable_w = page_w - 2 * margin

    out.parent.mkdir(parents=True, exist_ok=True)
    pdf = canvas.Canvas(str(out), pagesize=A4)

    for flat in flats:
        y = page_h - margin

        pdf.setFont(font, 8)
        pdf.drawRightString(page_w - margin, y - 8,
                            f"Приложение № 2 к письму от {letter_date}")
        y -= 20

        pdf.setFont(bold, 14)
        pdf.drawCentredString(page_w / 2, y - 14, f"Квартира № {flat.number}")
        y -= 26

        if flat.note:
            pdf.setFont(font, 9)
            for line in _wrap(flat.note, 95):
                pdf.drawCentredString(page_w / 2, y - 9, line)
                y -= 12
        y -= 6

        row: list[tuple[Path, Item, float]] = []
        current_role = None

        def flush(row, y):
            if not row:
                return y
            widths = [w * cm for _, _, w in row]
            gap = 0.6 * cm
            total = sum(widths) + gap * (len(row) - 1)
            x = margin + (usable_w - total) / 2
            height = 0
            for (path, item, width_cm), width in zip(row, widths):
                image = ImageReader(str(path))
                iw, ih = image.getSize()
                h = width * ih / iw
                pdf.drawImage(image, x, y - h, width=width, height=h)
                height = max(height, h)
                x += width + gap
            y -= height + 4

            x = margin + (usable_w - total) / 2
            pdf.setFont(font, 8)
            lowest = y
            for (path, item, width_cm), width in zip(row, widths):
                text_y = y
                for line in _wrap(item.caption, max(18, int(width / 4.6))):
                    pdf.drawCentredString(x + width / 2, text_y - 8, line)
                    text_y -= 10
                lowest = min(lowest, text_y)
                x += width + gap
            return lowest - 8

        for item in flat.items:
            path = _prepared(item, work)
            width_cm = WIDTH.get(item.role, WIDTH["meter"])
            if item.role != current_role and row:
                y = flush(row, y)
                row = []
            current_role = item.role
            row.append((path, item, width_cm))
            if item.role != "meter":
                y = flush(row, y)
                row = []
                current_role = None
        if row:
            y = flush(row, y)

        pdf.showPage()

    pdf.save()
    return out


def _register_fonts(pdfmetrics, TTFont) -> tuple[str, str]:
    """Кириллица во встроенных шрифтах reportlab не живёт — берём системный."""
    candidates = [
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("LiberationSerif", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
         "LiberationSerif-Bold", "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"),
    ]
    for name, path, bold_name, bold_path in candidates:
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))
            pdfmetrics.registerFont(TTFont(bold_name, bold_path))
            return name, bold_name
    return "Helvetica", "Helvetica-Bold"


def _wrap(text: str, limit: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > limit and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", default="images",
                        help="папка со снимками от жителей")
    parser.add_argument("--out", default="Приложение2.docx")
    parser.add_argument("--pdf", default="Приложение2.pdf")
    parser.add_argument("--work", default="work",
                        help="куда класть повёрнутые копии снимков")
    args = parser.parse_args()

    images = Path(args.images)
    flats = flats_for(images)
    print(f"Готово: {build(flats, Path(args.out), Path(args.work))}")
    print(f"Готово: {build_pdf(flats, Path(args.pdf), Path(args.work))}")


if __name__ == "__main__":
    main()
