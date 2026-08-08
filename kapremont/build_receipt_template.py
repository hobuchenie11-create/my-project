# -*- coding: utf-8 -*-
"""
Генератор шаблона квитанции на взнос за капитальный ремонт
(специальный счёт МКД, владелец счёта — Региональный фонд капитального
ремонта многоквартирных домов Омской области).

Формирует книгу output/Квитанция_КапРемонт_Омск_шаблон.xlsx:

    КВИТАНЦИЯ   — печатная форма А4 (по умолчанию — чёрно-белая),
                  все значения подтягиваются формулами по лицевому счёту;
    ДАННЫЕ      — лист-приёмник разноски (начислено / долг / к оплате и пр.);
    НАСТРОЙКИ   — реквизиты специального счёта и параметры периода;
    СХЕМА       — таблица соответствия «диапазон → цвета ЧБ / ЦВЕТ»,
                  по ней макрос перекрашивает бланк перед печатью и перед
                  выгрузкой в PDF;
    ИНСТРУКЦИЯ  — порядок интеграции в существующую книгу с макросом.

Запуск:  python3 build_receipt_template.py
"""

import argparse
import datetime as dt
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

OUTDIR = Path(__file__).resolve().parent / "output"

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument(
    "--scheme", choices=["ЧБ", "ЦВЕТ"], default="ЧБ",
    help="Схема, в которой сохранить книгу. ЧБ — рабочий шаблон для печати; "
         "ЦВЕТ — предпросмотр того, что увидит житель в PDF.")
ARGS = _parser.parse_args()
SCHEME_COL = 0 if ARGS.scheme == "ЧБ" else 1
OUT = OUTDIR / ("Квитанция_КапРемонт_Омск_шаблон.xlsx" if SCHEME_COL == 0
              else "Предпросмотр_цветной.xlsx")

SHEET = "КВИТАНЦИЯ"
DATA = "ДАННЫЕ"
CFG = "НАСТРОЙКИ"
SCHEME = "СХЕМА"
HELP = "ИНСТРУКЦИЯ"

FONT = "Arial"

# Генератора QR-кодов в Excel нет, а сторонний пока не подключён. Пока флаг
# снят, место под QR остаётся пустой зарезервированной рамкой, а в разделе
# «Порядок оплаты» третий пункт — пустая строка под будущее напоминание.
# Поставить True — вернутся и заголовок «QR-КОД ДЛЯ ОПЛАТЫ», и текст пункта.
QR_ВКЛЮЧЁН = False

