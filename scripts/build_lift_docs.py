# -*- coding: utf-8 -*-
"""
Генератор единого Excel-файла с пакетом документов для подрядной организации
по монтажу лифтов.

Листы: Параметры -> Смета -> Спецификация -> КП -> КС-2 -> КС-3 -> Счёт ->
Сопроводительное письмо -> Договор.

Все реквизиты, номера и даты вводятся ОДИН раз на листе «Параметры»;
остальные листы получают их формулами, поэтому меняются синхронно.
Денежные итоги идут цепочкой: Смета/Спецификация -> КП -> КС-2 -> КС-3 -> Счёт -> Договор.
"""
import datetime as dt

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

# ----------------------------------------------------------------------------
# Стили
# ----------------------------------------------------------------------------
F = "Arial"
FONT = Font(name=F, size=10)
FONT_B = Font(name=F, size=10, bold=True)
FONT_TITLE = Font(name=F, size=14, bold=True)
FONT_H = Font(name=F, size=11, bold=True)
FONT_SMALL = Font(name=F, size=8, italic=True, color="808080")
FONT_INPUT = Font(name=F, size=10, color="0000FF")          # ввод данных
FONT_LINK = Font(name=F, size=10, color="008000")           # ссылка на другой лист

FILL_INPUT = PatternFill("solid", fgColor="FFF2CC")         # жёлтая заливка — редактируемые ячейки
FILL_HEAD = PatternFill("solid", fgColor="D9E1F2")          # шапки таблиц
FILL_TOTAL = PatternFill("solid", fgColor="E2EFDA")         # итоговые строки
FILL_SECT = PatternFill("solid", fgColor="BDD7EE")          # заголовки разделов

THIN = Side(style="thin", color="000000")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

AL_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
AL_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
AL_R = Alignment(horizontal="right", vertical="center")
AL_TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)
AL_JUST = Alignment(horizontal="justify", vertical="top", wrap_text=True)

NUM = "#,##0.00"
QTY = "#,##0.##"
PCT = "0%"
PCT1 = "0.0%"
DATE = "DD.MM.YYYY"


