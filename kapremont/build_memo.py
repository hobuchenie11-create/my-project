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

ВСЕГО_КВАРТИР = 80      # квартир в доме
СТРОК_В_ПОДКОЛОНКЕ = 40  # в категории две подколонки => все 80 квартир
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
# Восемьдесят строк на одну страницу влезли бы только нечитаемо мелко,
# поэтому по высоте лист не ограничиваем.
lst.page_setup.fitToHeight = 0
lst.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)

# ==========================================================================
# Лист ПАМЯТКА — печатная страница
# ==========================================================================
# Каждая категория занимает две подколонки: так все квартиры дома помещаются
# на одну страницу даже если почти все они в одном статусе. Столбцов
# по-прежнему три — подколонки лишь делят список номеров пополам.
memo = wb.create_sheet(MEMO, 0)
memo.sheet_view.showGridLines = False
ШИРИНА = {"A": 1.5, "B": 12.5, "C": 12.5, "D": 12.5,
          "E": 12.5, "F": 12.5, "G": 12.5, "H": 1.5}
for col, w in ШИРИНА.items():
    memo.column_dimensions[col].width = w

memo.row_dimensions[1].height = 8
memo.merge_cells("B2:G2")
оформить(memo["B2"], size=15, bold=True, color=ACCENT, align="center",
         border=None)
memo["B2"] = "КОМУ КАКАЯ КВИТАНЦИЯ НУЖНА"
memo.row_dimensions[2].height = 24

memo.merge_cells("B3:G3")
оформить(memo["B3"], size=10, italic=True, color="666666", align="center",
         border=None)
memo["B3"] = ('="МКД г. Омск, ул. Магистральная, 2   ·   всего квартир в '
              f"списке: \"&COUNTA('{LIST}'!$B${ПЕРВАЯ_СТРОКА_СПИСКА}:$B${ПОСЛЕДНЯЯ})")
memo.row_dimensions[3].height = 16
memo.row_dimensions[4].height = 8

ЗАГОЛОВОК = 5
ПОДЗАГОЛОВОК = 6
СЧЁТЧИК = 7
ПЕРВАЯ = 8

memo.row_dimensions[ЗАГОЛОВОК].height = 30
memo.row_dimensions[ПОДЗАГОЛОВОК].height = 24
memo.row_dimensions[СЧЁТЧИК].height = 16

for i, (код, заголовок, пояснение) in enumerate(СТАТУСЫ):
    лев = chr(ord("B") + i * 2)
    прав = chr(ord("C") + i * 2)
    служебный = chr(ord("E") + i)
    счёт = f'COUNTIF(\'{LIST}\'!$C:$C,"{код}")'

    for строка, текст, стиль in (
            (ЗАГОЛОВОК, f"{i + 1}. {заголовок}",
             dict(size=10, bold=True, color="FFFFFF", fill=ACCENT)),
            (ПОДЗАГОЛОВОК, пояснение,
             dict(size=8.5, italic=True, color=TXT, fill=GREY)),
            (СЧЁТЧИК, f'="Квартир: "&{счёт}',
             dict(size=10, bold=True, color=ACCENT, fill=ACCENT_LIGHT))):
        memo.merge_cells(f"{лев}{строка}:{прав}{строка}")
        c = memo[f"{лев}{строка}"]
        c.value = текст
        for колонка in (лев, прав):
            оформить(memo[f"{колонка}{строка}"], align="center", wrap=True,
                     **стиль)

    # Номера: левая подколонка — первая половина списка, правая — вторая
    for k in range(СТРОК_В_ПОДКОЛОНКЕ):
        row = ПЕРВАЯ + k
        memo.row_dimensions[row].height = 14
        for половина, колонка in enumerate((лев, прав)):
            позиция = k + 1 + половина * СТРОК_В_ПОДКОЛОНКЕ
            c = memo[f"{колонка}{row}"]
            c.value = (
                f'=IFERROR("кв. "&INDEX(\'{LIST}\'!$B:$B,'
                f"MATCH({позиция},'{LIST}'!${служебный}:${служебный},0)),\"\")")
            оформить(c, size=9.5, align="center",
                     fill=ACCENT_LIGHT if k % 2 else "FFFFFF")

    хвост = ПЕРВАЯ + СТРОК_В_ПОДКОЛОНКЕ
    memo.row_dimensions[хвост].height = 14
    memo.merge_cells(f"{лев}{хвост}:{прав}{хвост}")
    c = memo[f"{лев}{хвост}"]
    ёмкость = СТРОК_В_ПОДКОЛОНКЕ * 2
    c.value = (f'=IF({счёт}>{ёмкость},"…и ещё "&({счёт}-{ёмкость})'
               f'&" — см. лист «{LIST}»","")')
    for колонка in (лев, прав):
        оформить(memo[f"{колонка}{хвост}"], size=8, italic=True,
                 color="B00000", align="center")

# Рамка вокруг каждой категории
for i in range(3):
    лев = chr(ord("B") + i * 2)
    прав = chr(ord("C") + i * 2)
    for row in range(ЗАГОЛОВОК, ПЕРВАЯ + СТРОК_В_ПОДКОЛОНКЕ + 1):
        for колонка, сторона in ((лев, "left"), (прав, "right")):
            c = memo[f"{колонка}{row}"]
            b = c.border
            c.border = Border(
                left=MEDIUM if сторона == "left" else b.left,
                right=MEDIUM if сторона == "right" else b.right,
                top=MEDIUM if row == ЗАГОЛОВОК else b.top,
                bottom=(MEDIUM if row == ПЕРВАЯ + СТРОК_В_ПОДКОЛОНКЕ
                        else b.bottom))

ПОДВАЛ = ПЕРВАЯ + СТРОК_В_ПОДКОЛОНКЕ + 2
memo.row_dimensions[ПОДВАЛ].height = 28
memo.merge_cells(f"B{ПОДВАЛ}:G{ПОДВАЛ}")
оформить(memo[f"B{ПОДВАЛ}"], size=9, italic=True, color="666666",
         align="center", wrap=True, border=None)
memo[f"B{ПОДВАЛ}"] = (
    f'="Статус меняется на листе «{LIST}» — квартира сама перейдёт '
    'в нужный столбец. Памятка обновлена: "'
    '&TEXT(DAY(TODAY()),"00")&"."&TEXT(MONTH(TODAY()),"00")&"."&YEAR(TODAY())')

memo.print_area = f"$B$1:$G${ПОДВАЛ}"
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