# --------------------------------------------------------------------------
# Две цветовые схемы одного и того же бланка.
# ЧБ   — то, что уходит на бумагу (принтер А4, чёрно-белый лазерник).
# ЦВЕТ — то, что уходит жителю в PDF по электронной почте.
# Роли используются и здесь, и в листе СХЕМА, который читает макрос.
# --------------------------------------------------------------------------
# В ЧБ-схеме заливок нет вообще: сплошные фоны съедают тонер, а на дом их
# уходит по листу на квартиру. Структуру держат рамки, акценты — кегль
# и полужирный. Цветная схема (только для PDF) заливки сохраняет.
PALETTE = {
    # роль        ЧБ(заливка, шрифт)        ЦВЕТ(заливка, шрифт)
    "title":     (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "subtitle":  (("FFFFFF", "000000"), ("DDEFF0", "0F6B70")),
    "section":   (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "thead":     (("FFFFFF", "000000"), ("263238", "FFFFFF")),
    "label":     (("FFFFFF", "000000"), ("F3F5F5", "263238")),
    "value":     (("FFFFFF", "000000"), ("FFFFFF", "263238")),
    "input":     (("FFFFFF", "000000"), ("E8F3F3", "0F6B70")),
    "total":     (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "totalsum":  (("FFFFFF", "000000"), ("E8F3F3", "0F6B70")),
    "note":      (("FFFFFF", "000000"), ("E8F3F3", "263238")),
    "qr":        (("FFFFFF", "000000"), ("F3F5F5", "0F6B70")),
    "plain":     (("FFFFFF", "000000"), ("FFFFFF", "263238")),
}

# Здесь копятся диапазоны каждой роли — из этого собирается лист СХЕМА.
ROLE_RANGES = {role: [] for role in PALETTE}

THIN = Side(style="thin", color="000000")
MEDIUM = Side(style="medium", color="000000")

BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BOX_MED = Border(left=MEDIUM, right=MEDIUM, top=MEDIUM, bottom=MEDIUM)

MONEY = '#,##0.00'
AREA = '#,##0.0'
RATE = '#,##0.00'
DATEFMT = 'DD.MM.YYYY'


# --------------------------------------------------------------------------
# Вспомогательные функции
# --------------------------------------------------------------------------
def put(ws, ref, value=None, *, role="plain", size=9, bold=False, italic=False,
        align="left", valign="center", wrap=False, fmt=None, border=BOX,
        indent=0):
    """Записать значение в ячейку/объединённый диапазон и оформить его."""
    if ":" in ref:
        ws.merge_cells(ref)
        first = ref.split(":")[0]
    else:
        first = ref

    cell = ws[first]
    if value is not None:
        cell.value = value

    fill_hex, font_hex = PALETTE[role][SCHEME_COL]
    ROLE_RANGES[role].append(ref)

    font = Font(name=FONT, size=size, bold=bold, italic=italic, color=font_hex)
    fill = PatternFill("solid", fgColor=fill_hex)
    alignment = Alignment(horizontal=align, vertical=valign, wrap_text=wrap,
                          indent=indent)

    block = ws[ref] if ":" in ref else ((cell,),)
    for row in block:
        for c in row:
            c.font = font
            c.fill = fill
            c.alignment = alignment
            if border is not None:
                c.border = border
            if fmt:
                c.number_format = fmt
    return cell


def spacer(ws, row, height=5.0):
    ws.row_dimensions[row].height = height


def outline(ws, ref, side=MEDIUM):
    """Обвести прямоугольный диапазон рамкой, не трогая внутренние линии."""
    rows = list(ws[ref])
    last_r = len(rows) - 1
    for ri, row in enumerate(rows):
        last_c = len(row) - 1
        for ci, cell in enumerate(row):
            b = cell.border
            cell.border = Border(
                left=side if ci == 0 else b.left,
                right=side if ci == last_c else b.right,
                top=side if ri == 0 else b.top,
                bottom=side if ri == last_r else b.bottom,
            )


def edge(ws, ref, top=None, bottom=None):
    """Усилить горизонтальные границы полосы.

    Без заливок именно линии отделяют заголовок раздела от его содержимого,
    поэтому заголовки подчёркиваются жирной чертой.
    """
    for row in ws[ref]:
        for c in row:
            b = c.border
            c.border = Border(left=b.left, right=b.right,
                              top=top or b.top, bottom=bottom or b.bottom)


def d(col_letter):
    """Ссылка на строку разноски, найденную по лицевому счёту."""
    return (f"INDEX({DATA}!{col_letter}:{col_letter},"
            f"MATCH(КВ_ЛС,{DATA}!$A:$A,0))")


def lookup(col_letter, empty='""'):
    """То же, но с подавлением ошибки, если лицевой счёт не найден."""
    return f'IFERROR({d(col_letter)},{empty})'


def rich(*parts, role="value", size=9):
    """Строка, в которой часть слов набрана полужирным или другим кеглем.

    Цвет прогонов берётся из текущей схемы. Макрос ПрименитьСхему красит
    ячейку целиком, поэтому при переключении ЧБ/ЦВЕТ полужирность и размер
    сохраняются, а цвет выравнивается по всей строке.

    parts: кортежи ("текст", жирный) или ("текст", жирный, кегль).
    """
    color = PALETTE[role][SCHEME_COL][1]
    blocks = []
    for part in parts:
        text, bold = part[0], part[1]
        sz = part[2] if len(part) > 2 else size
        blocks.append(TextBlock(
            InlineFont(rFont=FONT, sz=sz, b=bold, color=color), text))
    return CellRichText(*blocks)


def ru_date(expr):
    """Дата в виде ДД.ММ.ГГГГ.

    Через TEXT(...,"ДД.ММ.ГГГГ") делать нельзя: коды формата в TEXT
    зависят от языка Excel и ломаются при переносе файла. TEXT(n,"00")
    и YEAR() работают одинаково в любой локали.
    """
    return (f'TEXT(DAY({expr}),"00")&"."&TEXT(MONTH({expr}),"00")&"."'
            f'&YEAR({expr})')


# ==========================================================================
# Книга
# ==========================================================================
wb = Workbook()

# --------------------------------------------------------------------------
# Лист НАСТРОЙКИ — единственное место, где правятся реквизиты
# --------------------------------------------------------------------------
cfg = wb.active
cfg.title = CFG

CFG_ROWS = [
    ("Получатель платежа",
     "РЕГИОНАЛЬНЫЙ ФОНД КАПИТАЛЬНОГО РЕМОНТА МНОГОКВАРТИРНЫХ ДОМОВ "
     "ОМСКОЙ ОБЛАСТИ (СПЕЦ. СЧЕТ)",
     "Владелец специального счёта МКД", None),
    ("Юридический адрес", "644099, г. Омск, ул. Краснофлотская, 24",
     "Из образца", None),
    ("ИНН", "5503239348", "Из образца", None),
    ("КПП", "550301001", "Из образца", None),
    ("ОГРН", "1027700342890", "Из образца", None),
    ("Расчётный счёт (спец. счёт МКД)", "40604810809000000154",
     "Специальный счёт дома по ул. Магистральная, 2", None),
    ("Банк", "Омский РФ АО «Россельхозбанк»", "Из образца", None),
    ("Корреспондентский счёт", "30101810900000000822", "Из образца", None),
    ("БИК", "045209822", "Из образца", None),
    ("ИНН/КПП банка", "7725114488 / 550502001", "Из образца", None),
    ("Адрес МКД", "г. Омск, ул. Магистральная, 2", "Из образца", None),
    ("Контактный телефон", "8 908 108 02 00", "Председатель совета дома", None),
    ("Расчётный период (текст)", "Июль 2026",
     "Подставляется в заголовок и в назначение платежа", None),
    ("Дата начала периода", dt.datetime(2026, 7, 1),
     "Первое число расчётного месяца", DATEFMT),
    ("День срока оплаты", 15,
      "Взнос вносится до этого числа месяца, следующего за расчётным", None),
    ("Текущая цветовая схема", ARGS.scheme,
     "ЧБ — для печати на А4; ЦВЕТ — для выгрузки в PDF. Переключается макросом",
     None),
]

for i, name in enumerate(["Параметр", "Значение", "Примечание"], start=1):
    c = cfg.cell(1, i, name)
    c.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="263238")
    c.border = BOX
    c.alignment = Alignment(horizontal="center", vertical="center")

for i, (name, value, note, fmt) in enumerate(CFG_ROWS, start=2):
    cfg.cell(i, 1, name).font = Font(name=FONT, size=10, bold=True)
    vc = cfg.cell(i, 2, value)
    vc.font = Font(name=FONT, size=10)
    if fmt:
        vc.number_format = fmt
    cfg.cell(i, 3, note).font = Font(name=FONT, size=9, italic=True,
                                     color="666666")
    for col in range(1, 4):
        cfg.cell(i, col).border = BOX
        cfg.cell(i, col).alignment = Alignment(vertical="center", wrap_text=True)

CFG_REF = {name: f"{CFG}!$B${i}" for i, (name, _, _, _) in enumerate(CFG_ROWS, start=2)}

cfg.column_dimensions["A"].width = 34
cfg.column_dimensions["B"].width = 62
cfg.column_dimensions["C"].width = 48
cfg.sheet_view.showGridLines = False

# Строка платежа по ГОСТ Р 56042-2014 (формат ST00012). Собирается формулой,
# чтобы её можно было и прочитать глазами, и передать в генератор QR.
QR_ROW = len(CFG_ROWS) + 4
cfg.cell(QR_ROW, 1, "Строка QR (ГОСТ Р 56042-2014)").font = Font(
    name=FONT, size=10, bold=True)
qr_cell = cfg.cell(QR_ROW, 2)
qr_cell.value = (
    f'="ST00012|Name="&{CFG_REF["Получатель платежа"]}'
    f'&"|PersonalAcc="&{CFG_REF["Расчётный счёт (спец. счёт МКД)"]}'
    f'&"|BankName="&{CFG_REF["Банк"]}'
    f'&"|BIC="&{CFG_REF["БИК"]}'
    f'&"|CorrespAcc="&{CFG_REF["Корреспондентский счёт"]}'
    f'&"|PayeeINN="&{CFG_REF["ИНН"]}'
    f'&"|KPP="&{CFG_REF["КПП"]}'
    f'&"|Sum="&TEXT(ROUND(КВ_ИТОГО*100,0),"0")'
    f'&"|Purpose=Взнос на капитальный ремонт за "&{CFG_REF["Расчётный период (текст)"]}'
    f'&", л/с "&КВ_ЛС'
    f'&"|PersAcc="&КВ_ЛС'
    f'&"|PayerAddress="&КВ_АДРЕС'
)
qr_cell.font = Font(name=FONT, size=9)
qr_cell.alignment = Alignment(wrap_text=True, vertical="top")
cfg.cell(QR_ROW, 3,
         "Сумма — в копейках, как требует стандарт. Значение читается "
         "макросом (функция СтрокаQR) и передаётся в генератор QR-кода."
         ).font = Font(name=FONT, size=9, italic=True, color="666666")
cfg.row_dimensions[QR_ROW].height = 64

# --------------------------------------------------------------------------
# Лист ДАННЫЕ — точка стыковки с таблицей разноски
# --------------------------------------------------------------------------
data = wb.create_sheet(DATA)

DATA_COLS = [
    ("Лицевой счёт", 14, None),
    ("Квартира", 10, None),
    ("ФИО собственника", 30, None),
    ("Адрес помещения", 38, None),
    ("Площадь, м²", 12, AREA),
    ("Размер взноса, руб./м²", 18, RATE),
    ("Начислено за период, руб.", 20, MONEY),
    ("Задолженность на начало периода, руб.", 26, MONEY),
    ("Перерасчёт / переплата, руб.", 22, MONEY),
    ("ИТОГО к оплате, руб.", 18, MONEY),
    ("Оплачено с начала года, руб.", 22, MONEY),
    ("Остаток на спец. счёте МКД, руб.", 24, MONEY),
    ("Расчётный период (текст)", 20, None),
    ("Дата начала периода", 18, DATEFMT),
    ("Срок оплаты (если отличается)", 18, DATEFMT),
    ("№ квитанции", 18, None),
]

for i, (name, width, _) in enumerate(DATA_COLS, start=1):
    c = data.cell(1, i, name)
    c.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="263238")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = BOX
    data.column_dimensions[get_column_letter(i)].width = width
data.row_dimensions[1].height = 34

# Демонстрационная строка — цифры из образца и прототипа.
DEMO = [31202, 49, "Иванов Иван Иванович",
        "г. Омск, ул. Магистральная, 2, кв. 49", 63.1, None,
        674.99, 19501.38, 0, 20176.37, 13441.28, None,
        "Июль 2026", dt.datetime(2026, 7, 1), None,
        "КР-2026-07-31202"]

for i, value in enumerate(DEMO, start=1):
    c = data.cell(2, i, value)
    c.font = Font(name=FONT, size=9)
    c.border = BOX
    c.alignment = Alignment(vertical="center")
    fmt = DATA_COLS[i - 1][2]
    if fmt:
        c.number_format = fmt

data.freeze_panes = "A2"
data.auto_filter.ref = f"A1:{get_column_letter(len(DATA_COLS))}1"

hint = data.cell(4, 1,
                 "Строка 2 — пример из образца. Ниже макрос разноски дописывает "
                 "по одной строке на лицевой счёт за расчётный период. "
                 "Ключ поиска — столбец A (лицевой счёт): по нему лист КВИТАНЦИЯ "
                 "подтягивает все значения формулами ИНДЕКС/ПОИСКПОЗ. "
                 "Столбцы F, J, L и P можно оставить пустыми — бланк рассчитает "
                 "их сам либо поставит прочерк.")
hint.font = Font(name=FONT, size=9, italic=True, color="666666")
hint.alignment = Alignment(wrap_text=True, vertical="top")
data.merge_cells(start_row=4, start_column=1, end_row=6, end_column=8)

# --------------------------------------------------------------------------
# Лист КВИТАНЦИЯ
# --------------------------------------------------------------------------
ws = wb.create_sheet(SHEET, 0)

# D и F — колонки подписей во втором разделе («Квартира №», «Размер взноса,
# руб./м²», «Дата формирования», «Период оплаты»). Им нужен запас, иначе
# на печати текст и цифры срезаются.
WIDTHS = {"A": 1.8, "B": 20.5, "C": 12.5, "D": 15.0, "E": 10.5,
          "F": 15.0, "G": 12.0, "H": 14.0, "I": 1.8}
for col, w in WIDTHS.items():
    ws.column_dimensions[col].width = w
ws.sheet_view.showGridLines = False

PERIOD_TXT = (f'IF({lookup("$M")}="",{CFG_REF["Расчётный период (текст)"]},'
              f'{d("$M")})')
PERIOD_DATE = (f'IF({lookup("$N")}="",{CFG_REF["Дата начала периода"]},'
               f'{d("$N")})')
DUE_DAY = CFG_REF["День срока оплаты"]
DUE_DATE = (f'IF({lookup("$O")}="",EOMONTH({PERIOD_DATE},0)+{DUE_DAY},{d("$O")})')

# --- Шапка ---------------------------------------------------------------
spacer(ws, 1, 6)
# Наименование документа по ЖК РФ — «платёжный документ» (ч. 2 ст. 155,
# ч. 1 и 3 ст. 171; примерная форма — приказ Минстроя от 26.01.2018 № 43/пр).
# Слово «квитанция» в кодексе не употребляется, но привычно жителям,
# поэтому оставлено в скобках вторым названием.
ws.row_dimensions[2].height = 40
put(ws, "B2:H2",
    rich(("ПЛАТЁЖНЫЙ ДОКУМЕНТ (КВИТАНЦИЯ)\n", True, 13),
         ("на внесение взноса на капитальный ремонт общего имущества "
          "в многоквартирном доме", True, 9),
         role="title"),
    role="title", size=13, bold=True, align="center", valign="center",
    wrap=True, border=BOX_MED)

ws.row_dimensions[3].height = 20
put(ws, "B3:E3", f'="Специальный счёт МКД · "&{CFG_REF["Адрес МКД"]}',
    role="subtitle", size=9, bold=True, align="left", indent=1)
put(ws, "F3:H3", f'="Расчётный период: "&{PERIOD_TXT}',
    role="subtitle", size=9, bold=True, align="right", indent=1)
outline(ws, "B3:H3")
spacer(ws, 4)

# --- 1. Получатель платежа ------------------------------------------------
ws.row_dimensions[5].height = 16
put(ws, "B5:H5", "1. ПОЛУЧАТЕЛЬ ПЛАТЕЖА — ВЛАДЕЛЕЦ СПЕЦИАЛЬНОГО СЧЁТА",
    role="section", size=10, bold=True, indent=1)
edge(ws, "B5:H5", bottom=MEDIUM)

ws.row_dimensions[6].height = 26
put(ws, "B6", "Получатель платежа", role="label", size=8, bold=True,
    wrap=True, indent=1)
put(ws, "C6:H6", f'={CFG_REF["Получатель платежа"]}',
    role="value", size=9, bold=True, wrap=True, indent=1)

ws.row_dimensions[7].height = 14
put(ws, "B7", "Юридический адрес", role="label", size=8, bold=True, indent=1)
put(ws, "C7:H7", f'={CFG_REF["Юридический адрес"]}', role="value", indent=1)

ws.row_dimensions[8].height = 14
put(ws, "B8", "ИНН / КПП", role="label", size=8, bold=True, indent=1)
put(ws, "C8:D8", f'={CFG_REF["ИНН"]}&" / "&{CFG_REF["КПП"]}',
    role="value", indent=1)
put(ws, "E8", "ОГРН", role="label", size=8, bold=True, indent=1)
put(ws, "F8:H8", f'={CFG_REF["ОГРН"]}', role="value", indent=1)

ws.row_dimensions[9].height = 16
put(ws, "B9", "Расчётный счёт", role="label", size=8, bold=True, indent=1)
put(ws, "C9:H9",
    f'={CFG_REF["Расчётный счёт (спец. счёт МКД)"]}'
    f'&"   (специальный счёт МКД: "&{CFG_REF["Адрес МКД"]}&")"',
    role="value", size=10, bold=True, indent=1)

ws.row_dimensions[10].height = 14
put(ws, "B10", "Банк", role="label", size=8, bold=True, indent=1)
put(ws, "C10:H10", f'={CFG_REF["Банк"]}', role="value", indent=1)

ws.row_dimensions[11].height = 14
put(ws, "B11", "Корр. счёт / БИК", role="label", size=8, bold=True, indent=1)
put(ws, "C11:D11",
    f'={CFG_REF["Корреспондентский счёт"]}&" / "&{CFG_REF["БИК"]}',
    role="value", indent=1)
put(ws, "E11", "ИНН/КПП банка", role="label", size=8, bold=True, indent=1)
put(ws, "F11:H11", f'={CFG_REF["ИНН/КПП банка"]}', role="value", indent=1)

outline(ws, "B5:H11")
spacer(ws, 12)

# --- 2. Плательщик и помещение -------------------------------------------
ws.row_dimensions[13].height = 16
put(ws, "B13:H13", "2. ПЛАТЕЛЬЩИК И ПОМЕЩЕНИЕ", role="section",
    size=10, bold=True, indent=1)
edge(ws, "B13:H13", bottom=MEDIUM)

ws.row_dimensions[14].height = 19
put(ws, "B14", "Лицевой счёт", role="label", size=8, bold=True, indent=1)
put(ws, "C14", 31202, role="input", size=11, bold=True, align="center",
    border=BOX_MED)
put(ws, "D14", "Квартира №", role="label", size=8, bold=True, indent=1)
put(ws, "E14", f"={lookup('$B')}", role="value", size=10, bold=True,
    align="center")
put(ws, "F14", "Дата формирования", role="label", size=8, bold=True,
    wrap=True, indent=1)
put(ws, "G14:H14", "=TODAY()", role="value", size=10, align="center",
    fmt=DATEFMT)

ws.row_dimensions[15].height = 17
put(ws, "B15", "Плательщик", role="label", size=8, bold=True, indent=1)
put(ws, "C15:H15", f"={lookup('$C')}", role="value", size=10, bold=True,
    indent=1)

ws.row_dimensions[16].height = 16
put(ws, "B16", "Адрес помещения", role="label", size=8, bold=True, indent=1)
put(ws, "C16:H16", f"={lookup('$D')}", role="value", size=9, indent=1)

ws.row_dimensions[17].height = 20
put(ws, "B17", "Площадь помещения, м²", role="label", size=8, bold=True,
    wrap=True, indent=1)
put(ws, "C17", f"={lookup('$E', empty='0')}", role="value", size=10, bold=True,
    align="center", fmt=AREA)
put(ws, "D17", "Размер взноса, руб./м²", role="label", size=8, bold=True,
    wrap=True, indent=1)
# Если тариф в разноске не заполнен — восстанавливаем его из начисления.
put(ws, "E17",
    f'=IF({lookup("$F")}="",IFERROR(ROUND({d("$G")}/{d("$E")},2),"—"),{d("$F")})',
    role="value", size=10, bold=True, align="center", fmt=RATE)
put(ws, "F17", "Период оплаты", role="label", size=8, bold=True, indent=1)
put(ws, "G17:H17", f"={PERIOD_TXT}", role="value", size=10, bold=True,
    align="center")

outline(ws, "B13:H17")
spacer(ws, 18)

# --- 3. Расчёт ------------------------------------------------------------
ws.row_dimensions[19].height = 16
put(ws, "B19:H19", "3. РАСЧЁТ РАЗМЕРА ВЗНОСА И СУММЫ К ОПЛАТЕ",
    role="section", size=10, bold=True, indent=1)
edge(ws, "B19:H19", bottom=MEDIUM)

ws.row_dimensions[20].height = 18
put(ws, "B20:E20", "Вид платежа", role="thead", size=9, bold=True, align="center")
put(ws, "F20:G20", "Расчётный период", role="thead", size=9, bold=True,
    align="center")
put(ws, "H20", "Сумма, руб.", role="thead", size=9, bold=True, align="center")
edge(ws, "B20:H20", bottom=MEDIUM)

# Пени в этом доме не начисляются — строки под них в бланке нет.
CALC_ROWS = [
    (21, "Начислено за расчётный период (площадь × размер взноса)",
     f"={PERIOD_TXT}", f"={lookup('$G', empty='0')}"),
    (22, "Задолженность за предыдущие периоды",
     f'="на "&{ru_date(PERIOD_DATE)}', f"={lookup('$H', empty='0')}"),
    (23, "Перерасчёты / переплата (уменьшают сумму к оплате)", None,
     f"={lookup('$I', empty='0')}"),
]
for row, title, period, amount in CALC_ROWS:
    ws.row_dimensions[row].height = 17
    put(ws, f"B{row}:E{row}", title, role="value", size=9, indent=1)
    put(ws, f"F{row}:G{row}", period, role="value", size=9, align="center")
    put(ws, f"H{row}", amount, role="value", size=10, bold=True, align="right",
        fmt=MONEY, indent=1)

# Итог: берём готовое значение из разноски, а если его нет — считаем сами.
ws.row_dimensions[24].height = 28
put(ws, "B24:G24", "ИТОГО К ОПЛАТЕ", role="total", size=14, bold=True, indent=1)
put(ws, "H24", f'=IF({lookup("$J")}="",ROUND(H21+H22+H23,2),{d("$J")})',
    role="totalsum", size=16, bold=True, align="right", fmt=MONEY,
    border=BOX_MED, indent=1)
edge(ws, "B24:H24", top=MEDIUM)

outline(ws, "B19:H24")
spacer(ws, 25)

# --- 4. Справочная информация по специальному счёту -----------------------
ws.row_dimensions[26].height = 16
put(ws, "B26:H26",
    "4. СПРАВОЧНАЯ ИНФОРМАЦИЯ ПО СПЕЦИАЛЬНОМУ СЧЁТУ (ч. 7 ст. 177 ЖК РФ)",
    role="section", size=10, bold=True, indent=1)
edge(ws, "B26:H26", bottom=MEDIUM)

REF_ROWS = [
    (27, f'="Поступило оплат по лицевому счёту с начала "&YEAR({PERIOD_DATE})'
         f'&" года, руб."',
     f"={lookup('$K', empty='0')}"),
    (28, "Остаток средств на специальном счёте многоквартирного дома, руб.",
     f'=IF({lookup("$L")}="","—",{d("$L")})'),
]
for row, title, amount in REF_ROWS:
    ws.row_dimensions[row].height = 15
    put(ws, f"B{row}:F{row}", title, role="value", size=9, indent=1)
    put(ws, f"G{row}:H{row}", amount, role="value", size=10, bold=True,
        align="right", fmt=MONEY, indent=1)

outline(ws, "B26:H28")
spacer(ws, 29)

# --- 5. Порядок оплаты и QR ----------------------------------------------
ws.row_dimensions[30].height = 16
if QR_ВКЛЮЧЁН:
    put(ws, "B30:F30", "5. ПОРЯДОК ОПЛАТЫ", role="section", size=10, bold=True,
        indent=1)
    put(ws, "G30:H30", "QR-КОД ДЛЯ ОПЛАТЫ", role="section", size=10, bold=True,
        align="center")
else:
    # Заголовка над пустой рамкой быть не должно — иначе житель решит,
    # что квитанция напечаталась с ошибкой.
    put(ws, "B30:H30", "5. ПОРЯДОК ОПЛАТЫ", role="section", size=10, bold=True,
        indent=1)

edge(ws, "B30:H30", bottom=MEDIUM)

PAY_LINES = [
    (31, 14, "1) без комиссии — в отделениях АО «Россельхозбанк» "
             "(банк, в котором открыт специальный счёт дома);"),
    (32, 26, rich(
        ("2) по тарифам банка — ", False),
        ("только по номеру расчётного счёта", True),
        (", указанного в разделе 1, в отделениях и мобильных приложениях "
         "ПАО Сбербанк, АО «АЛЬФА-БАНК», Банка ВТБ (ПАО), АО «ТБанк», "
         "а также любого другого банка;", False))),
    # Третий пункт зарезервирован под напоминание об оплате по QR-коду.
    (33, 14, "3) в мобильном приложении любого банка — по QR-коду "
             "(ГОСТ Р 56042-2014)." if QR_ВКЛЮЧЁН else None),
]
for row, height, text in PAY_LINES:
    ws.row_dimensions[row].height = height
    put(ws, f"B{row}:F{row}", text, role="value", size=9, wrap=True, indent=1)

ws.row_dimensions[34].height = 14
put(ws, "B34:F34", "Назначение платежа:", role="label", size=8, bold=True,
    indent=1)

ws.row_dimensions[35].height = 30
put(ws, "B35:F35",
    f'="Взнос на капитальный ремонт, л/с № "&КВ_ЛС&", кв. № "&{lookup("$B")}'
    f'&", за "&{PERIOD_TXT}&"."',
    role="value", size=9, wrap=True, indent=1)

ws.row_dimensions[36].height = 20
put(ws, "B36:F36",
    f'="Срок оплаты: до "&{DUE_DAY}&" числа каждого месяца (за "&{PERIOD_TXT}'
    f'&" — до "&{ru_date(DUE_DATE)}&")"',
    role="note", size=9, bold=True, align="center", wrap=True)

# Место под QR-код зарезервировано, но пока пустое: своего генератора QR нет.
# Когда он появится — QR_ВКЛЮЧЁН = True, и сюда встанет картинка (ВставитьQR).
put(ws, "G31:H36",
    "QR-код\nформируется\nмакросом" if QR_ВКЛЮЧЁН else None,
    role="qr", size=9, bold=True, align="center", wrap=True)

outline(ws, "B30:H36")
spacer(ws, 37)

# --- Подвал ---------------------------------------------------------------
# Ключевое предупреждение: платёж идёт на счёт дома только по номеру
# расчётного счёта. Оплата через поиск «капремонт» уводит деньги на общий
# счёт регионального оператора, откуда их потом приходится разыскивать.
ws.row_dimensions[38].height = 32
put(ws, "B38:H38",
    f'="ВНИМАНИЕ! ПЛАТИТЕ ТОЛЬКО ПО НОМЕРУ РАСЧЁТНОГО СЧЁТА "'
    f'&{CFG_REF["Расчётный счёт (спец. счёт МКД)"]}'
    f'&" — ЭТО СПЕЦИАЛЬНЫЙ СЧЁТ ВАШЕГО ДОМА"',
    role="total", size=11, bold=True, align="center", wrap=True,
    border=BOX_MED)

ws.row_dimensions[39].height = 44
put(ws, "B39:H39",
    f'="В отделении банка и в мобильном приложении во вкладках ищите "'
    f'&"«РФКР МКД_капремонт, оплата по расчётному счёту» и указывайте номер '
    f'расчётного счёта, приведённый выше. Оплата через общий поиск '
    f'«Капитальный ремонт» уходит на общий счёт Регионального фонда '
    f'капитального ремонта и на счёт вашего дома не поступает."'
    f'&CHAR(10)&"Лицевой счёт № "&КВ_ЛС&" при оплате НЕ вводится — он указан '
    f'справочно, только для учёта начислений."',
    role="note", size=9, align="center", wrap=True)

spacer(ws, 40, 6)

ws.row_dimensions[41].height = 24
put(ws, "B41:D41", "Подпись плательщика  ______________________",
    role="plain", size=9, align="center", border=None)
put(ws, "E41:F41", "Кассир  ______________", role="plain", size=9,
    align="center", border=None)
put(ws, "G41:H41", "Дата  ____________", role="plain", size=9,
    align="center", border=None)

ws.row_dimensions[42].height = 22
put(ws, "B42:H42",
    f'="По вопросам начислений обращайтесь к председателю совета дома, тел. "'
    f'&{CFG_REF["Контактный телефон"]}&".    Документ № "'
    f'&IF({lookup("$P")}="","—",{d("$P")})',
    role="value", size=8, italic=True, align="center", wrap=True)

# --- Параметры печати -----------------------------------------------------
ws.print_area = "$A$1:$I$42"
ws.page_setup.orientation = "portrait"
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 1
ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
# Поля в дюймах: 0.24" ≈ 6 мм, 0.2" ≈ 5 мм.
ws.page_margins.left = 0.24
ws.page_margins.right = 0.24
ws.page_margins.top = 0.2
ws.page_margins.bottom = 0.2
ws.page_margins.header = 0.2
ws.page_margins.footer = 0.2
ws.print_options.horizontalCentered = True

dv = DataValidation(type="list", formula1=f"={DATA}!$A$2:$A$5000",
                    allow_blank=True, showDropDown=False)
dv.promptTitle = "Лицевой счёт"
dv.prompt = "Выберите лицевой счёт из листа ДАННЫЕ"
ws.add_data_validation(dv)
dv.add(ws["C14"])

# --------------------------------------------------------------------------
# Лист СХЕМА — по нему макрос перекрашивает бланк
# --------------------------------------------------------------------------
sch = wb.create_sheet(SCHEME)
for i, name in enumerate(["Роль", "Диапазоны (через запятую)", "ЧБ: заливка",
                          "ЧБ: шрифт", "ЦВЕТ: заливка", "ЦВЕТ: шрифт"], start=1):
    c = sch.cell(1, i, name)
    c.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="263238")
    c.border = BOX
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

