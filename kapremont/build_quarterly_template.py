# -*- coding: utf-8 -*-
"""
Генератор квартальной книги: квитанции и сопроводительные письма
по взносам на капитальный ремонт (специальный счёт МКД Магистральная, 2).

Книга рассчитана на юридическое лицо-собственника (Департамент жилищной
политики Администрации г. Омска, кв. 47) и выставляется поквартально.

Листы:

    ИСХОДНЫЕ ДАННЫЕ  — единственное место для ввода: тариф, площадь,
                       начисление, задолженность и даты по каждому кварталу,
                       реквизиты председателя и адресата письма;
    Квитанция 1–4 кв — платёжный документ на квартал, три строки начисления
                       по месяцам квартала плюс задолженность;
    Письмо 1–4 кв    — сопроводительное письмо, суммы и периоды подтягиваются
                       формулами, сумма прописью считается на листе ПРОПИСЬ;
    ПРОПИСЬ          — скрытый справочник числительных (0–999) для суммы
                       прописью без макросов;
    ИНСТРУКЦИЯ       — порядок работы с книгой.

Запуск:
    python3 build_quarterly_template.py                # рабочая книга (ЧБ)
    python3 build_quarterly_template.py --scheme ЦВЕТ  # цветной вариант
"""

import argparse
import datetime as dt
from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.properties import PageSetupProperties

OUTDIR = Path(__file__).resolve().parent / "output"

_parser = argparse.ArgumentParser(description=__doc__)
_parser.add_argument("--scheme", choices=["ЧБ", "ЦВЕТ"], default="ЧБ")
ARGS = _parser.parse_args()
SCHEME_COL = 0 if ARGS.scheme == "ЧБ" else 1
OUT = OUTDIR / ("Квитанции_квартальные_шаблон.xlsx" if SCHEME_COL == 0
                else "Квитанции_квартальные_цветной.xlsx")

SRC = "ИСХОДНЫЕ ДАННЫЕ"
WORDS = "ПРОПИСЬ"
HELP = "ИНСТРУКЦИЯ"
FONT = "Arial"

QR_ВКЛЮЧЁН = False

