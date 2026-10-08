"""Приложение № 1 к письму в Омск РТС: перечень квартир таблицей.

Письмо читают по приложению: перечень отвечает на вопрос «какие квартиры и
что с ними», приложение № 2 (scripts/attachments.py) — «чем это
подтверждается». Поэтому порядок квартир в обоих документах одинаковый.

Запуск (нужны python-docx и reportlab):

    python -m scripts.appendix_list --out Приложение1.docx --pdf Приложение1.pdf
"""
from __future__ import annotations

import argparse
from pathlib import Path

HEAD = ["№", "Кв.", "Прибор учёта ГВС,\nместо установки", "Заводской №",
        "Документ о поверке (приёмке)", "Поверка\nдо",
        "Отметка в базе\nАО «ОмскВодоканал»"]

# Данные взяты из документов жителей и выписок АО «ОмскВодоканал».
# Ничего не додумано: чего в документах нет, оставлено прочерком.
ROWS = [
    ("24", "кухня", "250335153",
     "Акт обследования АО «Омск РТС» от 18.06.2026", "06.01.2032",
     "числится, показание 0 (17.09.2026)"),
    ("24", "ванная", "51727507",
     "Акт обследования АО «Омск РТС» от 18.06.2026", "03.01.2029",
     "числится, показание 58 (17.09.2026)"),
    # По кв. 29 акта у собственника нет. Прочерк в графе «документ» вызывает
    # у читателя ровно один вопрос — поэтому прямо пишем, чем подтверждаем
    ("29", "кухня", "С293574411",
     "Акт не представлен; подтверждение — выписка АО «ОмскВодоканал»",
     "23.03.2028", "числится, показание 115 (20.09.2026)"),
    ("29", "ванная", "С293923811",
     "Акт не представлен; подтверждение — фотография прибора учёта "
     "и выписка АО «ОмскВодоканал»",
     "23.03.2028", "числится, показание 179 (20.09.2026)"),
    ("50", "санузел", "63410979",
     "Акт приёмки АО «Омск РТС» от 03.03.2026 "
     "(снят зав. № 0052988, показание 889)", "02.01.2032",
     "числится, показание 1 (03.10.2026)"),
    ("80", "кухня", "22686427",
     "Акт поверочных работ ООО «ПКФ «СЧЁТ» от 30.01.2025", "29.01.2029",
     "числится, показание 317 (17.09.2026)"),
    ("80", "санузел", "22686544",
     "Акт поверочных работ ООО «ПКФ «СЧЁТ» от 30.01.2025", "29.01.2029",
     "числится, показание 1252 (17.09.2026)"),
]

TITLE = "Перечень квартир"
SUBTITLE = ("многоквартирный дом по адресу: г. Омск, ул. Магистральная, д. 2 — "
            "приборы учёта горячей воды, сведения по которым требуют сверки "
            "с базой начислений АО «Омск РТС»")
FOOT = ("Документы, подтверждающие сведения настоящего перечня (копии актов, "
        "фотографии приборов учёта с заводскими номерами и показаниями, "
        "выписки АО «ОмскВодоканал»), приведены в приложении № 2 — по одной "
        "странице на каждую квартиру.")

WIDTHS = [0.9, 1.2, 2.6, 2.6, 6.2, 2.0, 4.0]      # см, сумма 19,5 — альбомная


def build_docx(out: Path) -> Path:
    from docx import Document
    from docx.enum.section import WD_ORIENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Cm, Pt

    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width, section.page_height = Cm(29.7), Cm(21)
    for side in ("top", "bottom", "left", "right"):
        setattr(section, f"{side}_margin", Cm(1.5))

    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(10)

    head = doc.add_paragraph()
    head.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = head.add_run("Приложение № 1 к письму "
                       "от «____» ____________ 2026 г.")
    run.italic = True
    run.font.size = Pt(9)

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run(TITLE)
    run.bold = True
    run.font.size = Pt(13)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(SUBTITLE)
    run.font.size = Pt(9)

    table = doc.add_table(rows=1, cols=len(HEAD))
    table.style = "Table Grid"
    for cell, text, width in zip(table.rows[0].cells, HEAD, WIDTHS):
        cell.width = Cm(width)
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run(text.replace("\n", " "))
        run.bold = True
        run.font.size = Pt(9)

    for index, row in enumerate(ROWS, start=1):
        cells = table.add_row().cells
        for cell, text, width in zip(cells, (str(index), *row), WIDTHS):
            cell.width = Cm(width)
            para = cell.paragraphs[0]
            para.add_run(text).font.size = Pt(9)

    foot = doc.add_paragraph()
    foot.paragraph_format.space_before = Pt(10)
    run = foot.add_run(FOOT)
    run.font.size = Pt(9)
    run.italic = True

    out.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out)
    return out


def build_pdf(out: Path) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                    Table, TableStyle)

    from scripts.attachments import _register_fonts

    font, bold = _register_fonts(pdfmetrics, TTFont)
    body = ParagraphStyle("body", fontName=font, fontSize=8.5, leading=10.5)
    head = ParagraphStyle("head", parent=body, fontName=bold,
                          alignment=1)
    title = ParagraphStyle("title", fontName=bold, fontSize=13, alignment=1,
                           spaceAfter=4)
    sub = ParagraphStyle("sub", fontName=font, fontSize=9, alignment=1,
                         spaceAfter=10, leading=11)
    note = ParagraphStyle("note", parent=body, fontSize=8)

    out.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(out), pagesize=landscape(A4),
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    data = [[Paragraph(text, head) for text in HEAD]]
    for index, row in enumerate(ROWS, start=1):
        data.append([Paragraph(text, body) for text in (str(index), *row)])

    table = Table(data, colWidths=[w * cm for w in WIDTHS], repeatRows=1)
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.93, 0.93, 0.93)),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    doc.build([
        Paragraph("Приложение № 1 к письму от «____» ____________ 2026 г.",
                  ParagraphStyle("hdr", fontName=font, fontSize=8,
                                 alignment=2, spaceAfter=8)),
        Paragraph(TITLE, title),
        Paragraph(SUBTITLE, sub),
        table,
        Spacer(1, 10),
        Paragraph(FOOT, note),
    ])
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="Приложение1.docx")
    parser.add_argument("--pdf", default="Приложение1.pdf")
    args = parser.parse_args()
    print(f"Готово: {build_docx(Path(args.out))}")
    print(f"Готово: {build_pdf(Path(args.pdf))}")


if __name__ == "__main__":
    main()