def put(ws, row, col, value, font=FONT, fmt=None, align=None, fill=None, border=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    if fmt:
        c.number_format = fmt
    if align:
        c.alignment = align
    if fill:
        c.fill = fill
    if border:
        c.border = border
    return c


def merge(ws, row, c1, c2, row2=None):
    ws.merge_cells(start_row=row, start_column=c1, end_row=row2 or row, end_column=c2)


def para(ws, row, value, height=None, cols=(1, 7), font=FONT, align=AL_JUST):
    """Абзац текста, объединённый по ширине листа."""
    merge(ws, row, cols[0], cols[1])
    put(ws, row, cols[0], value, font=font, align=align)
    if height:
        ws.row_dimensions[row].height = height


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def page(ws, landscape=False):
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


wb = Workbook()

# ----------------------------------------------------------------------------
# Лист «Параметры» — единый источник данных
# ----------------------------------------------------------------------------
ws = wb.active
ws.title = "Параметры"
widths(ws, {"A": 44, "B": 58, "C": 40})

P = {}  # ключ -> абсолютная ссылка на ячейку значений


def ref(key):
    return P[key]


rows = [
    # (тип, ключ, подпись, значение, формат)
    ("title", None, "ПАРАМЕТРЫ ПАКЕТА ДОКУМЕНТОВ (единый источник данных)", None, None),
    ("note", None, "Жёлтые ячейки с синим шрифтом — исходные данные: заполняйте/меняйте только их. "
                   "Все остальные листы обновятся автоматически.", None, None),
    ("gap",) * 5,
    ("sect", None, "1. ДОГОВОР", None, None),
    ("in", "dog_num", "Номер договора", "ПД-14/2026", None),
    ("in", "dog_date", "Дата договора", dt.date(2026, 7, 17), DATE),
    ("in", "dog_city", "Место заключения", "г. Москва", None),
    ("in", "work_start", "Дата начала работ", dt.date(2026, 8, 1), DATE),
    ("in", "work_end", "Дата окончания работ", dt.date(2026, 11, 30), DATE),
    ("in", "advance", "Аванс, % от цены договора", 0.30, PCT),
    ("in", "warranty", "Гарантийный срок, мес.", 24, "0"),
    ("in", "nds", "Ставка НДС", 0.20, PCT),
    ("in", "penalty", "Неустойка за просрочку, % за каждый день", 0.001, PCT1),
    ("gap",) * 5,
    ("sect", None, "2. ЗАКАЗЧИК", None, None),
    ("in", "z_full", "Полное наименование",
     "Общество с ограниченной ответственностью «Специализированный застройщик «Новый квартал»", None),
    ("in", "z_short", "Краткое наименование", "ООО «СЗ «Новый квартал»", None),
    ("in", "z_inn", "ИНН", "7701234567", None),
    ("in", "z_kpp", "КПП", "770101001", None),
    ("in", "z_ogrn", "ОГРН", "1157746123456", None),
    ("in", "z_addr", "Юридический адрес", "101000, г. Москва, ул. Мясницкая, д. 10, офис 5", None),
    ("in", "z_bank", "Банк", "ПАО «Сбербанк России», г. Москва", None),
    ("in", "z_bik", "БИК", "044525225", None),
    ("in", "z_rs", "Расчётный счёт", "40702810438000012345", None),
    ("in", "z_ks", "Корреспондентский счёт", "30101810400000000225", None),
    ("in", "z_pos", "Должность руководителя", "Генеральный директор", None),
    ("in", "z_fio", "ФИО руководителя (полностью)", "Иванов Иван Иванович", None),
    ("in", "z_fio_short", "ФИО руководителя (кратко)", "Иванов И.И.", None),
    ("in", "z_basis", "Действует на основании (род. падеж)", "Устава", None),
    ("in", "z_pos_gen", "Должность руководителя (род. падеж)", "Генерального директора", None),
    ("in", "z_fio_gen", "ФИО руководителя (род. падеж)", "Иванова Ивана Ивановича", None),
    ("in", "z_pos_dat", "Должность руководителя (дат. падеж, для писем)", "Генеральному директору", None),
    ("in", "z_fio_dat", "ФИО руководителя (дат. падеж)", "Иванову И.И.", None),
    ("in", "z_name_patr", "Имя и отчество руководителя (для обращения)", "Иван Иванович", None),
    ("in", "z_phone", "Телефон", "+7 (495) 123-45-67", None),
    ("in", "z_email", "E-mail", "info@nk-dev.ru", None),
    ("gap",) * 5,
    ("sect", None, "3. ПОДРЯДЧИК", None, None),
    ("in", "p_full", "Полное наименование",
     "Общество с ограниченной ответственностью «ЛифтМонтажСервис»", None),
    ("in", "p_short", "Краткое наименование", "ООО «ЛифтМонтажСервис»", None),
    ("in", "p_inn", "ИНН", "7725678901", None),
    ("in", "p_kpp", "КПП", "772501001", None),
    ("in", "p_ogrn", "ОГРН", "1187746654321", None),
    ("in", "p_addr", "Юридический адрес", "115280, г. Москва, ул. Ленинская Слобода, д. 19, стр. 2", None),
    ("in", "p_bank", "Банк", "АО «Альфа-Банк», г. Москва", None),
    ("in", "p_bik", "БИК", "044525593", None),
    ("in", "p_rs", "Расчётный счёт", "40702810102300067890", None),
    ("in", "p_ks", "Корреспондентский счёт", "30101810200000000593", None),
    ("in", "p_pos", "Должность руководителя", "Генеральный директор", None),
    ("in", "p_fio", "ФИО руководителя (полностью)", "Петров Пётр Петрович", None),
    ("in", "p_fio_short", "ФИО руководителя (кратко)", "Петров П.П.", None),
    ("in", "p_basis", "Действует на основании (род. падеж)", "Устава", None),
    ("in", "p_pos_gen", "Должность руководителя (род. падеж)", "Генерального директора", None),
    ("in", "p_fio_gen", "ФИО руководителя (род. падеж)", "Петрова Петра Петровича", None),
    ("in", "p_buh", "Главный бухгалтер (для счёта)", "Сидорова А.В.", None),
    ("in", "p_phone", "Телефон", "+7 (495) 987-65-43", None),
    ("in", "p_email", "E-mail", "office@liftmontag.ru", None),
    ("gap",) * 5,
    ("sect", None, "4. ОБЪЕКТ", None, None),
    ("in", "obj_name", "Наименование объекта", "Многоквартирный жилой дом, корпус 3", None),
    ("in", "obj_addr", "Адрес объекта", "г. Москва, ул. Полярная, д. 25, корп. 3", None),
    ("in", "obj_lifts", "Количество лифтов, шт.", 2, "0"),
    ("in", "obj_type", "Тип оборудования",
     "лифт пассажирский, г/п 630 кг, скорость 1,0 м/с, 9 остановок", None),
    ("gap",) * 5,
    ("sect", None, "5. НОМЕРА И ДАТЫ ДОКУМЕНТОВ", None, None),
    ("in", "kp_num", "Коммерческое предложение: номер", "14-КП", None),
    ("in", "kp_date", "Коммерческое предложение: дата", dt.date(2026, 7, 17), DATE),
    ("in", "ks2_num", "Акт КС-2: номер", "1", None),
    ("in", "ks2_date", "Акт КС-2: дата", dt.date(2026, 11, 30), DATE),
    ("in", "period_from", "Отчётный период: с", dt.date(2026, 8, 1), DATE),
    ("in", "period_to", "Отчётный период: по", dt.date(2026, 11, 30), DATE),
    ("in", "ks3_num", "Справка КС-3: номер", "1", None),
    ("in", "ks3_date", "Справка КС-3: дата", dt.date(2026, 11, 30), DATE),
    ("in", "inv_num", "Счёт: номер", "118", None),
    ("in", "inv_date", "Счёт: дата", dt.date(2026, 11, 30), DATE),
    ("in", "let_num", "Сопроводительное письмо: исх. №", "245", None),
    ("in", "let_date", "Сопроводительное письмо: дата", dt.date(2026, 12, 1), DATE),
    ("gap",) * 5,
    ("sect", None, "6. ЦЕНА ДОГОВОРА (контроль)", None, None),
    ("link", "total_calc", "Цена договора с НДС, руб. (расчёт — не менять)", "='КП'!E14", NUM),
    ("in", "total_words", "Цена договора прописью (обновите вручную при изменении цены)",
     "Одиннадцать миллионов семьсот шестьдесят две тысячи четыреста рублей 00 копеек", None),
]

r = 0
for row_spec in rows:
    r += 1
    kind = row_spec[0]
    if kind == "gap":
        continue
    if kind == "title":
        merge(ws, r, 1, 3)
        put(ws, r, 1, row_spec[2], font=FONT_TITLE, align=AL_L)
        ws.row_dimensions[r].height = 22
        continue
    if kind == "note":
        merge(ws, r, 1, 3)
        put(ws, r, 1, row_spec[2], font=Font(name=F, size=9, italic=True, color="808080"), align=AL_L)
        ws.row_dimensions[r].height = 26
        continue
    if kind == "sect":
        merge(ws, r, 1, 3)
        put(ws, r, 1, row_spec[2], font=FONT_H, fill=FILL_SECT, align=AL_L)
        continue
    _, key, label, value, fmt = row_spec
    put(ws, r, 1, label, font=FONT, align=AL_L, border=BORDER)
    if kind == "in":
        put(ws, r, 2, value, font=FONT_INPUT, fmt=fmt, align=AL_L, fill=FILL_INPUT, border=BORDER)
    else:  # link — формула, не редактировать
        put(ws, r, 2, value, font=FONT_LINK, fmt=fmt, align=AL_L, border=BORDER)
    P[key] = f"'Параметры'!$B${r}"

cmt = Comment("Сумма прописью не пересчитывается формулой. При изменении сметы или спецификации "
              "сверьте с ячейкой «Цена договора с НДС (расчёт)» выше и обновите текст.",
              "Параметры")
ws[P["total_words"].split("!")[1].replace("$", "")].comment = cmt
ws.freeze_panes = "A3"
page(ws)

# ----------------------------------------------------------------------------
# Лист «Смета» — мастер позиций работ
# ----------------------------------------------------------------------------
ws = wb.create_sheet("Смета")
widths(ws, {"A": 6, "B": 62, "C": 10, "D": 10, "E": 16, "F": 18})

merge(ws, 1, 1, 6)
put(ws, 1, 1, f'="ЛОКАЛЬНАЯ СМЕТА № 1 к договору подряда № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)
merge(ws, 2, 1, 6)
put(ws, 2, 1, f'="Объект: "&{ref("obj_name")}&", "&{ref("obj_addr")}', font=FONT, align=AL_C)

hdr_row = 4
headers = ["№", "Наименование работ", "Ед. изм.", "Кол-во", "Цена за ед., руб. без НДС", "Стоимость, руб. без НДС"]
for i, h in enumerate(headers, 1):
    put(ws, hdr_row, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

works = [
    ("Демонтаж существующего лифтового оборудования", "шт.", 2, 180000),
    ("Монтаж направляющих кабины и противовеса", "компл.", 2, 220000),
    ("Монтаж лебёдки и рамы главного привода", "шт.", 2, 150000),
    ("Монтаж кабины лифта", "шт.", 2, 260000),
    ("Монтаж противовеса", "шт.", 2, 90000),
    ("Монтаж дверей шахты", "шт.", 18, 25000),
    ("Электромонтажные работы (станция управления, освещение и разводка по шахте)", "компл.", 2, 190000),
    ("Монтаж обрамлений дверных проёмов", "шт.", 18, 12000),
    ("Пусконаладочные работы", "компл.", 2, 160000),
    ("Полное техническое освидетельствование и сдача лифтов в эксплуатацию", "компл.", 2, 85000),
]
SM_FIRST = hdr_row + 1
for i, (name, unit, qty, price) in enumerate(works):
    r = SM_FIRST + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, name, font=FONT_INPUT, align=AL_L, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 3, unit, font=FONT_INPUT, align=AL_C, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 4, qty, font=FONT_INPUT, fmt=QTY, align=AL_C, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 5, price, font=FONT_INPUT, fmt=NUM, align=AL_R, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 6, f"=D{r}*E{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)
SM_LAST = SM_FIRST + len(works) - 1

r = SM_LAST + 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Итого без НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=SUM(F{SM_FIRST}:F{SM_LAST})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SM_NET = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, f'="НДС ("&TEXT({ref("nds")},"0%")&")"', font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{SM_NET}*{ref('nds')}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SM_VAT = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Всего с НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{SM_NET}+F{SM_VAT}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SM_GROSS = r

para(ws, SM_GROSS + 2,
     "Жёлтые ячейки — редактируемые данные сметы. При добавлении строк вставляйте их ВНУТРЬ таблицы "
     "(между первой и последней позицией) и добавляйте зеркальную строку в акт КС-2.",
     height=26, cols=(1, 6), font=FONT_SMALL, align=AL_TOP)

SMETA = {
    "net": f"'Смета'!$F${SM_NET}",
    "vat": f"'Смета'!$F${SM_VAT}",
    "gross": f"'Смета'!$F${SM_GROSS}",
    "first": SM_FIRST,
    "last": SM_LAST,
}
page(ws)

# ----------------------------------------------------------------------------
# Лист «Спецификация» — материалы и оборудование
# ----------------------------------------------------------------------------
ws = wb.create_sheet("Спецификация")
widths(ws, {"A": 6, "B": 62, "C": 10, "D": 10, "E": 16, "F": 18})

merge(ws, 1, 1, 6)
put(ws, 1, 1, f'="СПЕЦИФИКАЦИЯ № 1 (оборудование и материалы) к договору подряда № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)
merge(ws, 2, 1, 6)
put(ws, 2, 1, f'="Объект: "&{ref("obj_name")}&", "&{ref("obj_addr")}', font=FONT, align=AL_C)

hdr_row = 4
headers = ["№", "Наименование оборудования / материалов", "Ед. изм.", "Кол-во", "Цена за ед., руб. без НДС", "Стоимость, руб. без НДС"]
for i, h in enumerate(headers, 1):
    put(ws, hdr_row, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

materials = [
    ("Лифт пассажирский, г/п 630 кг, скорость 1,0 м/с, 9 остановок (комплект поставки завода-изготовителя)", "шт.", 2, 2950000),
    ("Обрамление дверного портала из нержавеющей стали", "компл.", 18, 15000),
    ("Кабельная продукция (силовые и слаботочные линии, комплект на шахту)", "компл.", 2, 45000),
    ("Металлоконструкции для крепления направляющих", "компл.", 2, 60000),
    ("Крепёжные изделия и расходные материалы", "компл.", 2, 25000),
    ("Светильники освещения шахты", "шт.", 20, 1800),
]
SP_FIRST = hdr_row + 1
for i, (name, unit, qty, price) in enumerate(materials):
    r = SP_FIRST + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, name, font=FONT_INPUT, align=AL_L, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 3, unit, font=FONT_INPUT, align=AL_C, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 4, qty, font=FONT_INPUT, fmt=QTY, align=AL_C, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 5, price, font=FONT_INPUT, fmt=NUM, align=AL_R, fill=FILL_INPUT, border=BORDER)
    put(ws, r, 6, f"=D{r}*E{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)
SP_LAST = SP_FIRST + len(materials) - 1

r = SP_LAST + 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Итого без НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=SUM(F{SP_FIRST}:F{SP_LAST})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SP_NET = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, f'="НДС ("&TEXT({ref("nds")},"0%")&")"', font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{SP_NET}*{ref('nds')}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SP_VAT = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Всего с НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{SP_NET}+F{SP_VAT}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
SP_GROSS = r

SPEC = {
    "net": f"'Спецификация'!$F${SP_NET}",
    "vat": f"'Спецификация'!$F${SP_VAT}",
    "gross": f"'Спецификация'!$F${SP_GROSS}",
}
page(ws)

# ----------------------------------------------------------------------------
# Лист «КП» — коммерческое предложение
# ----------------------------------------------------------------------------
ws = wb.create_sheet("КП")
widths(ws, {"A": 6, "B": 58, "C": 18, "D": 18, "E": 18})

put(ws, 1, 1, f'={ref("p_short")}', font=FONT_B)
merge(ws, 1, 1, 5)
para(ws, 2, f'={ref("p_addr")}&", тел. "&{ref("p_phone")}&", "&{ref("p_email")}', cols=(1, 5), font=FONT, align=AL_L)
para(ws, 3, f'="ИНН "&{ref("p_inn")}&" / КПП "&{ref("p_kpp")}&", ОГРН "&{ref("p_ogrn")}', cols=(1, 5), font=FONT, align=AL_L)

merge(ws, 5, 1, 5)
put(ws, 5, 1, f'="КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ № "&{ref("kp_num")}&" от "&TEXT({ref("kp_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)

para(ws, 7, f'="Кому: "&{ref("z_short")}&", "&{ref("z_pos")}&" "&{ref("z_fio_short")}', cols=(1, 5), font=FONT, align=AL_L)
para(ws, 9,
     f'={ref("p_short")}&" предлагает выполнить комплекс работ по монтажу и пусконаладке лифтового '
     f'оборудования ("&{ref("obj_type")}&", "&{ref("obj_lifts")}&" шт.) на объекте: "&{ref("obj_name")}&" '
     f'по адресу: "&{ref("obj_addr")}&"."',
     height=42, cols=(1, 5))

hdr = 11
for i, h in enumerate(["№", "Наименование", "Стоимость без НДС, руб.", None, "Стоимость с НДС, руб."], 1):
    if h is not None:
        put(ws, hdr, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)
put(ws, hdr, 4, f'="НДС ("&TEXT({ref("nds")},"0%")&"), руб."', font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

kp_lines = [
    ("Строительно-монтажные и пусконаладочные работы (лист «Смета»)", SMETA),
    ("Лифтовое оборудование и материалы (лист «Спецификация»)", SPEC),
]
for i, (name, src) in enumerate(kp_lines):
    r = hdr + 1 + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, name, font=FONT, align=AL_L, border=BORDER)
    put(ws, r, 3, f'={src["net"]}', font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 4, f'={src["vat"]}', font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 5, f'={src["gross"]}', font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
KP_TOTAL = hdr + 3  # строка 14... вычислим фактически
r = hdr + len(kp_lines) + 1
merge(ws, r, 1, 2)
put(ws, r, 1, "ИТОГО", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
for col in (3, 4, 5):
    L = get_column_letter(col)
    put(ws, r, col, f"=SUM({L}{hdr + 1}:{L}{r - 1})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KP_TOTAL = r  # 'КП'!E{r} — цена договора с НДС; C{r} — без НДС; D{r} — НДС

KP = {
    "net": f"'КП'!$C${KP_TOTAL}",
    "vat": f"'КП'!$D${KP_TOTAL}",
    "gross": f"'КП'!$E${KP_TOTAL}",
}

r += 2
para(ws, r, f'="Срок выполнения работ: с "&TEXT({ref("work_start")},"DD.MM.YYYY")&" по "&TEXT({ref("work_end")},"DD.MM.YYYY")&"."', cols=(1, 5), font=FONT, align=AL_L)
r += 1
para(ws, r, f'="Условия оплаты: аванс "&TEXT({ref("advance")},"0%")&", окончательный расчёт — в течение 10 банковских дней после подписания актов по формам КС-2 и КС-3."',
     height=28, cols=(1, 5), font=FONT, align=AL_L)
r += 1
para(ws, r, f'="Гарантия на выполненные работы: "&{ref("warranty")}&" мес. Срок действия предложения: 30 календарных дней."', cols=(1, 5), font=FONT, align=AL_L)
r += 3
put(ws, r, 1, f'={ref("p_pos")}&" "&{ref("p_short")}', font=FONT)
merge(ws, r, 1, 3)
put(ws, r, 5, f'="_____________ /"&{ref("p_fio_short")}&"/"', font=FONT, align=AL_R)
page(ws)

# Контрольная ссылка на листе Параметры уже указывает на 'КП'!E17 — проверим:
assert KP_TOTAL == 14, f"Итог КП переехал на строку {KP_TOTAL}: обновите формулу total_calc на листе Параметры"

# ----------------------------------------------------------------------------
# Лист «КС-2» — акт о приёмке выполненных работ
# ----------------------------------------------------------------------------
ws = wb.create_sheet("КС-2")
widths(ws, {"A": 6, "B": 10, "C": 52, "D": 10, "E": 10, "F": 16, "G": 18})

put(ws, 1, 7, "Унифицированная форма № КС-2", font=FONT_SMALL, align=AL_R)
para(ws, 2, f'="Заказчик (Генподрядчик): "&{ref("z_full")}&", "&{ref("z_addr")}&", тел. "&{ref("z_phone")}',
     height=26, cols=(1, 7), font=FONT, align=AL_L)
para(ws, 3, f'="Подрядчик (Субподрядчик): "&{ref("p_full")}&", "&{ref("p_addr")}&", тел. "&{ref("p_phone")}',
     height=26, cols=(1, 7), font=FONT, align=AL_L)
para(ws, 4, f'="Стройка (объект): "&{ref("obj_name")}&", "&{ref("obj_addr")}', cols=(1, 7), font=FONT, align=AL_L)
para(ws, 5, f'="Договор подряда: № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")', cols=(1, 7), font=FONT, align=AL_L)

merge(ws, 7, 1, 7)
put(ws, 7, 1, f'="АКТ О ПРИЕМКЕ ВЫПОЛНЕННЫХ РАБОТ № "&{ref("ks2_num")}&" от "&TEXT({ref("ks2_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)
merge(ws, 8, 1, 7)
put(ws, 8, 1, f'="Отчётный период: с "&TEXT({ref("period_from")},"DD.MM.YYYY")&" по "&TEXT({ref("period_to")},"DD.MM.YYYY")',
    font=FONT, align=AL_C)

hdr = 10
for i, h in enumerate(["№ п/п", "№ поз. по смете", "Наименование работ", "Ед. изм.", "Кол-во",
                       "Цена за ед., руб.", "Стоимость, руб. без НДС"], 1):
    put(ws, hdr, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

n = SMETA["last"] - SMETA["first"] + 1
for i in range(n):
    r = hdr + 1 + i
    sr = SMETA["first"] + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, f"='Смета'!A{sr}", font=FONT_LINK, align=AL_C, border=BORDER)
    put(ws, r, 3, f"='Смета'!B{sr}", font=FONT_LINK, align=AL_L, border=BORDER)
    put(ws, r, 4, f"='Смета'!C{sr}", font=FONT_LINK, align=AL_C, border=BORDER)
    put(ws, r, 5, f"='Смета'!D{sr}", font=FONT_LINK, fmt=QTY, align=AL_C, border=BORDER)
    put(ws, r, 6, f"='Смета'!E{sr}", font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 7, f"=E{r}*F{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)
KS2_FIRST = hdr + 1
KS2_LAST = hdr + n

r = KS2_LAST + 1
merge(ws, r, 1, 6)
put(ws, r, 1, "Итого без НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 7, f"=SUM(G{KS2_FIRST}:G{KS2_LAST})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS2_NET = r
r += 1
merge(ws, r, 1, 6)
put(ws, r, 1, f'="НДС ("&TEXT({ref("nds")},"0%")&"), справочно"', font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 7, f"=G{KS2_NET}*{ref('nds')}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS2_VAT = r
r += 1
merge(ws, r, 1, 6)
put(ws, r, 1, "Всего с НДС, справочно", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 7, f"=G{KS2_NET}+G{KS2_VAT}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS2_GROSS = r

KS2 = {"net": f"'КС-2'!$G${KS2_NET}", "vat": f"'КС-2'!$G${KS2_VAT}", "gross": f"'КС-2'!$G${KS2_GROSS}"}

r += 2
put(ws, r, 1, f'="Сдал: "&{ref("p_pos")}&" "&{ref("p_short")}', font=FONT)
merge(ws, r, 1, 4)
put(ws, r, 6, f'="__________ /"&{ref("p_fio_short")}&"/"', font=FONT, align=AL_R)
merge(ws, r, 6, 7)
r += 2
put(ws, r, 1, f'="Принял: "&{ref("z_pos")}&" "&{ref("z_short")}', font=FONT)
merge(ws, r, 1, 4)
put(ws, r, 6, f'="__________ /"&{ref("z_fio_short")}&"/"', font=FONT, align=AL_R)
merge(ws, r, 6, 7)
page(ws)

# ----------------------------------------------------------------------------
# Лист «КС-3» — справка о стоимости выполненных работ и затрат
# ----------------------------------------------------------------------------
ws = wb.create_sheet("КС-3")
widths(ws, {"A": 6, "B": 46, "C": 18, "D": 18, "E": 20})

put(ws, 1, 5, "Унифицированная форма № КС-3", font=FONT_SMALL, align=AL_R)
para(ws, 2, f'="Заказчик (Генподрядчик): "&{ref("z_full")}&", "&{ref("z_addr")}', height=26, cols=(1, 5), font=FONT, align=AL_L)
para(ws, 3, f'="Подрядчик (Субподрядчик): "&{ref("p_full")}&", "&{ref("p_addr")}', height=26, cols=(1, 5), font=FONT, align=AL_L)
para(ws, 4, f'="Стройка (объект): "&{ref("obj_name")}&", "&{ref("obj_addr")}', cols=(1, 5), font=FONT, align=AL_L)
para(ws, 5, f'="Договор подряда: № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")', cols=(1, 5), font=FONT, align=AL_L)

merge(ws, 7, 1, 5)
put(ws, 7, 1, f'="СПРАВКА О СТОИМОСТИ ВЫПОЛНЕННЫХ РАБОТ И ЗАТРАТ № "&{ref("ks3_num")}&" от "&TEXT({ref("ks3_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)
merge(ws, 8, 1, 5)
put(ws, 8, 1, f'="Отчётный период: с "&TEXT({ref("period_from")},"DD.MM.YYYY")&" по "&TEXT({ref("period_to")},"DD.MM.YYYY")',
    font=FONT, align=AL_C)

hdr = 10
for i, h in enumerate(["№", "Наименование работ и затрат",
                       "С начала проведения работ, руб.", "С начала года, руб.",
                       "В том числе за отчётный период, руб."], 1):
    put(ws, hdr, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

ks3_lines = [
    (f'="Строительно-монтажные и пусконаладочные работы (акт КС-2 № "&{ref("ks2_num")}&" от "&TEXT({ref("ks2_date")},"DD.MM.YYYY")&")"',
     KS2["net"]),
    ('"Лифтовое оборудование и материалы (Спецификация № 1)"', SPEC["net"]),
]
for i, (name_f, src) in enumerate(ks3_lines):
    r = hdr + 1 + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, f"={name_f.lstrip('=')}" if name_f.startswith("=") else f"={name_f}", font=FONT, align=AL_L, border=BORDER)
    put(ws, r, 3, f"={src}", font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 4, f"=C{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 5, f"=C{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)

r = hdr + len(ks3_lines) + 1
put(ws, r, 1, "", border=BORDER)
put(ws, r, 2, "Итого", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
for col in (3, 4, 5):
    L = get_column_letter(col)
    put(ws, r, col, f"=SUM({L}{hdr + 1}:{L}{r - 1})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS3_NET = r
r += 1
put(ws, r, 1, "", border=BORDER)
put(ws, r, 2, f'="Сумма НДС ("&TEXT({ref("nds")},"0%")&")"', font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
for col in (3, 4, 5):
    L = get_column_letter(col)
    put(ws, r, col, f"={L}{KS3_NET}*{ref('nds')}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS3_VAT = r
r += 1
put(ws, r, 1, "", border=BORDER)
put(ws, r, 2, "Всего с учётом НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
for col in (3, 4, 5):
    L = get_column_letter(col)
    put(ws, r, col, f"={L}{KS3_NET}+{L}{KS3_VAT}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
KS3_GROSS = r

KS3 = {"net": f"'КС-3'!$E${KS3_NET}", "vat": f"'КС-3'!$E${KS3_VAT}", "gross": f"'КС-3'!$E${KS3_GROSS}"}

r += 2
put(ws, r, 1, f'="Заказчик: "&{ref("z_pos")}&" "&{ref("z_short")}', font=FONT)
merge(ws, r, 1, 3)
put(ws, r, 5, f'="__________ /"&{ref("z_fio_short")}&"/"', font=FONT, align=AL_R)
r += 2
put(ws, r, 1, f'="Подрядчик: "&{ref("p_pos")}&" "&{ref("p_short")}', font=FONT)
merge(ws, r, 1, 3)
put(ws, r, 5, f'="__________ /"&{ref("p_fio_short")}&"/"', font=FONT, align=AL_R)
page(ws)

# ----------------------------------------------------------------------------
# Лист «Счёт»
# ----------------------------------------------------------------------------
ws = wb.create_sheet("Счёт")
widths(ws, {"A": 6, "B": 46, "C": 12, "D": 10, "E": 16, "F": 18})

para(ws, 1, f'="Банк получателя: "&{ref("p_bank")}', cols=(1, 4), font=FONT, align=AL_L)
put(ws, 1, 5, "БИК", font=FONT, align=AL_R)
put(ws, 1, 6, f'={ref("p_bik")}', font=FONT_LINK, align=AL_L)
put(ws, 2, 5, "К/с", font=FONT, align=AL_R)
put(ws, 2, 6, f'={ref("p_ks")}', font=FONT_LINK, align=AL_L)
para(ws, 3, f'="Получатель: "&{ref("p_short")}&", ИНН "&{ref("p_inn")}&" / КПП "&{ref("p_kpp")}', cols=(1, 4), font=FONT, align=AL_L)
put(ws, 3, 5, "Р/с", font=FONT, align=AL_R)
put(ws, 3, 6, f'={ref("p_rs")}', font=FONT_LINK, align=AL_L)

merge(ws, 5, 1, 6)
put(ws, 5, 1, f'="СЧЁТ НА ОПЛАТУ № "&{ref("inv_num")}&" от "&TEXT({ref("inv_date")},"DD.MM.YYYY")',
    font=FONT_H, align=AL_C)

para(ws, 7, f'="Поставщик (Исполнитель): "&{ref("p_full")}&", "&{ref("p_addr")}', height=26, cols=(1, 6), font=FONT, align=AL_L)
para(ws, 8, f'="Покупатель (Заказчик): "&{ref("z_full")}&", ИНН "&{ref("z_inn")}&" / КПП "&{ref("z_kpp")}&", "&{ref("z_addr")}',
     height=26, cols=(1, 6), font=FONT, align=AL_L)
para(ws, 9, f'="Основание: договор подряда № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")', cols=(1, 6), font=FONT, align=AL_L)

hdr = 11
for i, h in enumerate(["№", "Наименование работ (услуг), товаров", "Кол-во", "Ед. изм.",
                       "Цена, руб. без НДС", "Сумма, руб. без НДС"], 1):
    put(ws, hdr, i, h, font=FONT_B, fill=FILL_HEAD, align=AL_C, border=BORDER)

inv_lines = [
    (f'="Работы по монтажу и пусконаладке лифтового оборудования по договору № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")&" (акт КС-2 № "&{ref("ks2_num")}&", справка КС-3 № "&{ref("ks3_num")}&")"',
     KS2["net"], 34),
    ('="Лифтовое оборудование и материалы (Спецификация № 1 к договору)"', SPEC["net"], 20),
]
for i, (name_f, src, h) in enumerate(inv_lines):
    r = hdr + 1 + i
    put(ws, r, 1, i + 1, font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 2, name_f, font=FONT, align=AL_L, border=BORDER)
    ws.row_dimensions[r].height = h
    put(ws, r, 3, 1, font=FONT, fmt=QTY, align=AL_C, border=BORDER)
    put(ws, r, 4, "компл.", font=FONT, align=AL_C, border=BORDER)
    put(ws, r, 5, f"={src}", font=FONT_LINK, fmt=NUM, align=AL_R, border=BORDER)
    put(ws, r, 6, f"=C{r}*E{r}", font=FONT, fmt=NUM, align=AL_R, border=BORDER)

r = hdr + len(inv_lines) + 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Итого без НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=SUM(F{hdr + 1}:F{r - 1})", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
INV_NET = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, f'="НДС ("&TEXT({ref("nds")},"0%")&")"', font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{INV_NET}*{ref('nds')}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
INV_VAT = r
r += 1
merge(ws, r, 1, 5)
put(ws, r, 1, "Всего к оплате с НДС", font=FONT_B, align=AL_R, fill=FILL_TOTAL, border=BORDER)
put(ws, r, 6, f"=F{INV_NET}+F{INV_VAT}", font=FONT_B, fmt=NUM, align=AL_R, fill=FILL_TOTAL, border=BORDER)
INV_GROSS = r

r += 2
para(ws, r, f'="Всего наименований "&COUNT(A{hdr + 1}:A{hdr + len(inv_lines)})&", на сумму "&TEXT(F{INV_GROSS},"#,##0.00")&" руб."'.replace("COUNT(A", f"COUNT('Счёт'!A"),
     cols=(1, 6), font=FONT_B, align=AL_L)
r += 1
para(ws, r, f'="Сумма прописью: "&{ref("total_words")}', height=28, cols=(1, 6), font=FONT, align=AL_L)
r += 3
put(ws, r, 1, f'="Руководитель: "&{ref("p_pos")}', font=FONT)
merge(ws, r, 1, 3)
put(ws, r, 5, f'="__________ /"&{ref("p_fio_short")}&"/"', font=FONT, align=AL_R)
merge(ws, r, 5, 6)
r += 2
put(ws, r, 1, '="Главный бухгалтер:"', font=FONT)
merge(ws, r, 1, 3)
put(ws, r, 5, f'="__________ /"&{ref("p_buh")}&"/"', font=FONT, align=AL_R)
merge(ws, r, 5, 6)
page(ws)

# ----------------------------------------------------------------------------
# Лист «Сопроводительное письмо»
# ----------------------------------------------------------------------------
ws = wb.create_sheet("Сопроводительное письмо")
widths(ws, {"A": 50, "B": 12, "C": 12, "D": 30})

put(ws, 1, 1, f'={ref("p_full")}', font=FONT_B, align=AL_L)
merge(ws, 1, 1, 4)
para(ws, 2, f'={ref("p_addr")}&", тел. "&{ref("p_phone")}&", "&{ref("p_email")}', cols=(1, 4), font=FONT, align=AL_L)
para(ws, 3, f'="ИНН "&{ref("p_inn")}&" / КПП "&{ref("p_kpp")}&", ОГРН "&{ref("p_ogrn")}', cols=(1, 4), font=FONT, align=AL_L)

put(ws, 5, 1, f'="Исх. № "&{ref("let_num")}&" от "&TEXT({ref("let_date")},"DD.MM.YYYY")', font=FONT, align=AL_L)
merge(ws, 5, 1, 2)
put(ws, 6, 4, f'={ref("z_pos_dat")}', font=FONT, align=AL_L)
put(ws, 7, 4, f'={ref("z_short")}', font=FONT, align=AL_L)
put(ws, 8, 4, f'={ref("z_fio_dat")}', font=FONT_B, align=AL_L)

merge(ws, 10, 1, 4)
put(ws, 10, 1, f'="О направлении документов по договору № "&{ref("dog_num")}&" от "&TEXT({ref("dog_date")},"DD.MM.YYYY")',
    font=FONT_B, align=AL_L)

para(ws, 12, f'="Уважаемый "&{ref("z_name_patr")}&"!"', cols=(1, 4), font=FONT_B, align=AL_L)
para(ws, 13,
     f'="В связи с завершением работ по монтажу и пусконаладке лифтового оборудования на объекте: "'
     f'&{ref("obj_name")}&" по адресу: "&{ref("obj_addr")}&" направляем Вам для рассмотрения и подписания '
     f'комплект отчётных документов по договору подряда № "&{ref("dog_num")}&" от "'
     f'&TEXT({ref("dog_date")},"DD.MM.YYYY")&"."',
     height=60, cols=(1, 4))
para(ws, 14,
     '="Просим в течение 5 (пяти) рабочих дней с даты получения подписать документы и вернуть по одному '
     'экземпляру в наш адрес либо направить мотивированный отказ от подписания."',
     height=40, cols=(1, 4))

put(ws, 16, 1, "Приложения:", font=FONT_B, align=AL_L)
apps = [
    f'="1. Акт о приёмке выполненных работ (КС-2) № "&{ref("ks2_num")}&" от "&TEXT({ref("ks2_date")},"DD.MM.YYYY")&" — в 2 экз."',
    f'="2. Справка о стоимости выполненных работ и затрат (КС-3) № "&{ref("ks3_num")}&" от "&TEXT({ref("ks3_date")},"DD.MM.YYYY")&" — в 2 экз."',
    f'="3. Счёт на оплату № "&{ref("inv_num")}&" от "&TEXT({ref("inv_date")},"DD.MM.YYYY")&" на сумму "&TEXT({KS3["gross"]},"#,##0.00")&" руб. с НДС — в 1 экз."',
]
for i, a in enumerate(apps):
    para(ws, 17 + i, a, cols=(1, 4), font=FONT, align=AL_L)

r = 22
put(ws, r, 1, f'={ref("p_pos")}&" "&{ref("p_short")}', font=FONT, align=AL_L)
merge(ws, r, 1, 2)
put(ws, r, 4, f'="_____________ /"&{ref("p_fio_short")}&"/"', font=FONT, align=AL_L)
page(ws)

# ----------------------------------------------------------------------------
# Лист «Договор»
# ----------------------------------------------------------------------------
ws = wb.create_sheet("Договор")
widths(ws, {"A": 14, "B": 14, "C": 14, "D": 14, "E": 14, "F": 14, "G": 14})

r = 1
merge(ws, r, 1, 7)
put(ws, r, 1, f'="ДОГОВОР ПОДРЯДА № "&{ref("dog_num")}', font=FONT_TITLE, align=AL_C)
r += 1
merge(ws, r, 1, 3)
put(ws, r, 1, f'={ref("dog_city")}', font=FONT, align=AL_L)
merge(ws, r, 5, 7)
put(ws, r, 5, f'=TEXT({ref("dog_date")},"DD.MM.YYYY")', font=FONT, align=AL_R)
r += 2

para(ws, r,
     f'={ref("z_full")}&" (далее — «Заказчик»), в лице "&{ref("z_pos_gen")}&" "&{ref("z_fio_gen")}'
     f'&", действующего на основании "&{ref("z_basis")}&", с одной стороны, и "&{ref("p_full")}'
     f'&" (далее — «Подрядчик»), в лице "&{ref("p_pos_gen")}&" "&{ref("p_fio_gen")}'
     f'&", действующего на основании "&{ref("p_basis")}&", с другой стороны, совместно именуемые '
     f'«Стороны», заключили настоящий Договор о нижеследующем:"',
     height=78)
r += 2

def h(text):
    global r
    para(ws, r, text, font=FONT_B, align=AL_C)
    r += 1

def p(text, height=None):
    global r
    para(ws, r, text, height=height)
    r += 1

h("1. ПРЕДМЕТ ДОГОВОРА")
p(f'="1.1. Подрядчик обязуется выполнить комплекс работ по монтажу и пусконаладке лифтового оборудования '
  f'("&{ref("obj_type")}&", "&{ref("obj_lifts")}&" шт.) на объекте: "&{ref("obj_name")}&" по адресу: "'
  f'&{ref("obj_addr")}&" (далее — «Объект»), а Заказчик обязуется создать Подрядчику необходимые условия '
  f'для выполнения работ, принять их результат и уплатить обусловленную Договором цену."', height=60)
p('="1.2. Состав, объёмы и стоимость работ определяются Локальной сметой № 1 (Приложение № 1) и '
  'Спецификацией № 1 (Приложение № 2), являющимися неотъемлемой частью настоящего Договора."', height=32)
r += 1

h("2. ЦЕНА ДОГОВОРА И ПОРЯДОК РАСЧЁТОВ")
p(f'="2.1. Цена Договора составляет "&TEXT({KP["gross"]},"#,##0.00")&" ("&{ref("total_words")}&") руб., '
  f'в том числе НДС ("&TEXT({ref("nds")},"0%")&") — "&TEXT({KP["vat"]},"#,##0.00")&" руб."', height=44)
p(f'="2.2. Заказчик перечисляет Подрядчику аванс в размере "&TEXT({ref("advance")},"0%")&" от цены Договора, '
  f'что составляет "&TEXT({KP["gross"]}*{ref("advance")},"#,##0.00")&" руб., в течение 5 (пяти) банковских '
  f'дней с даты подписания настоящего Договора."', height=44)
p('="2.3. Окончательный расчёт производится Заказчиком в течение 10 (десяти) банковских дней после '
  'подписания Сторонами акта о приёмке выполненных работ (форма КС-2) и справки о стоимости выполненных '
  'работ и затрат (форма КС-3) на основании выставленного Подрядчиком счёта."', height=44)
r += 1

h("3. СРОКИ ВЫПОЛНЕНИЯ РАБОТ")
p(f'="3.1. Начало работ: "&TEXT({ref("work_start")},"DD.MM.YYYY")&". Окончание работ: "'
  f'&TEXT({ref("work_end")},"DD.MM.YYYY")&"."')
p('="3.2. Сроки выполнения работ могут быть изменены по соглашению Сторон путём подписания '
  'дополнительного соглашения к настоящему Договору."', height=30)
r += 1

h("4. ОБЯЗАННОСТИ СТОРОН")
p('="4.1. Подрядчик обязуется выполнить работы в соответствии с требованиями ТР ТС 011/2011 «Безопасность '
  'лифтов», проектной документацией и условиями настоящего Договора, своими силами, инструментами и '
  'механизмами."', height=44)
p('="4.2. Подрядчик обязуется обеспечить на Объекте соблюдение требований охраны труда, пожарной '
  'безопасности, а также вывоз строительного мусора, образовавшегося в результате выполнения работ."', height=32)
p('="4.3. Заказчик обязуется передать Подрядчику по акту строительную готовность машинных помещений и '
  'шахт, обеспечить электроснабжение на период монтажа и допуск персонала Подрядчика на Объект."', height=32)
p('="4.4. Заказчик обязуется своевременно принять и оплатить выполненные работы в порядке, установленном '
  'разделом 2 настоящего Договора."', height=30)
r += 1

h("5. ПОРЯДОК СДАЧИ И ПРИЁМКИ РАБОТ")
p('="5.1. По завершении работ Подрядчик передаёт Заказчику акт по форме КС-2, справку по форме КС-3 и '
  'исполнительную документацию сопроводительным письмом."', height=30)
p('="5.2. Заказчик в течение 5 (пяти) рабочих дней с даты получения документов подписывает их либо '
  'направляет Подрядчику мотивированный отказ с перечнем замечаний и сроками их устранения."', height=32)
r += 1

h("6. ГАРАНТИИ КАЧЕСТВА")
p(f'="6.1. Гарантийный срок на выполненные работы составляет "&{ref("warranty")}&" месяца(ев) с даты '
  f'подписания Сторонами акта по форме КС-2. Гарантия на оборудование — в соответствии с документацией '
  f'завода-изготовителя."', height=40)
r += 1

h("7. ОТВЕТСТВЕННОСТЬ СТОРОН")
p(f'="7.1. За нарушение сроков выполнения работ Заказчик вправе требовать от Подрядчика уплаты неустойки '
  f'в размере "&TEXT({ref("penalty")},"0.0%")&" от цены Договора за каждый день просрочки, но не более 10% '
  f'от цены Договора. За нарушение сроков оплаты Подрядчик вправе требовать от Заказчика неустойку в том '
  f'же размере от неоплаченной суммы."', height=52)
r += 1

h("8. ПРОЧИЕ УСЛОВИЯ")
p('="8.1. Споры Сторон разрешаются путём переговоров, а при недостижении согласия — в Арбитражном суде '
  'по месту нахождения ответчика с соблюдением претензионного порядка (срок ответа на претензию — '
  '10 рабочих дней)."', height=40)
p('="8.2. Договор составлен в двух экземплярах, имеющих равную юридическую силу, по одному для каждой '
  'из Сторон. Приложения: № 1 — Локальная смета № 1; № 2 — Спецификация № 1."', height=32)
r += 1

h("9. АДРЕСА И РЕКВИЗИТЫ СТОРОН")
left_col, right_col = (1, 3), (5, 7)
z_lines = [
    '="ЗАКАЗЧИК:"',
    f'={ref("z_full")}',
    f'="ИНН/КПП: "&{ref("z_inn")}&" / "&{ref("z_kpp")}',
    f'="ОГРН: "&{ref("z_ogrn")}',
    f'="Адрес: "&{ref("z_addr")}',
    f'="Банк: "&{ref("z_bank")}',
    f'="БИК: "&{ref("z_bik")}',
    f'="Р/с: "&{ref("z_rs")}',
    f'="К/с: "&{ref("z_ks")}',
    f'="Тел.: "&{ref("z_phone")}&", "&{ref("z_email")}',
    "",
    f'={ref("z_pos")}',
    f'="_____________ /"&{ref("z_fio_short")}&"/"',
    '="М.П."',
]
p_lines = [
    '="ПОДРЯДЧИК:"',
    f'={ref("p_full")}',
    f'="ИНН/КПП: "&{ref("p_inn")}&" / "&{ref("p_kpp")}',
    f'="ОГРН: "&{ref("p_ogrn")}',
    f'="Адрес: "&{ref("p_addr")}',
    f'="Банк: "&{ref("p_bank")}',
    f'="БИК: "&{ref("p_bik")}',
    f'="Р/с: "&{ref("p_rs")}',
    f'="К/с: "&{ref("p_ks")}',
    f'="Тел.: "&{ref("p_phone")}&", "&{ref("p_email")}',
    "",
    f'={ref("p_pos")}',
    f'="_____________ /"&{ref("p_fio_short")}&"/"',
    '="М.П."',
]
for i, (zl, pl) in enumerate(zip(z_lines, p_lines)):
    row = r + i
    tall = i in (1, 4, 5)
    merge(ws, row, *left_col)
    if zl:
        put(ws, row, left_col[0], zl, font=FONT_B if i in (0, 11) else FONT, align=AL_TOP)
    merge(ws, row, *right_col)
    if pl:
        put(ws, row, right_col[0], pl, font=FONT_B if i in (0, 11) else FONT, align=AL_TOP)
    if tall:
        ws.row_dimensions[row].height = 40
page(ws)

# ----------------------------------------------------------------------------
out = "Пакет_документов_монтаж_лифтов.xlsx"
wb.save(out)
print("saved", out)