row = 2
for role, ((bw_fill, bw_font), (cl_fill, cl_font)) in PALETTE.items():
    ranges = ROLE_RANGES[role]
    if not ranges:
        continue
    for col, value in enumerate(
            [role, ",".join(ranges), bw_fill, bw_font, cl_fill, cl_font], start=1):
        c = sch.cell(row, col, value)
        c.font = Font(name=FONT, size=9)
        c.border = BOX
        c.alignment = Alignment(vertical="top", wrap_text=(col == 2))
    row += 1

sch.cell(row + 1, 1,
         "Служебная таблица. Макрос ПрименитьСхему читает её и перекрашивает "
         "лист КВИТАНЦИЯ. Цвета задаются шестью шестнадцатеричными знаками "
         "RRGGBB — правьте прямо здесь, код менять не нужно."
         ).font = Font(name=FONT, size=9, italic=True, color="666666")
sch.merge_cells(start_row=row + 1, start_column=1, end_row=row + 2, end_column=6)
sch.cell(row + 1, 1).alignment = Alignment(wrap_text=True, vertical="top")

sch.column_dimensions["A"].width = 12
sch.column_dimensions["B"].width = 90
for col in "CDEF":
    sch.column_dimensions[col].width = 14
sch.sheet_state = "hidden"

