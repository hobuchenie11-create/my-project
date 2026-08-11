# -*- coding: utf-8 -*-
"""
Памятка председателя: кому какая квитанция нужна.

Книга из двух листов:

    ПАМЯТКА          — печатная страница А4 с тремя столбцами:
                       бумажная квитанция / не нужна (платят онлайн) /
                       электронная. Заполняется формулами;
    СПИСОК КВАРТИР   — единственное место для правки: номер квартиры,
                       статус из выпадающего списка и примечание.

Квартиру не переносят между столбцами руками — меняют её статус в списке,
и она сама уходит в нужный столбец памятки.

Запуск:  python3 build_memo.py
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.properties import PageSetupProperties

OUTDIR = Path(__file__).resolve().parent / "output"
OUT = OUTDIR / "Памятка_доставка_квитанций.xlsx"

MEMO = "ПАМЯТКА"
LIST = "СПИСОК КВАРТИР"
FONT = "Arial"

ACCENT = "0F6B70"
ACCENT_LIGHT = "E8F3F3"
GREY = "F3F5F5"
TXT = "263238"

# Статусы. Порядок задаёт порядок столбцов памятки.
СТАТУСЫ = [
    ("Бумажная", "НУЖНА БУМАЖНАЯ КВИТАНЦИЯ",
     "печатаем и разносим по почтовым ящикам"),
    ("Онлайн", "КВИТАНЦИЯ НЕ НУЖНА",
     "платят онлайн по сохранённому шаблону"),
    ("Электронная", "КВИТАНЦИЯ В ЭЛЕКТРОННОМ ВИДЕ",
     "отправляем PDF на электронную почту"),
]

ВСЕГО_КВАРТИР = 60      # строк в списке; лишние можно очистить
СТРОК_В_СТОЛБЦЕ = 43    # столько номеров помещается в столбец на А4
ПЕРВАЯ_СТРОКА_СПИСКА = 3

THIN = Side(style="thin", color="BFBFBF")
MEDIUM = Side(style="medium", color=ACCENT)
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def оформить(cell, *, size=10, bold=False, italic=False, color=TXT,
             fill=None, align="left", valign="center", wrap=False,
             border=BOX, indent=0):
    cell.font = Font(name=FONT, size=size, bold=bold, italic=italic,
                     color=color)
    if fill:
        cell.fill = PatternFill("solid", fgColor=fill)
    cell.alignment = Alignment(horizontal=align, vertical=valign,
                               wrap_text=wrap, indent=indent)
    if border is not None:
        cell.border = border
    return cell


wb = Workbook()

# ==========================================================================
# Лист СПИСОК КВАРТИР — единственное место для правки
# ==========================================================================
lst = wb.create_sheet(LIST)
lst.sheet_view.showGridLines = False
for col, w in {"A": 3, "B": 12, "C": 22, "D": 46,
               "E": 11, "F": 11, "G": 11}.items():
    lst.column_dimensions[col].width = w

lst.merge_cells("B1:D1")
оформить(lst["B1"], size=13, bold=True, color=ACCENT, border=None)
lst["B1"] = "СПИСОК КВАРТИР — ЗДЕСЬ МЕНЯЕМ СТАТУС"
lst.row_dimensions[1].height = 24

for i, name in enumerate(["Квартира", "Статус", "Примечание (собственник, "
                          "почта, договорённости)"], start=2):
    c = lst.cell(2, i, name)
    оформить(c, size=10, bold=True, color="FFFFFF", fill=ACCENT,
             align="center", wrap=True)
lst.row_dimensions[2].height = 30

# Служебные счётчики: порядковый номер квартиры внутри своего статуса.
# По ним памятка вытаскивает номера формулой ИНДЕКС/ПОИСКПОЗ — без макросов
# и без формул массива, поэтому работает в любой версии Excel.
for i, (код, _, _) in enumerate(СТАТУСЫ):
    c = lst.cell(2, 5 + i, f"№ в «{код}»")
    оформить(c, size=8, bold=True, color="888888", fill=GREY,
             align="center", wrap=True)

ПРИМЕРЫ = {47: ("Электронная", "Департамент жилищной политики "
                               "Администрации города Омска"),
           49: ("Онлайн", "Председатель совета дома")}

for n in range(1, ВСЕГО_КВАРТИР + 1):
    row = ПЕРВАЯ_СТРОКА_СПИСКА + n - 1
    статус, примечание = ПРИМЕРЫ.get(n, ("Бумажная", ""))
    lst.row_dimensions[row].height = 17

    оформить(lst.cell(row, 2, n), size=10, bold=True, align="center")
    оформить(lst.cell(row, 3, статус), size=10, color=ACCENT, bold=True,
             fill=ACCENT_LIGHT, align="center")
    оформить(lst.cell(row, 4, примечание or None), size=9, indent=1)

    for i, (код, _, _) in enumerate(СТАТУСЫ):
        col = 5 + i
        буква = chr(ord("C"))
        формула = (f'=IF($C{row}="{код}",'
                   f'COUNTIF($C${ПЕРВАЯ_СТРОКА_СПИСКА}:$C{row},"{код}"),"")')
        c = lst.cell(row, col, формула)
        оформить(c, size=8, color="AAAAAA", align="center")

ПОСЛЕДНЯЯ = ПЕРВАЯ_СТРОКА_СПИСКА + ВСЕГО_КВАРТИР - 1

dv = DataValidation(
    type="list",
    formula1='"' + ",".join(код for код, _, _ in СТАТУСЫ) + '"',
    allow_blank=True, showDropDown=False)
dv.promptTitle = "Статус квартиры"
dv.prompt = ("Бумажная — печатаем и разносим\n"
             "Онлайн — платят сами по шаблону\n"
             "Электронная — отправляем PDF на почту")
dv.errorTitle = "Такого статуса нет"
dv.error = "Выберите значение из списка."
lst.add_data_validation(dv)
dv.add(f"C{ПЕРВАЯ_СТРОКА_СПИСКА}:C{ПОСЛЕДНЯЯ}")

подсказка = lst.cell(ПОСЛЕДНЯЯ + 2, 2,
                     "Чтобы квартира переехала в другой столбец памятки, "
                     "поменяйте её статус в столбце «Статус» — вручную "
                     "переносить ничего не нужно. Столбцы E–G служебные: "
                     "по ним памятка собирает списки, их можно скрыть, "
                     "но не удалять. Лишние строки просто очистите, "
                     "новые квартиры дописывайте ниже и протяните формулы "
                     "в E–G.")
оформить(подсказка, size=9, italic=True, color="666666", wrap=True,
         valign="top", border=None)
lst.merge_cells(start_row=ПОСЛЕДНЯЯ + 2, start_column=2,
                end_row=ПОСЛЕДНЯЯ + 4, end_column=4)

lst.freeze_panes = f"B{ПЕРВАЯ_СТРОКА_СПИСКА}"
lst.print_area = f"$B$1:$D${ПОСЛЕДНЯЯ + 4}"
lst.page_setup.orientation = "portrait"
lst.page_setup.paperSize = lst.PAPERSIZE_A4
lst.page_setup.fitToWidth = 1
lst.page_setup.fitToHeight = 1
lst.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)

# ==========================================================================
# Лист ПАМЯТКА — печатная страница
# ==========================================================================
memo = wb.create_sheet(MEMO, 0)
memo.sheet_view.showGridLines = False
for col, w in {"A": 1.5, "B": 26, "C": 26, "D": 26, "E": 1.5}.items():
    memo.column_dimensions[col].width = w

memo.row_dimensions[1].height = 8
memo.merge_cells("B2:D2")
оформить(memo["B2"], size=15, bold=True, color=ACCENT, align="center",
         border=None)
memo["B2"] = "КОМУ КАКАЯ КВИТАНЦИЯ НУЖНА"
memo.row_dimensions[2].height = 26

memo.merge_cells("B3:D3")
оформить(memo["B3"], size=10, italic=True, color="666666", align="center",
         border=None)
memo["B3"] = ('="МКД г. Омск, ул. Магистральная, 2   ·   всего квартир в '
              f"списке: \"&COUNTA('{LIST}'!$B${ПЕРВАЯ_СТРОКА_СПИСКА}:$B${ПОСЛЕДНЯЯ})")
memo.row_dimensions[3].height = 18
memo.row_dimensions[4].height = 10

# --- Шапки трёх столбцов
ЗАГОЛОВОК = 5
ПОДЗАГОЛОВОК = 6
СЧЁТЧИК = 7
ПЕРВАЯ = 8

memo.row_dimensions[ЗАГОЛОВОК].height = 32
memo.row_dimensions[ПОДЗАГОЛОВОК].height = 26
memo.row_dimensions[СЧЁТЧИК].height = 18

for i, (код, заголовок, пояснение) in enumerate(СТАТУСЫ):
    col = chr(ord("B") + i)
    оформить(memo[f"{col}{ЗАГОЛОВОК}"], size=10, bold=True, color="FFFFFF",
             fill=ACCENT, align="center", wrap=True)
    memo[f"{col}{ЗАГОЛОВОК}"] = f"{i + 1}. {заголовок}"

    оформить(memo[f"{col}{ПОДЗАГОЛОВОК}"], size=9, italic=True, color=TXT,
             fill=GREY, align="center", wrap=True)
    memo[f"{col}{ПОДЗАГОЛОВОК}"] = пояснение

    оформить(memo[f"{col}{СЧЁТЧИК}"], size=10, bold=True, color=ACCENT,
             fill=ACCENT_LIGHT, align="center")
    memo[f"{col}{СЧЁТЧИК}"] = (
        f'="Квартир: "&COUNTIF(\'{LIST}\'!$C:$C,"{код}")')

    # Сами номера квартир
    служебный = chr(ord("E") + i)
    for k in range(СТРОК_В_СТОЛБЦЕ):
        row = ПЕРВАЯ + k
        memo.row_dimensions[row].height = 13.5
        c = memo[f"{col}{row}"]
        c.value = (
            f'=IFERROR("кв. "&INDEX(\'{LIST}\'!$B:$B,'
            f"MATCH({k + 1},'{LIST}'!${служебный}:${служебный},0)),\"\")")
        оформить(c, size=9.5, align="center",
                 fill=ACCENT_LIGHT if k % 2 else "FFFFFF")

    # Если в категории больше строк, чем помещается на страницу
    хвост = ПЕРВАЯ + СТРОК_В_СТОЛБЦЕ
    memo.row_dimensions[хвост].height = 16
    c = memo[f"{col}{хвост}"]
    c.value = (f'=IF(COUNTIF(\'{LIST}\'!$C:$C,"{код}")>{СТРОК_В_СТОЛБЦЕ},'
               f'"…и ещё "&(COUNTIF(\'{LIST}\'!$C:$C,"{код}")'
               f'-{СТРОК_В_СТОЛБЦЕ})&" — см. лист «{LIST}»","")')
    оформить(c, size=8, italic=True, color="B00000", align="center")

# Рамка вокруг каждого столбца
for i in range(3):
    col = chr(ord("B") + i)
    for row in range(ЗАГОЛОВОК, ПЕРВАЯ + СТРОК_В_СТОЛБЦЕ + 1):
        c = memo[f"{col}{row}"]
        b = c.border
        c.border = Border(
            left=MEDIUM, right=MEDIUM,
            top=MEDIUM if row == ЗАГОЛОВОК else b.top,
            bottom=MEDIUM if row == ПЕРВАЯ + СТРОК_В_СТОЛБЦЕ else b.bottom)

ПОДВАЛ = ПЕРВАЯ + СТРОК_В_СТОЛБЦЕ + 2
memo.row_dimensions[ПОДВАЛ].height = 30
memo.merge_cells(f"B{ПОДВАЛ}:D{ПОДВАЛ}")
оформить(memo[f"B{ПОДВАЛ}"], size=9, italic=True, color="666666",
         align="center", wrap=True, border=None)
memo[f"B{ПОДВАЛ}"] = (
    f'="Статус меняется на листе «{LIST}» — квартира сама перейдёт '
    'в нужный столбец. Памятка обновлена: "'
    '&TEXT(DAY(TODAY()),"00")&"."&TEXT(MONTH(TODAY()),"00")&"."&YEAR(TODAY())')

memo.print_area = f"$B$1:$D${ПОДВАЛ}"
memo.page_setup.orientation = "portrait"
memo.page_setup.paperSize = memo.PAPERSIZE_A4
memo.page_setup.fitToWidth = 1
memo.page_setup.fitToHeight = 1
memo.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
memo.page_margins.left = 0.39
memo.page_margins.right = 0.39
memo.page_margins.top = 0.39
memo.page_margins.bottom = 0.39
memo.print_options.horizontalCentered = True

wb.defined_names.add(DefinedName(
    "СПИСОК_КВАРТИР",
    attr_text=f"'{LIST}'!$B${ПЕРВАЯ_СТРОКА_СПИСКА}:$D${ПОСЛЕДНЯЯ}"))

wb.active = 0
OUTDIR.mkdir(parents=True, exist_ok=True)
wb.save(OUT)
print(f"Готово: {OUT}")