PALETTE = {
    "title":     (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "subtitle":  (("FFFFFF", "000000"), ("DDEFF0", "0F6B70")),
    "section":   (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "thead":     (("FFFFFF", "000000"), ("263238", "FFFFFF")),
    "label":     (("FFFFFF", "000000"), ("F3F5F5", "263238")),
    "value":     (("FFFFFF", "000000"), ("FFFFFF", "263238")),
    "subtotal":  (("FFFFFF", "000000"), ("F3F5F5", "263238")),
    "total":     (("FFFFFF", "000000"), ("0F6B70", "FFFFFF")),
    "totalsum":  (("FFFFFF", "000000"), ("E8F3F3", "0F6B70")),
    "note":      (("FFFFFF", "000000"), ("E8F3F3", "263238")),
    "qr":        (("FFFFFF", "000000"), ("F3F5F5", "0F6B70")),
    "plain":     (("FFFFFF", "000000"), ("FFFFFF", "263238")),
}

THIN = Side(style="thin", color="000000")
MEDIUM = Side(style="medium", color="000000")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BOX_MED = Border(left=MEDIUM, right=MEDIUM, top=MEDIUM, bottom=MEDIUM)

MONEY = '#,##0.00'
AREA = '#,##0.0'
DATEFMT = 'DD.MM.YYYY'

КВАРТАЛЫ = [
    (1, "I", ["январь", "февраль", "март"]),
    (2, "II", ["апрель", "май", "июнь"]),
    (3, "III", ["июль", "август", "сентябрь"]),
    (4, "IV", ["октябрь", "ноябрь", "декабрь"]),
]
# Родительный падеж для фразы «за период с января по март»
РОДИТ = {"январь": "января", "февраль": "февраля", "март": "марта",
         "апрель": "апреля", "май": "мая", "июнь": "июня",
         "июль": "июля", "август": "августа", "сентябрь": "сентября",
         "октябрь": "октября", "ноябрь": "ноября", "декабрь": "декабря"}


# --------------------------------------------------------------------------
# Оформление
# --------------------------------------------------------------------------
def put(ws, ref, value=None, *, role="plain", size=9, bold=False, italic=False,
        align="left", valign="center", wrap=False, fmt=None, border=BOX,
        indent=0):
    if ":" in ref:
        ws.merge_cells(ref)
        first = ref.split(":")[0]
    else:
        first = ref
    cell = ws[first]
    if value is not None:
        cell.value = value

    fill_hex, font_hex = PALETTE[role][SCHEME_COL]
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
                bottom=side if ri == last_r else b.bottom)


def edge(ws, ref, top=None, bottom=None):
    for row in ws[ref]:
        for c in row:
            b = c.border
            c.border = Border(left=b.left, right=b.right,
                              top=top or b.top, bottom=bottom or b.bottom)


def rich(*parts, role="value", size=9):
    color = PALETTE[role][SCHEME_COL][1]
    blocks = []
    for part in parts:
        text, bold = part[0], part[1]
        sz = part[2] if len(part) > 2 else size
        blocks.append(TextBlock(
            InlineFont(rFont=FONT, sz=sz, b=bold, color=color), text))
    return CellRichText(*blocks)


def ru_date(expr):
    """Дата ДД.ММ.ГГГГ без локалезависимых кодов формата в TEXT."""
    return (f'TEXT(DAY({expr}),"00")&"."&TEXT(MONTH({expr}),"00")&"."'
            f'&YEAR({expr})')


# --------------------------------------------------------------------------
# Числительные для суммы прописью
# --------------------------------------------------------------------------
ЕДИНИЦЫ_М = ["ноль", "один", "два", "три", "четыре", "пять", "шесть", "семь",
             "восемь", "девять", "десять", "одиннадцать", "двенадцать",
             "тринадцать", "четырнадцать", "пятнадцать", "шестнадцать",
             "семнадцать", "восемнадцать", "девятнадцать"]
ЕДИНИЦЫ_Ж = ЕДИНИЦЫ_М.copy()
ЕДИНИЦЫ_Ж[1], ЕДИНИЦЫ_Ж[2] = "одна", "две"
ДЕСЯТКИ = ["", "", "двадцать", "тридцать", "сорок", "пятьдесят", "шестьдесят",
           "семьдесят", "восемьдесят", "девяносто"]
СОТНИ = ["", "сто", "двести", "триста", "четыреста", "пятьсот", "шестьсот",
         "семьсот", "восемьсот", "девятьсот"]


def прописью(n, женский=False):
    """Число 0–999 словами."""
    единицы = ЕДИНИЦЫ_Ж if женский else ЕДИНИЦЫ_М
    if n == 0:
        return единицы[0]
    части = []
    if n >= 100:
        части.append(СОТНИ[n // 100])
        n %= 100
    if n >= 20:
        части.append(ДЕСЯТКИ[n // 10])
        n %= 10
    if n > 0:
        части.append(единицы[n])
    return " ".join(части)


def форма(n, одна, две, много):
    """Согласование существительного с числом: рубль / рубля / рублей."""
    сотня = n % 100
    if 11 <= сотня <= 19:
        return много
    последняя = n % 10
    if последняя == 1:
        return одна
    if последняя in (2, 3, 4):
        return две
    return много


# ==========================================================================
wb = Workbook()

# --------------------------------------------------------------------------
# Лист ИСХОДНЫЕ ДАННЫЕ
# --------------------------------------------------------------------------
src = wb.active
src.title = SRC
src.sheet_view.showGridLines = False

# 104 знака ≈ 19,8 см — ровно ширина книжного А4 с полями 1 см.
for col, width in {"A": 3, "B": 26, "C": 28, "D": 32, "E": 13,
                   "F": 13, "G": 13}.items():
    src.column_dimensions[col].width = width


# Лист ввода на печать не идёт, поэтому он всегда в фирменной бирюзовой
# гамме — той же, что и цветная квитанция для жителей.
ACCENT = "0F6B70"       # заголовки блоков
ACCENT_LIGHT = "E8F3F3"  # ячейки для ввода
GREY = "F3F5F5"          # названия параметров
TXT = "263238"


def заголовок_блока(row, text):
    src.row_dimensions[row].height = 20
    c = src.cell(row, 2, text)
    src.merge_cells(start_row=row, start_column=2, end_row=row, end_column=7)
    for i in range(2, 8):
        cc = src.cell(row, i)
        cc.font = Font(name=FONT, size=10, bold=True, color="FFFFFF")
        cc.fill = PatternFill("solid", fgColor=ACCENT)
        cc.border = BOX
        cc.alignment = Alignment(vertical="center", indent=1)
    return c


def параметр(row, name, value, note="", fmt=None, вводимый=True):
    src.row_dimensions[row].height = 30
    n = src.cell(row, 2, name)
    n.font = Font(name=FONT, size=10, bold=True, color=TXT)
    n.fill = PatternFill("solid", fgColor=GREY)
    v = src.cell(row, 3, value)
    v.font = Font(name=FONT, size=10, bold=вводимый,
                  color=ACCENT if вводимый else TXT)
    if fmt:
        v.number_format = fmt
    if вводимый:
        v.fill = PatternFill("solid", fgColor=ACCENT_LIGHT)
    h = src.cell(row, 4, note)
    h.font = Font(name=FONT, size=9, italic=True, color="666666")
    for i in (2, 3, 4):
        src.cell(row, i).border = BOX
        src.cell(row, i).alignment = Alignment(vertical="center", wrap_text=True)
    return f"'{SRC}'!$C${row}"


src.row_dimensions[1].height = 26
t = src.cell(1, 2, "ИСХОДНЫЕ ДАННЫЕ ДЛЯ КВИТАНЦИЙ И ПИСЕМ")
t.font = Font(name=FONT, size=14, bold=True, color=ACCENT)
src.merge_cells("B1:G1")

src.cell(2, 2, "Ячейки на бирюзовом фоне — для ввода. Всё остальное в книге "
               "считается формулами от них; квитанции и письма пересчитаются "
               "сами.")
src.cell(2, 2).font = Font(name=FONT, size=9, italic=True, color="666666")
src.merge_cells("B2:G2")
src.row_dimensions[2].height = 16

заголовок_блока(4, "1. РАСЧЁТ: ТАРИФ, ПЛОЩАДЬ, НАЧИСЛЕНИЕ")
R_ГОД = параметр(5, "Год", 2026, "Подставляется во все периоды")
R_ПЛОЩАДЬ = параметр(6, "Площадь помещения, м²", 52.8, "Из образца", AREA)
R_ТАРИФ = параметр(7, "Размер взноса, руб./м² в месяц", 15.3,
                   "Меняется ежегодно — правится здесь", MONEY)
src.row_dimensions[8].height = 18
_n = src.cell(8, 2, "Начислено за месяц, руб.")
_n.font = Font(name=FONT, size=10, bold=True)
_v = src.cell(8, 3, f"=ROUND({R_ПЛОЩАДЬ}*{R_ТАРИФ},2)")
_v.font = Font(name=FONT, size=10, bold=True)
_v.number_format = MONEY
_h = src.cell(8, 4, "Считается как площадь × тариф. Чтобы задать сумму вручную, "
                    "замените формулу числом")
_h.font = Font(name=FONT, size=9, italic=True, color="666666")
for i in (2, 3, 4):
    src.cell(8, i).border = BOX
    src.cell(8, i).alignment = Alignment(vertical="center", wrap_text=True)
R_НАЧ_МЕС = f"'{SRC}'!$C$8"

заголовок_блока(10, "2. ПЛАТЕЛЬЩИК И ПОМЕЩЕНИЕ")
R_ЛС = параметр(11, "Лицевой счёт", 3120247,
                "Лицевой счёт помещения по этому адресу")
R_КВ = параметр(12, "Квартира №", 47, "Из образца")
R_ПЛАТЕЛЬЩИК = параметр(
    13, "Плательщик (собственник)",
    "Департамент жилищной политики Администрации города Омска",
    "Юридическое лицо — собственник помещения")
R_АДРЕС_МКД = параметр(14, "Адрес МКД", "г. Омск, ул. Магистральная, 2",
                       "Не меняется")
R_МКД_КРАТКО = параметр(15, "МКД кратко", "Магистральная, 2",
                        "Для подписи: «Председатель МКД Магистральная, 2»")

заголовок_блока(17, "3. ПРЕДСЕДАТЕЛЬ СОВЕТА ДОМА (ОТ КОГО ПИСЬМО)")
R_ПРЕД_ФИО_Р = параметр(18, "ФИО в родительном падеже",
                        "Яворсюк Елены Викторовны",
                        "«от Председателя … Яворсюк Елены Викторовны»")
R_ПРЕД_ФИО_К = параметр(19, "ФИО кратко", "Яворсюк Е.В.", "Для подписи")
R_ПРЕД_АДРЕС = параметр(20, "Адрес проживания",
                        "г. Омск, ул. Магистральная, д. 2, кв. 49", "")
R_ПРЕД_ТЕЛ = параметр(21, "Телефон", "8-908-108-02-00", "")
R_ПРЕД_ПОЧТА = параметр(22, "Электронная почта", "e.yavorsuk@mail.ru", "")

заголовок_блока(24, "4. АДРЕСАТ ПИСЬМА (МЕНЯЕТСЯ ПРИ СМЕНЕ РУКОВОДИТЕЛЯ)")
R_АДРЕСАТ_ОРГ = параметр(
    25, "Организация",
    "Департамент жилищной политики Администрации города Омска", "")
R_АДРЕСАТ_ДОЛЖН = параметр(26, "Должность руководителя", "Директору",
                           "В дательном падеже: «Директору»")
R_АДРЕСАТ_ФИО = параметр(27, "ФИО руководителя", "",
                         "Оставьте пустым — строка не напечатается")

заголовок_блока(29, "5. ПО КВАРТАЛАМ: ЗАДОЛЖЕННОСТЬ И ДАТЫ")
HDR = ["Квартал", "Задолженность, руб.", "Описание задолженности",
       "Дата формирования", "Поступило с начала года, руб."]
src.row_dimensions[30].height = 32
for i, name in enumerate(HDR, start=2):
    c = src.cell(30, i, name)
    c.font = Font(name=FONT, size=9, bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor=ACCENT)
    c.border = BOX
    c.alignment = Alignment(horizontal="center", vertical="center",
                            wrap_text=True)

# Значения 1 квартала — из образца; остальные кварталы заполняются по факту.
ДАННЫЕ_КВ = [
    ("I квартал", 4042.38, "за III и IV кварталы 2025 года",
     dt.datetime(2026, 1, 29), None),
    ("II квартал", 0, "", dt.datetime(2026, 4, 15), None),
    ("III квартал", 0, "", dt.datetime(2026, 7, 15), None),
    ("IV квартал", 0, "", dt.datetime(2026, 10, 15), None),
]
for k, (имя, долг, описание, дата, опл) in enumerate(ДАННЫЕ_КВ):
    row = 31 + k
    src.row_dimensions[row].height = 30
    values = [имя, долг, описание, дата, опл]
    formats = [None, MONEY, None, DATEFMT, MONEY]
    for i, (v, f) in enumerate(zip(values, formats), start=2):
        c = src.cell(row, i, v)
        c.font = Font(name=FONT, size=10, bold=(i == 2),
                      color=TXT if i == 2 else ACCENT)
        c.border = BOX
        c.alignment = Alignment(vertical="center", wrap_text=True)
        if f:
            c.number_format = f
        c.fill = PatternFill("solid",
                             fgColor=GREY if i == 2 else ACCENT_LIGHT)

src.cell(36, 2,
         "Задолженность и даты — единственное, что меняется от квартала "
         "к кварталу. Столбец «Поступило» можно не заполнять: в квитанции "
         "тогда встанет прочерк.")
src.cell(36, 2).font = Font(name=FONT, size=9, italic=True, color="666666")
src.merge_cells("B36:G37")
src.cell(36, 2).alignment = Alignment(wrap_text=True, vertical="top")

заголовок_блока(39, "6. РЕКВИЗИТЫ СПЕЦИАЛЬНОГО СЧЁТА (НЕ МЕНЯЮТСЯ)")
REQ = [
    ("Получатель платежа", "РЕГИОНАЛЬНЫЙ ФОНД КАПИТАЛЬНОГО РЕМОНТА "
                           "МНОГОКВАРТИРНЫХ ДОМОВ ОМСКОЙ ОБЛАСТИ (СПЕЦ. СЧЕТ)"),
    ("Юридический адрес", "644099, г. Омск, ул. Краснофлотская, 24"),
    ("ИНН", "5503239348"),
    ("КПП", "550301001"),
    ("ОГРН", "1027700342890"),
    ("Расчётный счёт (спец. счёт МКД)", "40604810809000000154"),
    ("Банк", "Омский РФ АО «Россельхозбанк»"),
    ("Корреспондентский счёт", "30101810900000000822"),
    ("БИК", "045209822"),
    ("ИНН/КПП банка", "7725114488 / 550502001"),
    ("День срока оплаты", 15),
]
R = {}
for i, (name, value) in enumerate(REQ):
    row = 40 + i
    # Наименование получателя длинное и переносится на три строки.
    src.row_dimensions[row].height = 44 if i == 0 else 30
    n = src.cell(row, 2, name)
    n.font = Font(name=FONT, size=10, bold=True, color=TXT)
    n.fill = PatternFill("solid", fgColor=GREY)
    v = src.cell(row, 3, value)
    v.font = Font(name=FONT, size=10, color=TXT)
    for j in (2, 3, 4):
        src.cell(row, j).border = BOX
        src.cell(row, j).alignment = Alignment(vertical="center", wrap_text=True)
    R[name] = f"'{SRC}'!$C${row}"
src.cell(50, 4, "Единый срок по ч. 1 ст. 155 и ч. 2 ст. 171 ЖК РФ "
                "(ФЗ от 24.06.2025 № 177-ФЗ)").font = Font(
    name=FONT, size=9, italic=True, color="666666")

ГОД = R_ГОД
СРОК_ДЕНЬ = R["День срока оплаты"]

# Лист ввода тоже иногда печатают — вписываем его в страницу, иначе
# при выгрузке всей книги в PDF он расползается на несколько листов.
src.print_area = "$B$1:$F$52"
src.page_setup.orientation = "portrait"
src.page_setup.paperSize = src.PAPERSIZE_A4
src.page_setup.fitToWidth = 1
src.page_setup.fitToHeight = 1
src.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
src.page_margins.left = 0.4
src.page_margins.right = 0.4
src.page_margins.top = 0.4
src.page_margins.bottom = 0.4


def кв(q, col):
    """Ссылка на ячейку строки квартала q (1..4) в таблице по кварталам."""
    return f"'{SRC}'!${col}${30 + q}"


# --------------------------------------------------------------------------
# Скрытый лист ПРОПИСЬ — справочник числительных
# --------------------------------------------------------------------------
words = wb.create_sheet(WORDS)
for i, name in enumerate(
        ["Число", "Прописью (муж.)", "Форма рубля", "Прописью (жен.)",
         "Форма тысячи", "Форма копейки"], start=1):
    words.cell(1, i, name).font = Font(name=FONT, size=9, bold=True)
for n in range(1000):
    row = n + 2
    words.cell(row, 1, n)
    words.cell(row, 2, прописью(n))
    words.cell(row, 3, форма(n, "рубль", "рубля", "рублей"))
    words.cell(row, 4, прописью(n, женский=True))
    words.cell(row, 5, форма(n, "тысяча", "тысячи", "тысяч"))
    words.cell(row, 6, форма(n, "копейка", "копейки", "копеек"))
words.sheet_state = "hidden"

СП_МУЖ = f"'{WORDS}'!$B$2:$B$1001"
СП_РУБ = f"'{WORDS}'!$C$2:$C$1001"
СП_ЖЕН = f"'{WORDS}'!$D$2:$D$1001"
СП_ТЫС = f"'{WORDS}'!$E$2:$E$1001"
СП_КОП = f"'{WORDS}'!$F$2:$F$1001"


def деньги(сумма):
    """Сумма в виде 1 234,56 в любой локали.

    TEXT(...;"# ##0,00") пришлось бы читать по языку Excel: в en-US запятая
    считается разделителем тысяч, и копейки пропадают. Поэтому целая часть
    и копейки собираются вручную.
    """
    S = f"ROUND({сумма},2)"
    I = f"INT({S})"
    K = f"(ROUND({S}*100,0)-{I}*100)"
    T = f"INT({I}/1000)"
    O = f"({I}-{T}*1000)"
    целая = f'IF({T}>0,{T}&" "&TEXT({O},"000"),{O}&"")'
    return f'{целая}&","&TEXT({K},"00")'


def прописью_формула(сумма):
    """Формула «сумма прописью» для произвольного денежного выражения.

    Разбивает сумму на тысячи, сотни и копейки и собирает строку по
    справочнику на листе ПРОПИСЬ — так обходимся без макросов, и книга
    остаётся обычным .xlsx.
    """
    S_ = f"ROUND({сумма},2)"
    R_ = f"INT({S_})"
    K_ = f"(ROUND({S_}*100,0)-{R_}*100)"
    T_ = f"INT({R_}/1000)"
    O_ = f"({R_}-{T_}*1000)"
    текст = (
        f'IF({T_}>0,INDEX({СП_ЖЕН},{T_}+1)&" "&INDEX({СП_ТЫС},{T_}+1)&" ","")'
        f'&IF(AND({O_}=0,{T_}>0),"",INDEX({СП_МУЖ},{O_}+1)&" ")'
        f'&INDEX({СП_РУБ},{O_}+1)&" "&INDEX({СП_ЖЕН},{K_}+1)&" "'
        f'&INDEX({СП_КОП},{K_}+1)'
    )
    return f'UPPER(LEFT({текст},1))&MID({текст},2,300)'


# ==========================================================================
# Квитанция за квартал
# ==========================================================================
def сделать_квитанцию(q, римская, месяцы):
    ws = wb.create_sheet(f"Квитанция {q} кв")
    ws.sheet_view.showGridLines = False
    for col, w in {"A": 1.8, "B": 20.5, "C": 12.5, "D": 15.0, "E": 10.5,
                   "F": 15.0, "G": 12.0, "H": 14.0, "I": 1.8}.items():
        ws.column_dimensions[col].width = w

    период = f'"{римская} квартал "&{ГОД}&" г."'
    кон_месяц = q * 3
    срок = f"DATE({ГОД},{кон_месяц}+1,{СРОК_ДЕНЬ})"

    spacer(ws, 1, 6)
    ws.row_dimensions[2].height = 40
    put(ws, "B2:H2",
        rich(("ПЛАТЁЖНЫЙ ДОКУМЕНТ (КВИТАНЦИЯ)\n", True, 13),
             ("на внесение взноса на капитальный ремонт общего имущества "
              "в многоквартирном доме", True, 9), role="title"),
        role="title", size=13, bold=True, align="center", wrap=True,
        border=BOX_MED)

    ws.row_dimensions[3].height = 20
    put(ws, "B3:E3", f'="Специальный счёт МКД · "&{R_АДРЕС_МКД}',
        role="subtitle", size=9, bold=True, indent=1)
    put(ws, "F3:H3", f'="Расчётный период: "&{период}',
        role="subtitle", size=9, bold=True, align="right", indent=1)
    outline(ws, "B3:H3")
    spacer(ws, 4)

    # --- 1. Получатель платежа
    ws.row_dimensions[5].height = 16
    put(ws, "B5:H5", "1. ПОЛУЧАТЕЛЬ ПЛАТЕЖА — ВЛАДЕЛЕЦ СПЕЦИАЛЬНОГО СЧЁТА",
        role="section", size=10, bold=True, indent=1)
    edge(ws, "B5:H5", bottom=MEDIUM)

    ws.row_dimensions[6].height = 26
    put(ws, "B6", "Получатель платежа", role="label", size=8, bold=True,
        wrap=True, indent=1)
    put(ws, "C6:H6", f'={R["Получатель платежа"]}', role="value", size=9,
        bold=True, wrap=True, indent=1)

    ws.row_dimensions[7].height = 14
    put(ws, "B7", "Юридический адрес", role="label", size=8, bold=True, indent=1)
    put(ws, "C7:H7", f'={R["Юридический адрес"]}', role="value", indent=1)

    ws.row_dimensions[8].height = 14
    put(ws, "B8", "ИНН / КПП", role="label", size=8, bold=True, indent=1)
    put(ws, "C8:D8", f'={R["ИНН"]}&" / "&{R["КПП"]}', role="value", indent=1)
    put(ws, "E8", "ОГРН", role="label", size=8, bold=True, indent=1)
    put(ws, "F8:H8", f'={R["ОГРН"]}', role="value", indent=1)

    ws.row_dimensions[9].height = 16
    put(ws, "B9", "Расчётный счёт", role="label", size=8, bold=True, indent=1)
    put(ws, "C9:H9",
        f'={R["Расчётный счёт (спец. счёт МКД)"]}'
        f'&"   (специальный счёт МКД: "&{R_АДРЕС_МКД}&")"',
        role="value", size=10, bold=True, indent=1)

    ws.row_dimensions[10].height = 14
    put(ws, "B10", "Банк", role="label", size=8, bold=True, indent=1)
    put(ws, "C10:H10", f'={R["Банк"]}', role="value", indent=1)

    ws.row_dimensions[11].height = 14
    put(ws, "B11", "Корр. счёт / БИК", role="label", size=8, bold=True, indent=1)
    put(ws, "C11:D11",
        f'={R["Корреспондентский счёт"]}&" / "&{R["БИК"]}',
        role="value", indent=1)
    put(ws, "E11", "ИНН/КПП банка", role="label", size=8, bold=True, indent=1)
    put(ws, "F11:H11", f'={R["ИНН/КПП банка"]}', role="value", indent=1)
    outline(ws, "B5:H11")
    spacer(ws, 12)

    # --- 2. Плательщик и помещение
    ws.row_dimensions[13].height = 16
    put(ws, "B13:H13", "2. ПЛАТЕЛЬЩИК И ПОМЕЩЕНИЕ", role="section", size=10,
        bold=True, indent=1)
    edge(ws, "B13:H13", bottom=MEDIUM)

    ws.row_dimensions[14].height = 19
    put(ws, "B14", "Лицевой счёт", role="label", size=8, bold=True, indent=1)
    put(ws, "C14", f"={R_ЛС}", role="value", size=11, bold=True, align="center")
    put(ws, "D14", "Квартира №", role="label", size=8, bold=True, indent=1)
    put(ws, "E14", f"={R_КВ}", role="value", size=10, bold=True, align="center")
    put(ws, "F14", "Дата формирования", role="label", size=8, bold=True,
        wrap=True, indent=1)
    put(ws, "G14:H14", f"={кв(q, 'E')}", role="value", size=10, align="center",
        fmt=DATEFMT)

    ws.row_dimensions[15].height = 17
    put(ws, "B15", "Плательщик", role="label", size=8, bold=True, indent=1)
    put(ws, "C15:H15", f"={R_ПЛАТЕЛЬЩИК}", role="value", size=10, bold=True,
        indent=1)

    ws.row_dimensions[16].height = 16
    put(ws, "B16", "Адрес помещения", role="label", size=8, bold=True, indent=1)
    put(ws, "C16:H16", f'={R_АДРЕС_МКД}&", кв. "&{R_КВ}', role="value",
        size=9, indent=1)

    ws.row_dimensions[17].height = 20
    put(ws, "B17", "Площадь помещения, м²", role="label", size=8, bold=True,
        wrap=True, indent=1)
    put(ws, "C17", f"={R_ПЛОЩАДЬ}", role="value", size=10, bold=True,
        align="center", fmt=AREA)
    put(ws, "D17", "Размер взноса, руб./м²", role="label", size=8, bold=True,
        wrap=True, indent=1)
    put(ws, "E17", f"={R_ТАРИФ}", role="value", size=10, bold=True,
        align="center", fmt=MONEY)
    put(ws, "F17", "Период оплаты", role="label", size=8, bold=True, indent=1)
    put(ws, "G17:H17", f"={период}", role="value", size=10, bold=True,
        align="center")
    outline(ws, "B13:H17")
    spacer(ws, 18)

    # --- 3. Расчёт: три месяца квартала, задолженность, итог
    ws.row_dimensions[19].height = 16
    put(ws, "B19:H19", "3. РАСЧЁТ РАЗМЕРА ВЗНОСА И СУММЫ К ОПЛАТЕ",
        role="section", size=10, bold=True, indent=1)
    edge(ws, "B19:H19", bottom=MEDIUM)

    ws.row_dimensions[20].height = 18
    put(ws, "B20:E20", "Вид платежа", role="thead", size=9, bold=True,
        align="center")
    put(ws, "F20:G20", "Расчётный период", role="thead", size=9, bold=True,
        align="center")
    put(ws, "H20", "Сумма, руб.", role="thead", size=9, bold=True,
        align="center")
    edge(ws, "B20:H20", bottom=MEDIUM)

    for i, месяц in enumerate(месяцы):
        row = 21 + i
        ws.row_dimensions[row].height = 16
        put(ws, f"B{row}:E{row}", "Взнос на капитальный ремонт "
                                  "(площадь × размер взноса)",
            role="value", size=9, indent=1)
        put(ws, f"F{row}:G{row}", f'="{месяц} "&{ГОД}&" г."', role="value",
            size=9, align="center")
        put(ws, f"H{row}", f"={R_НАЧ_МЕС}", role="value", size=10, bold=True,
            align="right", fmt=MONEY, indent=1)

    ws.row_dimensions[24].height = 17
    put(ws, "B24:E24", "Итого начислено за квартал", role="subtotal", size=9,
        bold=True, indent=1)
    put(ws, "F24:G24", f"={период}", role="subtotal", size=9, align="center")
    put(ws, "H24", "=ROUND(SUM(H21:H23),2)", role="subtotal", size=10,
        bold=True, align="right", fmt=MONEY, indent=1)

    ws.row_dimensions[25].height = 17
    put(ws, "B25:E25", "Задолженность за предыдущие периоды", role="value",
        size=9, indent=1)
    put(ws, "F25:G25", f'=IF({кв(q, "D")}="","",{кв(q, "D")})', role="value",
        size=9, align="center", wrap=True)
    put(ws, "H25", f"={кв(q, 'C')}", role="value", size=10, bold=True,
        align="right", fmt=MONEY, indent=1)

    ws.row_dimensions[26].height = 28
    put(ws, "B26:G26", "ИТОГО К ОПЛАТЕ", role="total", size=14, bold=True,
        indent=1)
    put(ws, "H26", "=ROUND(H24+H25,2)", role="totalsum", size=16, bold=True,
        align="right", fmt=MONEY, border=BOX_MED, indent=1)
    edge(ws, "B26:H26", top=MEDIUM)
    outline(ws, "B19:H26")
    spacer(ws, 27)

    # --- 4. Справочная информация
    ws.row_dimensions[28].height = 16
    put(ws, "B28:H28",
        "4. СПРАВОЧНАЯ ИНФОРМАЦИЯ ПО СПЕЦИАЛЬНОМУ СЧЁТУ (ч. 7 ст. 177 ЖК РФ)",
        role="section", size=10, bold=True, indent=1)
    edge(ws, "B28:H28", bottom=MEDIUM)

    ws.row_dimensions[29].height = 15
    put(ws, "B29:F29",
        f'="Поступило оплат по лицевому счёту с начала "&{ГОД}&" года, руб."',
        role="value", size=9, indent=1)
    put(ws, "G29:H29", f'=IF({кв(q, "F")}="","—",{кв(q, "F")})', role="value",
        size=10, bold=True, align="right", fmt=MONEY, indent=1)

    # Остатка средств на счёте здесь нет: квитанция выставляется раз
    # в квартал, и к моменту оплаты цифра успевает устареть.
    outline(ws, "B28:H29")
    spacer(ws, 30)

    # --- 5. Порядок оплаты
    ws.row_dimensions[31].height = 16
    put(ws, "B31:H31", "5. ПОРЯДОК ОПЛАТЫ", role="section", size=10, bold=True,
        indent=1)
    edge(ws, "B31:H31", bottom=MEDIUM)

    ws.row_dimensions[32].height = 14
    put(ws, "B32:F32", "1) без комиссии — в отделениях АО «Россельхозбанк» "
                       "(банк, в котором открыт специальный счёт дома);",
        role="value", size=9, wrap=True, indent=1)
    ws.row_dimensions[33].height = 26
    put(ws, "B33:F33", rich(
        ("2) по тарифам банка — ", False),
        ("только по номеру расчётного счёта", True),
        (", указанного в разделе 1, в отделениях и мобильных приложениях "
         "ПАО Сбербанк, АО «АЛЬФА-БАНК», Банка ВТБ (ПАО), АО «ТБанк», "
         "а также любого другого банка;", False)),
        role="value", size=9, wrap=True, indent=1)
    ws.row_dimensions[34].height = 14
    put(ws, "B34:F34",
        "3) в мобильном приложении любого банка — по QR-коду "
        "(ГОСТ Р 56042-2014)." if QR_ВКЛЮЧЁН else None,
        role="value", size=9, wrap=True, indent=1)

    ws.row_dimensions[35].height = 14
    put(ws, "B35:F35", "Назначение платежа:", role="label", size=8, bold=True,
        indent=1)
    ws.row_dimensions[36].height = 30
    put(ws, "B36:F36",
        f'="Взнос на капитальный ремонт, л/с № "&{R_ЛС}&", кв. № "&{R_КВ}'
        f'&", за "&{период}',
        role="value", size=9, wrap=True, indent=1)
    ws.row_dimensions[37].height = 26
    put(ws, "B37:F37",
        f'="Срок оплаты: до "&{СРОК_ДЕНЬ}&" числа месяца, следующего за '
        f'расчётным (за "&{период}&" — до "&{ru_date(срок)}&")."'
        f'&CHAR(10)&"Основание: ч. 1 ст. 155, ч. 2 ст. 171 ЖК РФ."',
        role="note", size=9, bold=True, align="center", wrap=True)

    put(ws, "G32:H37", "QR-код\nформируется\nмакросом" if QR_ВКЛЮЧЁН else None,
        role="qr", size=9, bold=True, align="center", wrap=True)
    outline(ws, "B31:H37")
    spacer(ws, 38)

    # --- Предупреждение
    ws.row_dimensions[39].height = 32
    put(ws, "B39:H39",
        f'="ВНИМАНИЕ! ПЛАТИТЕ ТОЛЬКО ПО НОМЕРУ РАСЧЁТНОГО СЧЁТА "'
        f'&{R["Расчётный счёт (спец. счёт МКД)"]}'
        f'&" — ЭТО СПЕЦИАЛЬНЫЙ СЧЁТ ВАШЕГО ДОМА"',
        role="total", size=11, bold=True, align="center", wrap=True,
        border=BOX_MED)

    ws.row_dimensions[40].height = 44
    put(ws, "B40:H40",
        f'="В отделении банка и в мобильном приложении во вкладках ищите "'
        f'&"«РФКР МКД_капремонт, оплата по расчётному счёту» и указывайте '
        f'номер расчётного счёта, приведённый выше. Оплата через общий поиск '
        f'«Капитальный ремонт» уходит на общий счёт Регионального фонда '
        f'капитального ремонта и на счёт вашего дома не поступает."'
        f'&CHAR(10)&"Лицевой счёт № "&{R_ЛС}&" при оплате НЕ вводится — '
        f'он указан справочно, только для учёта начислений."',
        role="note", size=9, align="center", wrap=True)
    spacer(ws, 41, 6)

    ws.row_dimensions[42].height = 24
    put(ws, "B42:D42", "Подпись плательщика  ______________________",
        role="plain", size=9, align="center", border=None)
    put(ws, "E42:F42", "Кассир  ______________", role="plain", size=9,
        align="center", border=None)
    put(ws, "G42:H42", "Дата  ____________", role="plain", size=9,
        align="center", border=None)

    ws.row_dimensions[43].height = 22
    put(ws, "B43:H43",
        f'="Начисление за "&{период}&"    По вопросам начислений обращайтесь '
        f'к председателю совета дома, тел. "&{R_ПРЕД_ТЕЛ}&"."',
        role="value", size=8, italic=True, align="center", wrap=True)

    ws.print_area = "$A$1:$I$43"
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_margins.left = 0.24
    ws.page_margins.right = 0.24
    ws.page_margins.top = 0.2
    ws.page_margins.bottom = 0.2
    ws.print_options.horizontalCentered = True
    return ws


# ==========================================================================
# Сопроводительное письмо за квартал
# ==========================================================================
def сделать_письмо(q, римская, месяцы):
    ws = wb.create_sheet(f"Письмо {q} кв")
    ws.sheet_view.showGridLines = False
    # Ширина взята с запасом: 84 знака ≈ 16,2 см при доступных 18,5 см
    # (поля 1,5 см слева и 1 см справа). Запас нужен потому, что Excel
    # пересчитывает ширину колонок под шрифт книги по умолчанию, и подгонка
    # впритык у него выходила на вторую страницу.
    for col, w in {"A": 0.8, "B": 20.0, "C": 16.0, "D": 16.0, "E": 16.0,
                   "F": 16.0, "G": 0.8}.items():
        ws.column_dimensions[col].width = w

    период = f'"{римская} квартал "&{ГОД}&" г."'
    # «с января по март»: первый месяц в родительном падеже, второй —
    # в винительном, который для этих слов совпадает с именительным.
    с_месяца = РОДИТ[месяцы[0]]
    по_месяц = месяцы[2]
    начислено = f"ROUND({R_НАЧ_МЕС}*3,2)"
    долг = кв(q, "C")
    всего = f"ROUND({начислено}+{долг},2)"

    def строка(row, ref, value, *, size=11, bold=False, align="left",
               wrap=True, height=16, italic=False):
        ws.row_dimensions[row].height = height
        put(ws, ref, value, role="plain", size=size, bold=bold, italic=italic,
            align=align, valign="top", wrap=wrap, border=None, indent=0)

    # --- Шапка: адресат и отправитель, прижаты вправо
    строка(1, "D1:F1", f"=\"В \"&{R_АДРЕСАТ_ОРГ}", size=11, bold=True,
           height=32)
    строка(2, "D2:F2",
           f'=IF({R_АДРЕСАТ_ФИО}="","",{R_АДРЕСАТ_ДОЛЖН}&" "&{R_АДРЕСАТ_ФИО})',
           size=11, bold=True, height=16)
    строка(3, "D3:F3",
           f'="от Председателя МКД "&{R_МКД_КРАТКО}&", "&{R_ПРЕД_ФИО_Р}',
           size=11, height=32)
    строка(4, "D4:F4", f'="проживающей по адресу: "&{R_ПРЕД_АДРЕС}',
           size=11, height=32)
    строка(5, "D5:F5", f'="Конт. тел.: "&{R_ПРЕД_ТЕЛ}', size=11, height=16)
    строка(6, "D6:F6", f'="Эл. почта: "&{R_ПРЕД_ПОЧТА}', size=11, height=16)
    spacer(ws, 7, 18)

    # --- Тело письма
    строка(8, "B8:F8",
           f'="В связи с тем, что на балансе департамента числится кв. № "'
           f'&{R_КВ}&" по адресу: "&{R_АДРЕС_МКД}&", сообщаю Вам '
           f'о необходимости оплатить "&{деньги(всего)}&" руб., '
           f'в том числе:"',
           size=11, height=54)
    spacer(ws, 9, 8)

    строка(10, "B10:F10",
           f'="— текущий платёж за период с {с_месяца} по {по_месяц} "&{ГОД}'
           f'&" года ("&{период}&") в размере "'
           f'&{деньги(начислено)}&" рублей"',
           size=11, height=38)
    строка(11, "B11:F11", f'="("&{прописью_формула(начислено)}&")."',
           size=11, italic=True, height=18)
    spacer(ws, 12, 6)

    строка(13, "B13:F13",
           f'=IF({долг}=0,"— задолженности за предыдущие периоды нет.",'
           f'"— задолженность "&IF({кв(q, "D")}="","за предыдущие периоды",'
           f'{кв(q, "D")})&" в размере "&{деньги(долг)}&" рублей")',
           size=11, height=32)
    строка(14, "B14:F14",
           f'=IF({долг}=0,"","("&{прописью_формула(долг)}&").")',
           size=11, italic=True, height=18)
    spacer(ws, 15, 10)

    строка(16, "B16:F16",
           f'="Для сведения и сверки оплат направляю акт взаимных расчётов '
           f'по взносам на капитальный ремонт по квартире № "&{R_КВ}'
           f'&" с учётом всех поступивших платежей на специальный счёт МКД "'
           f'&{R_АДРЕС_МКД}&" (р/счёт "&{R["Расчётный счёт (спец. счёт МКД)"]}'
           f'&") по состоянию расчётов на "&{ru_date(кв(q, "E"))}'
           f'&" и с учётом начислений по "&"{месяцы[2]} "&{ГОД}'
           f'&" года включительно."',
           size=11, height=90)
    spacer(ws, 17, 10)

    строка(18, "B18:F18",
           f'="В случае возникновения дополнительных вопросов прошу связаться '
           f'со мной по электронной почте "&{R_ПРЕД_ПОЧТА}&" или по телефону "'
           f'&{R_ПРЕД_ТЕЛ}&"."',
           size=11, height=54)
    spacer(ws, 19, 14)

    строка(20, "B20:F20", "ПРИЛОЖЕНИЯ:", size=11, bold=True, height=20)
    строка(21, "B21:F21",
           f'="1) Акт взаимных расчётов по состоянию на "'
           f'&{ru_date(кв(q, "E"))}&" — один экземпляр на 1 л."',
           size=11, height=18)
    строка(22, "B22:F22",
           f'="2) Квитанция для оплаты за "&{период}&" — один экземпляр на 1 л."',
           size=11, height=18)
    spacer(ws, 23, 26)

    строка(24, "B24:C24", '="«______» ______________ "&' + ГОД + '&" г."',
           size=11, height=20)
    spacer(ws, 25, 16)

    строка(26, "B26:C26", "Председатель", size=11, height=16)
    строка(27, "B27:C27", f'="МКД "&{R_МКД_КРАТКО}', size=11, height=16)
    строка(27, "D27:F27", f'="___________________  /"&{R_ПРЕД_ФИО_К}&"/"',
           size=11, align="right", height=16)

    ws.print_area = "$B$1:$F$27"
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.page_margins.left = 0.59   # 1,5 см
    ws.page_margins.right = 0.39  # 1 см
    ws.page_margins.top = 0.51
    ws.page_margins.bottom = 0.51
    return ws


for q, римская, месяцы in КВАРТАЛЫ:
    сделать_квитанцию(q, римская, месяцы)
for q, римская, месяцы in КВАРТАЛЫ:
    сделать_письмо(q, римская, месяцы)

# --------------------------------------------------------------------------
# ИНСТРУКЦИЯ
# --------------------------------------------------------------------------
doc = wb.create_sheet(HELP)
doc.sheet_view.showGridLines = False
LINES = [
    ("h", "КВАРТАЛЬНЫЕ КВИТАНЦИИ И ПИСЬМА — КАК ПОЛЬЗОВАТЬСЯ"),
    ("", ""),
    ("s", "1. Где вводить данные"),
    ("t", "Всё вводится на листе «ИСХОДНЫЕ ДАННЫЕ», в жёлтых ячейках. "
          "Остальные девять листов — расчётные: они читают эти значения "
          "формулами и пересчитываются сами."),
    ("t", "Ежегодно меняется только тариф (блок 1). Поменяли размер взноса "
          "и год — все четыре квитанции и все четыре письма обновились."),
    ("t", "Начисление за месяц по умолчанию считается как площадь × тариф. "
          "Если сумму нужно задать вручную, замените в ячейке формулу числом."),
    ("", ""),
    ("s", "2. Задолженность по кварталам"),
    ("t", "Блок 5 листа «ИСХОДНЫЕ ДАННЫЕ» — таблица на четыре строки. "
          "Для каждого квартала укажите сумму задолженности, её описание "
          "(оно попадёт и в квитанцию, и в письмо) и дату формирования."),
    ("t", "Если задолженности нет, поставьте 0: в письме вместо строки "
          "о долге напечатается «задолженности за предыдущие периоды нет», "
          "а в квитанции строка останется с нулём."),
    ("", ""),
    ("s", "3. Сопроводительное письмо"),
    ("t", "Суммы, периоды, даты и приложения подтягиваются автоматически. "
          "Сумма прописью считается формулами по скрытому листу ПРОПИСЬ — "
          "макросы для этого не нужны, книга остаётся обычным .xlsx."),
    ("t", "Адресат письма — блок 4. Должность и ФИО руководителя правятся "
          "здесь; при смене директора достаточно поменять их один раз. "
          "Если ФИО оставить пустым, строка с ним не напечатается."),
    ("", ""),
    ("s", "4. Печать"),
    ("t", "Каждый лист настроен на одну страницу А4. Квитанции — книжная "
          "ориентация, поля 6 мм; письма — стандартные поля 20/15 мм."),
    ("t", "Книга сохранена в чёрно-белом виде: заливок нет, акценты сделаны "
          "кеглем, полужирным и рамками. Цветной вариант для отправки по "
          "электронной почте лежит отдельным файлом."),
    ("", ""),
    ("s", "5. Что проверить"),
    ("t", "• Тариф 15,30 руб./м² и площадь 52,8 м² взяты из вашего образца "
          "за I квартал 2026 года. Начисление выходит 807,84 руб. в месяц "
          "и 2 423,52 руб. за квартал — совпадает с образцом."),
    ("t", "• Задолженность 4 042,38 руб. проставлена только для I квартала. "
          "Для остальных кварталов стоят нули — заполните их по факту."),
    ("t", "• В образце письма период января–марта 2026 года был подписан "
          "как «I квартал 2025 г.» — в шаблоне это исправлено на 2026 год."),
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
doc.column_dimensions["A"].width = 20
for col in "BCDEF":
    doc.column_dimensions[col].width = 13
doc.print_area = f"$A$1:$F${r - 1}"
doc.page_setup.orientation = "portrait"
doc.page_setup.paperSize = doc.PAPERSIZE_A4
doc.page_setup.fitToWidth = 1
doc.page_setup.fitToHeight = 1
doc.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
doc.page_margins.left = 0.4
doc.page_margins.right = 0.4
doc.page_margins.top = 0.4
doc.page_margins.bottom = 0.4

# --------------------------------------------------------------------------
NAMES = {
    "ИД_ГОД": f"'{SRC}'!$C$5",
    "ИД_ПЛОЩАДЬ": f"'{SRC}'!$C$6",
    "ИД_ТАРИФ": f"'{SRC}'!$C$7",
    "ИД_НАЧИСЛЕНО_МЕС": f"'{SRC}'!$C$8",
    "ИД_ЛС": f"'{SRC}'!$C$11",
    "ИД_КВАРТИРА": f"'{SRC}'!$C$12",
    "ИД_КВАРТАЛЫ": f"'{SRC}'!$B$31:$F$34",
}
for name, ref in NAMES.items():
    wb.defined_names.add(DefinedName(name, attr_text=ref))

wb.active = 0
OUTDIR.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print(f"Готово: {OUT}")