# --------------------------------------------------------------------------
# Лист ИНСТРУКЦИЯ
# --------------------------------------------------------------------------
doc = wb.create_sheet(HELP)
LINES = [
    ("h", "КАК ВСТРОИТЬ ЭТОТ БЛАНК В СУЩЕСТВУЮЩУЮ ТАБЛИЦУ РАЗНОСКИ"),
    ("", ""),
    ("s", "1. Перенос листов"),
    ("t", "Скопируйте в свою книгу (правый клик по ярлыку листа → "
          "Переместить/скопировать) листы КВИТАНЦИЯ, ДАННЫЕ, НАСТРОЙКИ и СХЕМА. "
          "Лист СХЕМА скрыт: чтобы увидеть его, нажмите правой кнопкой на любом "
          "ярлыке → Показать."),
    ("t", "Именованные диапазоны (КВ_ЛС, КВ_НАЧИСЛЕНО, КВ_ДОЛГ, КВ_ИТОГО и др.) "
          "переносятся вместе с листами. Проверьте их в Формулы → Диспетчер имён."),
    ("t", "Импортируйте модуль vba/modКвитанция.bas: Alt+F11 → File → Import File. "
          "Книгу сохраните как .xlsm."),
    ("", ""),
    ("s", "2. Подключение разноски"),
    ("t", "Лист ДАННЫЕ — единственная точка стыковки. Ваш макрос разноски кладёт "
          "в него по одной строке на лицевой счёт за расчётный период. "
          "Ключ поиска — столбец A (лицевой счёт)."),
    ("t", "Если разноска уже лежит на другом листе, не копируйте её: пропишите в "
          "столбцах листа ДАННЫЕ обычные формулы-ссылки на этот лист "
          "(ВПР или ИНДЕКС+ПОИСКПОЗ). Бланк разницы не заметит."),
    ("", ""),
    ("s", "3. Автоподстановка сумм"),
    ("t", "Достаточно записать лицевой счёт в ячейку КВИТАНЦИЯ!C14 (имя КВ_ЛС) — "
          "ФИО, адрес, площадь, начислено, долг и итог подтянутся формулами."),
    ("t", "Если суммы удобнее подавать напрямую из макроса, вызывайте процедуру "
          "ПодставитьСуммы: она пишет значения в лист ДАННЫЕ, а формулы бланка "
          "пересчитываются сами."),
    ("t", "ИТОГО К ОПЛАТЕ берётся из столбца J листа ДАННЫЕ. Если столбец пуст, "
          "бланк считает итог сам: начислено + долг + перерасчёт. Пени в этом "
          "доме не начисляются, поэтому строки под них в бланке нет."),
    ("", ""),
    ("s", "4. Печать и PDF"),
    ("t", "Книга сохранена в чёрно-белой схеме — можно сразу печатать на А4: "
          "одна страница, поля 5 мм, вписано по ширине и высоте."),
    ("t", "Макрос ЭкспортКвитанцииВPDF временно переключает бланк в цветную схему, "
          "выгружает PDF и возвращает чёрно-белый вид. Файл для отправки жителю "
          "получается цветным, бумажная копия остаётся чёрно-белой."),
    ("t", "Макрос ПакетныйЭкспортPDF делает то же самое по всем лицевым счетам "
          "листа ДАННЫЕ и раскладывает файлы по выбранной папке."),
    ("t", "Макросы СхемаЧБ и СхемаЦвет переключают вид вручную — например, чтобы "
          "посмотреть, как квитанция будет выглядеть у жителя на экране."),
    ("", ""),
    ("s", "5. QR-код"),
    ("t", "Строка платежа по ГОСТ Р 56042-2014 собирается формулой на листе "
          "НАСТРОЙКИ (имя КВ_QR) и готова к передаче в любой генератор QR. "
          "Функция СтрокаQR возвращает её из VBA."),
    ("t", "Сама картинка QR в шаблон не встроена: вставьте изображение в область "
          "G31:H36 вручную либо подключите свой генератор в процедуре ВставитьQR "
          "(в модуле оставлена заготовка)."),
    ("", ""),
    ("s", "6. Что проверить перед первой выдачей квитанций"),
    ("t", "• Размер взноса (руб./м²). В исходном файле он подтягивался из внешней "
          "книги, поэтому столбец F листа ДАННЫЕ оставлен пустым, а бланк "
          "восстанавливает тариф как начислено ÷ площадь. Впишите утверждённый "
          "тариф, чтобы в квитанции стояла точная величина."),
    ("t", "• Остаток средств на специальном счёте многоквартирного дома "
          "(столбец L). Пока он пуст, в разделе 4 стоит прочерк."),
    ("t", "• Реквизиты специального счёта на листе НАСТРОЙКИ — они перенесены из "
          "вашего образца без изменений."),
]

r = 1
for kind, text in LINES:
    c = doc.cell(r, 1, text)
    if kind == "h":
        c.font = Font(name=FONT, size=13, bold=True, color="0F6B70")
        doc.row_dimensions[r].height = 26
    elif kind == "s":
        c.font = Font(name=FONT, size=11, bold=True, color="263238")
        doc.row_dimensions[r].height = 22
    elif kind == "t":
        c.font = Font(name=FONT, size=10)
        doc.row_dimensions[r].height = 32
    else:
        doc.row_dimensions[r].height = 8
    c.alignment = Alignment(wrap_text=True, vertical="top")
    doc.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    r += 1

doc.column_dimensions["A"].width = 22
for col in "BCDEF":
    doc.column_dimensions[col].width = 18
doc.sheet_view.showGridLines = False

# --------------------------------------------------------------------------
# Именованные диапазоны — адреса для макроса
# --------------------------------------------------------------------------
NAMES = {
    "КВ_ЛС": f"{SHEET}!$C$14",
    "КВ_КВАРТИРА": f"{SHEET}!$E$14",
    "КВ_ДАТА": f"{SHEET}!$G$14",
    "КВ_ФИО": f"{SHEET}!$C$15",
    "КВ_АДРЕС": f"{SHEET}!$C$16",
    "КВ_ПЛОЩАДЬ": f"{SHEET}!$C$17",
    "КВ_ТАРИФ": f"{SHEET}!$E$17",
    "КВ_ПЕРИОД": f"{SHEET}!$G$17",
    "КВ_НАЧИСЛЕНО": f"{SHEET}!$H$21",
    "КВ_ДОЛГ": f"{SHEET}!$H$22",
    "КВ_ПЕРЕРАСЧЕТ": f"{SHEET}!$H$23",
    "КВ_ИТОГО": f"{SHEET}!$H$24",
    "КВ_ОПЛАЧЕНО": f"{SHEET}!$G$27",
    "КВ_ОСТАТОК": f"{SHEET}!$G$28",
    "КВ_QR_МЕСТО": f"{SHEET}!$G$31",
    "КВ_QR": f"{CFG}!$B${QR_ROW}",
    "КВ_СХЕМА": CFG_REF["Текущая цветовая схема"],
    "ДАННЫЕ_ТАБЛИЦА": f"{DATA}!$A$1:$P$5000",
}
for name, ref in NAMES.items():
    wb.defined_names.add(DefinedName(name, attr_text=ref))

wb.active = 0
OUT.parent.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print(f"Готово: {OUT}")
