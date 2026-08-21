# -*- coding: utf-8 -*-
"""Журнал арендных платежей — полная дизайнерская версия."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side, Protection
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import FormulaRule, CellIsRule, DataBarRule
from openpyxl.workbook.defined_name import DefinedName

OUT = "/home/user/my-project/Журнал_арендных_платежей_v3.xlsx"

# ---------- палитра: сирень / бирюза / белый ----------
LIL_DEEP = "4B2E73"
LIL      = "6A4C93"
LIL_MID  = "8E6FBF"
LIL_SOFT = "C9B6E8"
LIL_BG   = "F3EEFB"
LIL_BG2  = "E9E0F7"
TRQ_DEEP = "0B5F5E"
TRQ      = "0E8F8C"
TRQ_MID  = "16B3AF"
TRQ_SOFT = "9BDEDB"
TRQ_BG   = "E4F7F6"
WHITE    = "FFFFFF"
INK      = "2E2A3B"
MUTED    = "7A7590"
AMBER    = "C97C1B"
AMBER_BG = "FDF3E2"
RED      = "B3382F"
RED_BG   = "FBEAE8"
GREEN    = "1F7A55"
GREEN_BG = "E6F6EE"

F = "Arial"
MON = '[$-419]mmmm yyyy'
DATE_F = '[$-419]DD.MM.YYYY'
RUB = '#,##0" ₽";-#,##0" ₽";"—"'
RUB_BIG = '#,##0" ₽";-#,##0" ₽";"0 ₽"'
PCT = '0.0%'

PWD = "arenda"

JR_FIRST, JR_LAST = 7, 306          # строки журнала «Регистрация»
HS_FIRST, HS_LAST = 6, 41           # строки «История» (36 месяцев)
AN_FIRST, AN_LAST = 7, 42           # строки «Аналитика»

# ---------- помощники ----------
def fill(c):  return PatternFill("solid", fgColor=c)
def side(c, s="thin"): return Side(style=s, color=c)

def grid(ws, ref):
    """область -> кортеж кортежей ячеек, независимо от формы ссылки"""
    from openpyxl.cell.cell import Cell
    from openpyxl.cell.read_only import EmptyCell
    cells = ws[ref]
    if isinstance(cells, Cell):
        return ((cells,),)
    if isinstance(cells[0], Cell):
        return (tuple(cells),)
    return tuple(tuple(r) for r in cells)

def box(ws, ref, color, style="thin"):
    """рамка вокруг прямоугольной области"""
    cells = grid(ws, ref)
    rmin, rmax = cells[0][0].row, cells[-1][0].row
    cmin, cmax = cells[0][0].column, cells[0][-1].column
    for row in cells:
        for c in row:
            b = c.border
            ws.cell(row=c.row, column=c.column).border = Border(
                left=side(color) if c.column == cmin else b.left,
                right=side(color) if c.column == cmax else b.right,
                top=side(color) if c.row == rmin else b.top,
                bottom=side(color) if c.row == rmax else b.bottom,
            )

def paint(ws, ref, bg=None, font=None, align=None, fmt=None, unlock=False):
    cells = grid(ws, ref)
    for row in cells:
        for c in row:
            if bg:    c.fill = fill(bg)
            if font:  c.font = font
            if align: c.alignment = align
            if fmt:   c.number_format = fmt
            if unlock: c.protection = Protection(locked=False)

def put(ws, ref, value=None, bg=None, font=None, align=None, fmt=None, unlock=False, h=None):
    if ":" in ref:
        ws.merge_cells(ref)
        anchor = ref.split(":")[0]
    else:
        anchor = ref
    if value is not None:
        ws[anchor] = value
    paint(ws, ref, bg, font, align, fmt, unlock)
    if h:
        ws.row_dimensions[ws[anchor].row].height = h
    return ws[anchor]

L  = lambda ref: ref  # читаемость

A_C = Alignment(horizontal="center", vertical="center", wrap_text=True)
A_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
A_R = Alignment(horizontal="right", vertical="center")
A_LT = Alignment(horizontal="left", vertical="center", wrap_text=True)

def banner(ws, ref, title, sub_ref=None, sub=None, color=LIL):
    put(ws, ref, title, bg=color, font=Font(F, 17, bold=True, color=WHITE), align=A_C, h=44)
    if sub_ref:
        put(ws, sub_ref, sub, bg=TRQ_BG, font=Font(F, 10, color=TRQ_DEEP), align=A_C, h=24)

def section(ws, ref, text, color=LIL_BG2, fg=LIL_DEEP):
    put(ws, ref, text, bg=color, font=Font(F, 11, bold=True, color=fg), align=A_L, h=24)
    box(ws, ref, LIL_SOFT)

def page(ws, area, titles=None, landscape=False, fit_h=0):
    ws.print_area = area
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = fit_h
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.4
    ws.page_margins.header = ws.page_margins.footer = 0.2
    if titles:
        ws.print_title_rows = titles
    ws.oddFooter.center.text = "&\"Arial\"&8Журнал арендных платежей  •  стр. &P из &N"
    ws.oddFooter.center.color = "7A7590"

def protect(ws, rows=False):
    """Защита формул без пароля: снимается одним щелчком, но случайно
    формулу не сотрёшь. Пароль намеренно не ставим — часть мобильных
    приложений считает лист с паролем полностью нередактируемым."""
    ws.protection.sheet = True
    ws.protection.enable()
    ws.protection.formatCells = False
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    ws.protection.sort = False
    ws.protection.autoFilter = False
    ws.protection.selectLockedCells = False
    ws.protection.selectUnlockedCells = False
    if rows:                       # в журнале разрешаем добавлять/удалять строки
        ws.protection.insertRows = False
        ws.protection.deleteRows = False

# ---------- книга ----------
wb = Workbook()
wb._named_styles["Normal"].font = Font(name=F, size=11, color=INK)

main = wb.active
main.title = "Главная"
reg  = wb.create_sheet("Регистрация")
hist = wb.create_sheet("История")
anal = wb.create_sheet("Аналитика")
ref  = wb.create_sheet("Справочники")

main.sheet_properties.tabColor = LIL
reg.sheet_properties.tabColor  = TRQ
hist.sheet_properties.tabColor = LIL_MID
anal.sheet_properties.tabColor = TRQ_MID
ref.sheet_properties.tabColor  = LIL_SOFT

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    ws.sheet_format.defaultRowHeight = 20

# =====================================================================
#  ГЛАВНАЯ
# =====================================================================
ws = main
for col, w in zip("ABCDE", (23, 17.5, 2.2, 23, 17.5)):
    ws.column_dimensions[col].width = w
paint(ws, "A1:E40", bg=WHITE)

banner(ws, "A1:E1", "ЖУРНАЛ АРЕНДНЫХ ПЛАТЕЖЕЙ")
put(ws, "A2:E2",
    '=IF(B5="","Заполните карточку договора ниже  ·  все итоги считаются автоматически",'
    'B5&"   •   "&IF(B6="","наниматель не указан",B6))',
    bg=TRQ_BG, font=Font(F, 10, color=TRQ_DEEP), align=A_C, h=24)
ws.row_dimensions[3].height = 8

# --- карточка договора ---
section(ws, "A4:E4", "  КАРТОЧКА ДОГОВОРА")

LBL   = Font(F, 10.5, color=MUTED)
LBL_A = Font(F, 10.5, bold=True, color=LIL)
INP   = Font(F, 11.5, bold=True, color=INK)
AUTO  = Font(F, 11.5, bold=True, color=LIL_DEEP)

def lbl(cell, text, auto=False):
    put(ws, cell, text, bg=WHITE, font=LBL_A if auto else LBL, align=A_L)

def inp(cell, fmt=None, hint=None):
    c = put(ws, cell, bg=WHITE, font=INP, align=A_R, fmt=fmt, unlock=True)
    box(ws, cell, TRQ_SOFT)
    return c

def auto(cell, formula, fmt=None):
    c = put(ws, cell, formula, bg=LIL_BG, font=AUTO, align=A_R, fmt=fmt)
    box(ws, cell, LIL_SOFT)
    return c

lbl("A5", "Адрес");        inp("B5:E5"); ws["B5"].alignment = A_L
lbl("A6", "Наниматель");   inp("B6:E6"); ws["B6"].alignment = A_L
lbl("A7", "Дата договора"); inp("B7", DATE_F)
lbl("D7", "Срок (мес.)");   inp("E7", '0" мес."')
lbl("A8", "🤖 Дата окончания", True)
auto("B8", '=IF(OR($B$7="",$E$7=""),"",EDATE($B$7,$E$7)-1)', DATE_F)
lbl("D8", "🤖 Осталось дней", True)
auto("E8", '=IF($B$8="","",IF($B$8<TODAY(),"договор истёк",MAX(0,$B$8-TODAY())&" дн."))')
lbl("A9", "Размер аренды");  inp("B9", RUB)
lbl("D9", "Размер залога");  inp("E9", RUB)
lbl("A10", "День платежа");  inp("B10", '0" число"')
lbl("D10", "🤖 Следующий платеж", True)
auto("E10", '=IF(COUNTIF(История!$F$%d:$F$%d,">0")=0,"нет долгов",'
            '_xlfn.MINIFS(История!$B$%d:$B$%d,История!$F$%d:$F$%d,">0"))'
            % (HS_FIRST, HS_LAST, HS_FIRST, HS_LAST, HS_FIRST, HS_LAST), DATE_F)
lbl("A11", "🤖 Статус", True)
put(ws, "B11:E11",
    '=IF($B$7="","Договор не заполнен — начните с карточки выше",'
    'IF(SUMIF(История!$F$%d:$F$%d,">0")>0,'
    '"⚠ Задолженность: "&TEXT(SUMIF(История!$F$%d:$F$%d,">0"),"#,##0")&" ₽",'
    '"✔ Задолженности нет — все платежи в срок"))' % (HS_FIRST, HS_LAST, HS_FIRST, HS_LAST),
    bg=LIL_BG, font=Font(F, 11.5, bold=True, color=LIL_DEEP), align=A_C, h=26)
box(ws, "B11:E11", LIL_SOFT)
for r in range(5, 12):
    ws.row_dimensions[r].height = 26
ws.row_dimensions[12].height = 12

# --- крупные карточки итогов ---
section(ws, "A13:E13", "  ФИНАНСЫ · ИТОГИ ПО ПОЗИЦИЯМ")
ws.row_dimensions[14].height = 6

CARDS = [
    # (левый столбец?, строка, заголовок, формула, подпись, цвета)
    ("A", 15, "🏠  ОПЛАЧЕНО ЗА АРЕНДУ",
     '=SUMIFS(J_SUM,J_CAT,"Аренда")',
     '="Платежей: "&COUNTIFS(J_CAT,"Аренда")&"   •   всего по договору: "'
     '&TEXT(IFERROR($B$9*$E$7,0),"#,##0")&" ₽"',
     (LIL_BG, LIL, LIL_DEEP, LIL_SOFT)),
    ("D", 15, "🧾  ОПЛАЧЕНО НАЛОГОВ",
     '=SUMIFS(J_SUM,J_CAT,"Налог")',
     '="Платежей: "&COUNTIFS(J_CAT,"Налог")&"   •   расчёт от аренды: "'
     '&TEXT(SUMIFS(J_SUM,J_CAT,"Аренда")*TAX_RATE,"#,##0")&" ₽"',
     (TRQ_BG, TRQ, TRQ_DEEP, TRQ_SOFT)),
    ("A", 19, "💡  ОПЛАЧЕНО ЗА КОММУНАЛЬНЫЕ УСЛУГИ",
     '=SUMIFS(J_SUM,J_CAT,"Коммунальные услуги")',
     '="Платежей: "&COUNTIFS(J_CAT,"Коммунальные услуги")&"   •   в среднем: "'
     '&TEXT(IFERROR(AVERAGEIFS(J_SUM,J_CAT,"Коммунальные услуги"),0),"#,##0")&" ₽"',
     (LIL_BG, LIL_MID, LIL_DEEP, LIL_SOFT)),
    ("D", 19, "🔐  ОПЛАТА ЗАЛОГА",
     '=SUMIFS(J_SUM,J_CAT,"Залог")',
     '="По договору: "&TEXT($E$9,"#,##0")&" ₽   •   "&'
     'IF(SUMIFS(J_SUM,J_CAT,"Залог")>=$E$9,"✔ внесён полностью",'
     '"осталось "&TEXT($E$9-SUMIFS(J_SUM,J_CAT,"Залог"),"#,##0")&" ₽")',
     (TRQ_BG, TRQ_MID, TRQ_DEEP, TRQ_SOFT)),
]
for col, r, title, formula, sub, (bg, accent, val_c, brd) in CARDS:
    c2 = get_column_letter(ord(col) - 64 + 1)
    rng = f"{col}{r}:{c2}{r+2}"
    paint(ws, rng, bg=bg)
    put(ws, f"{col}{r}:{c2}{r}", title, bg=bg,
        font=Font(F, 9.5, bold=True, color=accent), align=A_L, h=20)
    put(ws, f"{col}{r+1}:{c2}{r+1}", formula, bg=bg,
        font=Font(F, 22, bold=True, color=val_c),
        align=Alignment(horizontal="center", vertical="center"), fmt=RUB_BIG, h=42)
    put(ws, f"{col}{r+2}:{c2}{r+2}", sub, bg=bg,
        font=Font(F, 8.5, color=MUTED), align=A_C, h=20)
    box(ws, rng, brd)
ws.row_dimensions[18].height = 8
ws.row_dimensions[22].height = 12

# --- сводка ---
section(ws, "A23:E23", "  СВОДКА")
def kv(lc, vc, label, formula, fmt=RUB):
    put(ws, lc, label, bg=WHITE, font=LBL, align=A_L)
    put(ws, vc, formula, bg=LIL_BG, font=Font(F, 11.5, bold=True, color=LIL_DEEP),
        align=A_R, fmt=fmt)
    box(ws, vc, LIL_SOFT)

kv("A24", "B24", "Итого оплачено (все позиции)", "=SUM(J_SUM)")
kv("D24", "E24", "Оплачено в текущем году",
   '=SUMIFS(J_SUM,J_PER,">="&DATE(YEAR(TODAY()),1,1),J_PER,"<="&DATE(YEAR(TODAY()),12,31))')
kv("A25", "B25", "Текущий долг по аренде",
   '=SUMIF(История!$F$%d:$F$%d,">0")' % (HS_FIRST, HS_LAST))
kv("D25", "E25", "Записей в журнале", "=COUNT(J_SUM)", fmt='0" шт."')
ws.row_dimensions[24].height = 24
ws.row_dimensions[25].height = 24
ws.row_dimensions[26].height = 12

section(ws, "A27:E27", "  КАК ПОЛЬЗОВАТЬСЯ")
tips = [
    "1.  Заполните карточку договора — поля с бирюзовой рамкой (белый фон) открыты для ввода.",
    "2.  Каждый платёж вносите на листе «Регистрация»: дата, категория, сумма — месяц подставится сам.",
    "3.  Листы «История» и «Аналитика» и карточки итогов пересчитываются сами — их не трогаем.",
    "4.  Сиреневые ячейки 🤖 — формулы. Защита без пароля: «Рецензирование → Снять защиту листа».",
]
for i, t in enumerate(tips):
    put(ws, f"A{28+i}:E{28+i}", t, bg=LIL_BG if i % 2 == 0 else WHITE,
        font=Font(F, 9.5, color=MUTED), align=A_L, h=19)
box(ws, "A28:E31", LIL_SOFT)

# подсветка незаполненных обязательных полей
for rng in ("B5:E5", "B6:E6", "B7", "E7", "B9", "E9", "B10"):
    ws.conditional_formatting.add(rng, FormulaRule(
        formula=[f'{rng.split(":")[0]}=""'], fill=fill(AMBER_BG), stopIfTrue=False))
# статус договора
ws.conditional_formatting.add("B11:E11", FormulaRule(
    formula=['ISNUMBER(SEARCH("Задолженность",$B$11))'],
    fill=fill(RED_BG), font=Font(F, 11.5, bold=True, color=RED)))
ws.conditional_formatting.add("B11:E11", FormulaRule(
    formula=['ISNUMBER(SEARCH("нет",$B$11))'],
    fill=fill(GREEN_BG), font=Font(F, 11.5, bold=True, color=GREEN)))
# залог внесён полностью
ws.conditional_formatting.add("D20:E20", FormulaRule(
    formula=['AND($E$9>0,SUMIFS(J_SUM,J_CAT,"Залог")>=$E$9)'],
    font=Font(F, 22, bold=True, color=GREEN)))

dv_day = DataValidation(type="whole", operator="between", formula1=1, formula2=28,
                        allow_blank=True, showErrorMessage=True,
                        errorTitle="День платежа", error="Укажите число от 1 до 28.",
                        promptTitle="День платежа", prompt="Число месяца, до которого вносится аренда (1–28).")
dv_day.showInputMessage = True
dv_day.errorStyle = "warning"
ws.add_data_validation(dv_day); dv_day.add("B10")

dv_date = DataValidation(type="date", operator="greaterThan", formula1="DATE(2000,1,1)",
                         allow_blank=True, showErrorMessage=True,
                         errorTitle="Дата", error="Введите корректную дату (ДД.ММ.ГГГГ).")
dv_date.errorStyle = "warning"
ws.add_data_validation(dv_date); dv_date.add("B7")

dv_money = DataValidation(type="decimal", operator="greaterThanOrEqual", formula1=0,
                          allow_blank=True, showErrorMessage=True,
                          errorTitle="Сумма", error="Сумма не может быть отрицательной.")
dv_money.errorStyle = "warning"
ws.add_data_validation(dv_money); dv_money.add("B9"); dv_money.add("E9")

dv_term = DataValidation(type="whole", operator="between", formula1=1, formula2=120,
                         allow_blank=True, showErrorMessage=True,
                         errorTitle="Срок", error="Срок договора: от 1 до 120 месяцев.")
dv_term.errorStyle = "warning"
ws.add_data_validation(dv_term); dv_term.add("E7")

page(ws, "A1:E31")
ws.sheet_view.zoomScale = 100

# =====================================================================
#  РЕГИСТРАЦИЯ
# =====================================================================
ws = reg
widths = {"A": 5.5, "B": 12.5, "C": 17, "D": 14, "E": 13.5, "F": 15, "G": 21, "H": 14, "I": 14}
for c, w in widths.items():
    ws.column_dimensions[c].width = w
paint(ws, f"A1:I{JR_LAST+2}", bg=WHITE)

banner(ws, "A1:I1", "РЕГИСТРАЦИЯ ПЛАТЕЖЕЙ", "A2:I2",
       "Одна строка — один платёж. Достаточно заполнить: Дата · Категория · Сумма — "
       "месяц подставится сам из даты платежа",
       color=TRQ)
ws.row_dimensions[3].height = 6

# полоска быстрых итогов
stats = [
    ("A4:B4", '="Записей: "&COUNT($E$%d:$E$%d)' % (JR_FIRST, JR_LAST), None),
    ("C4:D4", '="Сумма: "&TEXT(SUM($E$%d:$E$%d),"#,##0")&" ₽"' % (JR_FIRST, JR_LAST), None),
    ("E4", '="Последняя запись:"', None),
    ("F4", '=IF(COUNT($B$%d:$B$%d)=0,"—",MAX($B$%d:$B$%d))'
           % (JR_FIRST, JR_LAST, JR_FIRST, JR_LAST), DATE_F),
    ("G4:I4", '="Предупреждений: "&COUNTIF($H$%d:$H$%d,"⚠*")' % (JR_FIRST, JR_LAST), None),
]
for rng, f_, fmt_ in stats:
    put(ws, rng, f_, bg=LIL_BG, font=Font(F, 10, bold=True, color=LIL_DEEP), align=A_C,
        fmt=fmt_, h=24)
    box(ws, rng, LIL_SOFT)
ws.row_dimensions[5].height = 10

heads = ["№", "Дата", "Категория", "Месяц (необяз.)", "Сумма", "Способ", "Комментарий",
         "🤖 Контроль", "🤖 Учтён за месяц"]
for i, h in enumerate(heads):
    c = ws.cell(row=6, column=i + 1, value=h)
    c.fill = fill(LIL)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.row_dimensions[6].height = 32
box(ws, "A6:I6", LIL_DEEP)

for r in range(JR_FIRST, JR_LAST + 1):
    ws.row_dimensions[r].height = 22
    ws.cell(row=r, column=1, value=f'=IF(B{r}="","",ROW()-{JR_FIRST-1})').number_format = "0"
    ws.cell(row=r, column=1).font = Font(F, 10, color=MUTED)
    ws.cell(row=r, column=1).alignment = A_C
    for col in range(2, 8):
        c = ws.cell(row=r, column=col)
        c.protection = Protection(locked=False)
        c.font = Font(F, 10.5, color=INK)
    ws.cell(row=r, column=2).number_format = DATE_F
    ws.cell(row=r, column=2).alignment = A_C
    ws.cell(row=r, column=3).alignment = A_L
    ws.cell(row=r, column=4).number_format = MON
    ws.cell(row=r, column=4).alignment = A_C
    ws.cell(row=r, column=5).number_format = RUB
    ws.cell(row=r, column=5).alignment = A_R
    ws.cell(row=r, column=5).font = Font(F, 10.5, bold=True, color=INK)
    ws.cell(row=r, column=6).alignment = A_L
    ws.cell(row=r, column=7).alignment = A_L
    ctl = ws.cell(row=r, column=8, value=(
        f'=IF(COUNTA(B{r}:G{r})=0,"",'
        f'IF(B{r}="","⚠ нет даты",'
        f'IF(C{r}="","⚠ нет категории",'
        f'IF(NOT(ISNUMBER(E{r})),"⚠ нет суммы",'
        f'IF(E{r}<=0,"⚠ сумма ≤ 0",'
        f'IF(AND(Главная!$B$7<>"",B{r}<Главная!$B$7),"⚠ дата до договора",'
        f'IF(B{r}>TODAY(),"ⓘ будущая дата","✓ ОК")))))))'))
    ctl.font = Font(F, 9.5, color=GREEN)
    ctl.alignment = A_C
    # месяц, за который засчитан платёж: указанный вручную или месяц даты платежа
    per = ws.cell(row=r, column=9, value=(
        f'=IF(COUNTA(B{r}:G{r})=0,"",IF(D{r}<>"",D{r},'
        f'IF(B{r}="","",DATE(YEAR(B{r}),MONTH(B{r}),1))))'))
    per.number_format = MON
    per.alignment = A_C
    per.font = Font(F, 9.5, color=LIL)
    for col in range(1, 10):
        ws.cell(row=r, column=col).border = Border(
            bottom=side("EDE9F5"),
            left=side("EDE9F5") if col == 1 else None,
            right=side("EDE9F5"))

# итоговая строка журнала
tr = JR_LAST + 1
put(ws, f"A{tr}:D{tr}", "ИТОГО ПО ЖУРНАЛУ", bg=LIL_BG2,
    font=Font(F, 11, bold=True, color=LIL_DEEP), align=A_R, h=26)
put(ws, f"E{tr}", f"=SUM(E{JR_FIRST}:E{JR_LAST})", bg=LIL_BG2,
    font=Font(F, 12, bold=True, color=LIL_DEEP), align=A_R, fmt=RUB)
put(ws, f"F{tr}:I{tr}", f'="записей: "&COUNT(E{JR_FIRST}:E{JR_LAST})', bg=LIL_BG2,
    font=Font(F, 10, color=MUTED), align=A_C)
box(ws, f"A{tr}:I{tr}", LIL_SOFT)

ws.auto_filter.ref = f"A6:I{JR_LAST}"
ws.freeze_panes = "B7"

# --- выпадающие списки ---
# errorStyle="warning" — если приложение не даёт выбрать пункт списка,
# значение всегда можно вписать руками, книга его примет.
def add_dv(dv, rng, prompt_title=None, prompt=None):
    dv.errorStyle = "warning"
    if prompt:
        dv.promptTitle = prompt_title
        dv.prompt = prompt
        dv.showInputMessage = True
    ws.add_data_validation(dv)
    dv.add(rng)
    return dv

add_dv(DataValidation(type="list", formula1="L_CAT", allow_blank=True,
                      showErrorMessage=True, errorTitle="Категория",
                      error="Обычно выбирают из списка. Оставить введённое значение?"),
       f"C{JR_FIRST}:C{JR_LAST}", "Категория платежа",
       "Выберите из списка или впишите: Аренда · Налог · Коммунальные услуги · Залог · Прочее")

add_dv(DataValidation(type="list", formula1="L_PER", allow_blank=True,
                      showErrorMessage=True, errorTitle="Месяц",
                      error="Обычно выбирают месяц из списка. Оставить введённое значение?"),
       f"D{JR_FIRST}:D{JR_LAST}", "Месяц — заполнять не обязательно",
       "Оставьте пусто — платёж зачтётся за месяц своей даты. "
       "Заполняйте только для аванса или погашения долга за другой месяц.")

add_dv(DataValidation(type="list", formula1="L_PAY", allow_blank=True,
                      showErrorMessage=True, errorTitle="Способ оплаты",
                      error="Обычно выбирают из списка. Оставить введённое значение?"),
       f"F{JR_FIRST}:F{JR_LAST}", "Способ оплаты",
       "Выберите из списка или впишите свой вариант.")

add_dv(DataValidation(type="decimal", operator="greaterThan", formula1=0, allow_blank=True,
                      showErrorMessage=True, errorTitle="Сумма",
                      error="Ожидается число больше нуля. Оставить как есть?"),
       f"E{JR_FIRST}:E{JR_LAST}")

add_dv(DataValidation(type="date", operator="greaterThan", formula1="DATE(2000,1,1)",
                      allow_blank=True, showErrorMessage=True, errorTitle="Дата",
                      error="Ожидается дата в формате ДД.ММ.ГГГГ. Оставить как есть?"),
       f"B{JR_FIRST}:B{JR_LAST}", "Дата платежа",
       "Введите дату, когда деньги получены, например 05.09.2026.")

# --- условное форматирование ---
rng_all = f"A{JR_FIRST}:I{JR_LAST}"
cat_colors = [("Аренда", LIL_BG2, LIL_DEEP), ("Налог", TRQ_BG, TRQ_DEEP),
              ("Коммунальные услуги", "EAF4FB", "1C5C87"), ("Залог", AMBER_BG, AMBER),
              ("Прочее", "F2F1F6", MUTED)]
for name, bg, fg in cat_colors:
    ws.conditional_formatting.add(f"C{JR_FIRST}:C{JR_LAST}", CellIsRule(
        operator="equal", formula=[f'"{name}"'], fill=fill(bg),
        font=Font(F, 10.5, bold=True, color=fg)))
ws.conditional_formatting.add(f"H{JR_FIRST}:H{JR_LAST}", FormulaRule(
    formula=[f'LEFT($H{JR_FIRST},1)="⚠"'], fill=fill(RED_BG), font=Font(F, 9.5, bold=True, color=RED)))
ws.conditional_formatting.add(f"H{JR_FIRST}:H{JR_LAST}", FormulaRule(
    formula=[f'LEFT($H{JR_FIRST},1)="ⓘ"'], fill=fill(AMBER_BG), font=Font(F, 9.5, bold=True, color=AMBER)))
ws.conditional_formatting.add(f"H{JR_FIRST}:H{JR_LAST}", FormulaRule(
    formula=[f'LEFT($H{JR_FIRST},1)="✓"'], font=Font(F, 9.5, color=GREEN)))
ws.conditional_formatting.add(rng_all, FormulaRule(
    formula=[f'AND($B{JR_FIRST}<>"",MOD(ROW(),2)=1)'], fill=fill("FAF8FE"), stopIfTrue=False))
ws.conditional_formatting.add(f"E{JR_FIRST}:E{JR_LAST}", DataBarRule(
    start_type="num", start_value=0, end_type="percentile", end_value=95,
    color=TRQ_SOFT, showValue=True))

page(ws, f"A1:I{min(JR_FIRST+49, JR_LAST)}", titles="1:6")
ws.sheet_view.zoomScale = 100

# =====================================================================
#  ИСТОРИЯ
# =====================================================================
ws = hist
for c, w in zip("ABCDEFG", (17, 13, 13, 14, 14, 14, 17)):
    ws.column_dimensions[c].width = w
paint(ws, f"A1:G{HS_LAST+3}", bg=WHITE)

banner(ws, "A1:G1", "ИСТОРИЯ НАЧИСЛЕНИЙ И ОПЛАТ", "A2:G2",
       "Лист считается автоматически по данным журнала «Регистрация» — ручной ввод не требуется",
       color=LIL_MID)
ws.row_dimensions[3].height = 6

hstats = [
    ("A4:B4", '="Начислено на сегодня: "&TEXT(SUM($D$%d:$D$%d),"#,##0")&" ₽"' % (HS_FIRST, HS_LAST)),
    ("C4:D4", '="Оплачено: "&TEXT(SUM($E$%d:$E$%d),"#,##0")&" ₽"' % (HS_FIRST, HS_LAST)),
    ("E4:F4", '="Текущий долг: "&TEXT(SUMIF($F$%d:$F$%d,">0"),"#,##0")&" ₽"' % (HS_FIRST, HS_LAST)),
    ("G4", '="Закрыто: "&COUNTIF($G$%d:$G$%d,"✔*")&" мес."' % (HS_FIRST, HS_LAST)),
]
for rng, f_ in hstats:
    put(ws, rng, f_, bg=TRQ_BG, font=Font(F, 10, bold=True, color=TRQ_DEEP), align=A_C, h=24)
    box(ws, rng, TRQ_SOFT)

heads = ["Месяц", "Срок", "Дата", "Начислено", "Оплачено", "Долг", "Статус"]
for i, h in enumerate(heads):
    c = ws.cell(row=5, column=i + 1, value=h)
    c.fill = fill(LIL)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.row_dimensions[5].height = 30
box(ws, "A5:G5", LIL_DEEP)

for r in range(HS_FIRST, HS_LAST + 1):
    i = r - HS_FIRST
    ws.row_dimensions[r].height = 22
    ws.cell(row=r, column=1, value=(
        f'=IF(OR(Главная!$B$7="",{i+1}>IFERROR(Главная!$E$7,0)),"",'
        f'DATE(YEAR(EDATE(Главная!$B$7,{i})),MONTH(EDATE(Главная!$B$7,{i})),1))'))
    ws.cell(row=r, column=2, value=(
        f'=IF($A{r}="","",MIN($A{r}+MAX(1,IFERROR(Главная!$B$10,1))-1,EOMONTH($A{r},0)))'))
    ws.cell(row=r, column=3, value=(
        f'=IF($A{r}="","",IF(_xlfn.MAXIFS(J_DATE,J_PER,$A{r},J_CAT,"Аренда")=0,"",'
        f'_xlfn.MAXIFS(J_DATE,J_PER,$A{r},J_CAT,"Аренда")))'))
    ws.cell(row=r, column=4, value=(
        f'=IF($A{r}="","",IF(AND({i+1}<=IFERROR(Главная!$E$7,0),$A{r}<=TODAY()),'
        f'IFERROR(Главная!$B$9,0),0))'))
    ws.cell(row=r, column=5, value=(
        f'=IF($A{r}="","",SUMIFS(J_SUM,J_PER,$A{r},J_CAT,"Аренда"))'))
    ws.cell(row=r, column=6, value=f'=IF($A{r}="","",$D{r}-$E{r})')
    ws.cell(row=r, column=7, value=(
        f'=IF($A{r}="","",'
        f'IF($D{r}=0,'
        f'IF($E{r}>0,"✔ Оплачено авансом","⏳ Ожидается"),'
        f'IF($E{r}>=$D{r},"✔ Оплачено",'
        f'IF(AND($E{r}>0,TODAY()>$B{r}),"◐ Частично, просрочено",'
        f'IF($E{r}>0,"◐ Частично",'
        f'IF(TODAY()>$B{r},"⚠ Просрочено","⏳ Ожидается"))))))'))
    ws.cell(row=r, column=1).number_format = MON
    ws.cell(row=r, column=1).font = Font(F, 10.5, bold=True, color=LIL_DEEP)
    ws.cell(row=r, column=1).alignment = A_L
    ws.cell(row=r, column=2).number_format = DATE_F
    ws.cell(row=r, column=3).number_format = DATE_F
    for col in (2, 3):
        ws.cell(row=r, column=col).alignment = A_C
        ws.cell(row=r, column=col).font = Font(F, 10, color=MUTED)
    for col in (4, 5, 6):
        ws.cell(row=r, column=col).number_format = RUB
        ws.cell(row=r, column=col).alignment = A_R
        ws.cell(row=r, column=col).font = Font(F, 10.5, color=INK)
    ws.cell(row=r, column=6).font = Font(F, 10.5, bold=True, color=INK)
    ws.cell(row=r, column=7).alignment = A_C
    ws.cell(row=r, column=7).font = Font(F, 10, bold=True, color=INK)
    for col in range(1, 8):
        ws.cell(row=r, column=col).border = Border(bottom=side("EDE9F5"),
                                                   left=side("EDE9F5") if col == 1 else None,
                                                   right=side("EDE9F5"))

tr = HS_LAST + 1
put(ws, f"A{tr}:C{tr}", "ИТОГО", bg=LIL_BG2, font=Font(F, 11, bold=True, color=LIL_DEEP),
    align=A_R, h=26)
for col, letter in ((4, "D"), (5, "E"), (6, "F")):
    put(ws, f"{letter}{tr}", f"=SUM({letter}{HS_FIRST}:{letter}{HS_LAST})", bg=LIL_BG2,
        font=Font(F, 12, bold=True, color=LIL_DEEP), align=A_R, fmt=RUB)
put(ws, f"G{tr}", f'=IF(SUM(F{HS_FIRST}:F{HS_LAST})>0,"есть долг","всё оплачено")',
    bg=LIL_BG2, font=Font(F, 10, bold=True, color=LIL_DEEP), align=A_C)
box(ws, f"A{tr}:G{tr}", LIL_SOFT)
put(ws, f"A{tr+1}:G{tr+1}",
    f'="Просроченный долг (сумма положительных остатков): "'
    f'&TEXT(SUMIF(F{HS_FIRST}:F{HS_LAST},">0"),"#,##0")&" ₽"'
    f'&IF(SUMIF(F{HS_FIRST}:F{HS_LAST},"<0")<0,'
    f'"   •   оплачено авансом: "&TEXT(-SUMIF(F{HS_FIRST}:F{HS_LAST},"<0"),"#,##0")&" ₽","")'
    f'&"   •   в столбце «Долг» показан итог с учётом авансов"',
    bg=WHITE, font=Font(F, 8.5, color=MUTED), align=A_C, h=28)

ws.freeze_panes = "A6"
rng = f"A{HS_FIRST}:G{HS_LAST}"
ws.conditional_formatting.add(f"F{HS_FIRST}:F{HS_LAST}", CellIsRule(
    operator="greaterThan", formula=["0"], fill=fill(RED_BG), font=Font(F, 10.5, bold=True, color=RED)))
ws.conditional_formatting.add(f"F{HS_FIRST}:F{HS_LAST}", CellIsRule(
    operator="lessThan", formula=["0"], font=Font(F, 10.5, bold=True, color=TRQ_DEEP)))
for pat, bg, fg in (("Частично", AMBER_BG, AMBER), ("Оплачено", GREEN_BG, GREEN),
                    ("Просрочено", RED_BG, RED), ("Ожидается", LIL_BG, LIL)):
    ws.conditional_formatting.add(f"G{HS_FIRST}:G{HS_LAST}", FormulaRule(
        formula=[f'ISNUMBER(SEARCH("{pat}",$G{HS_FIRST}))'],
        fill=fill(bg), font=Font(F, 10, bold=True, color=fg), stopIfTrue=True))

ws.conditional_formatting.add(rng, FormulaRule(
    formula=[f'AND($A{HS_FIRST}<>"",$A{HS_FIRST}=DATE(YEAR(TODAY()),MONTH(TODAY()),1))'],
    fill=fill(TRQ_BG), stopIfTrue=False))
ws.conditional_formatting.add(rng, FormulaRule(
    formula=[f'AND($A{HS_FIRST}<>"",MOD(ROW(),2)=0)'], fill=fill("FAF8FE"), stopIfTrue=False))

page(ws, f"A1:G{tr+1}", titles="1:5", fit_h=1)
ws.sheet_view.zoomScale = 100

# =====================================================================
#  АНАЛИТИКА
# =====================================================================
ws = anal
for c, w in zip("ABCDEFG", (17, 14, 13, 17, 12, 12, 14)):
    ws.column_dimensions[c].width = w
paint(ws, "A1:G70", bg=WHITE)

banner(ws, "A1:G1", "АНАЛИТИКА ПЛАТЕЖЕЙ", "A2:G2",
       "Разбивка по месяцам, годам и способам оплаты — считается автоматически", color=TRQ_MID)
ws.row_dimensions[3].height = 6

section(ws, "A4:G4", "  ПО МЕСЯЦАМ")
cols = ["Месяц", "Аренда", "Налоги", "Коммуналка", "Залог", "Прочее", "Итого"]
for i, h in enumerate(cols):
    c = ws.cell(row=5, column=i + 1, value=h)
    c.fill = fill(TRQ)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.row_dimensions[5].height = 30
box(ws, "A5:G5", TRQ_DEEP)
ws.row_dimensions[6].height = 4

CATS = ["Аренда", "Налог", "Коммунальные услуги", "Залог", "Прочее"]
for r in range(AN_FIRST, AN_LAST + 1):
    hr = HS_FIRST + (r - AN_FIRST)
    ws.row_dimensions[r].height = 21
    ws.cell(row=r, column=1, value=f'=IF(История!$A${hr}="","",История!$A${hr})')
    ws.cell(row=r, column=1).number_format = MON
    ws.cell(row=r, column=1).font = Font(F, 10.5, bold=True, color=LIL_DEEP)
    ws.cell(row=r, column=1).alignment = A_L
    for j, cat in enumerate(CATS):
        c = ws.cell(row=r, column=2 + j,
                    value=f'=IF($A{r}="","",SUMIFS(J_SUM,J_PER,$A{r},J_CAT,"{cat}"))')
        c.number_format = RUB
        c.alignment = A_R
        c.font = Font(F, 10, color=INK)
    t = ws.cell(row=r, column=7, value=f'=IF($A{r}="","",SUM($B{r}:$F{r}))')
    t.number_format = RUB
    t.alignment = A_R
    t.font = Font(F, 10.5, bold=True, color=TRQ_DEEP)
    for col in range(1, 8):
        ws.cell(row=r, column=col).border = Border(bottom=side("EDE9F5"),
                                                   left=side("EDE9F5") if col == 1 else None,
                                                   right=side("EDE9F5"))

tr = AN_LAST + 1
put(ws, f"A{tr}", "ИТОГО", bg=TRQ_BG, font=Font(F, 11, bold=True, color=TRQ_DEEP), align=A_L, h=26)
for j in range(2, 8):
    letter = get_column_letter(j)
    put(ws, f"{letter}{tr}", f"=SUM({letter}{AN_FIRST}:{letter}{AN_LAST})", bg=TRQ_BG,
        font=Font(F, 11, bold=True, color=TRQ_DEEP), align=A_R, fmt=RUB)
box(ws, f"A{tr}:G{tr}", TRQ_SOFT)

ws.conditional_formatting.add(f"A{AN_FIRST}:G{AN_LAST}", FormulaRule(
    formula=[f'AND($A{AN_FIRST}<>"",MOD(ROW(),2)=0)'], fill=fill("FAF8FE")))
ws.conditional_formatting.add(f"G{AN_FIRST}:G{AN_LAST}", DataBarRule(
    start_type="num", start_value=0, end_type="percentile", end_value=95,
    color=TRQ_SOFT, showValue=True))
ws.freeze_panes = "A7"

# --- по годам ---
yr0 = tr + 2
section(ws, f"A{yr0}:G{yr0}", "  ПО ГОДАМ")
for i, h in enumerate(["Год", "Аренда", "Налоги", "Коммуналка", "Залог", "Прочее", "Итого"]):
    c = ws.cell(row=yr0 + 1, column=i + 1, value=h)
    c.fill = fill(LIL)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.row_dimensions[yr0 + 1].height = 26
for k in range(5):
    r = yr0 + 2 + k
    ws.row_dimensions[r].height = 21
    ws.cell(row=r, column=1, value=f'=IF(Главная!$B$7="","",YEAR(Главная!$B$7)+{k})')
    ws.cell(row=r, column=1).number_format = "0"
    ws.cell(row=r, column=1).alignment = A_C
    ws.cell(row=r, column=1).font = Font(F, 10.5, bold=True, color=LIL_DEEP)
    for j, cat in enumerate(CATS):
        c = ws.cell(row=r, column=2 + j, value=(
            f'=IF($A{r}="","",SUMIFS(J_SUM,J_CAT,"{cat}",J_PER,">="&DATE($A{r},1,1),'
            f'J_PER,"<="&DATE($A{r},12,31)))'))
        c.number_format = RUB
        c.alignment = A_R
        c.font = Font(F, 10, color=INK)
    t = ws.cell(row=r, column=7, value=f'=IF($A{r}="","",SUM($B{r}:$F{r}))')
    t.number_format = RUB
    t.alignment = A_R
    t.font = Font(F, 10.5, bold=True, color=LIL_DEEP)
    for col in range(1, 8):
        ws.cell(row=r, column=col).border = Border(bottom=side("EDE9F5"),
                                                   left=side("EDE9F5") if col == 1 else None,
                                                   right=side("EDE9F5"))
ws.conditional_formatting.add(f"G{yr0+2}:G{yr0+6}", DataBarRule(
    start_type="num", start_value=0, end_type="percentile", end_value=95,
    color=LIL_SOFT, showValue=True))

# --- по способам оплаты ---
pm0 = yr0 + 8
section(ws, f"A{pm0}:D{pm0}", "  ПО СПОСОБАМ ОПЛАТЫ")
for i, h in enumerate(["Способ", "Сумма", "Доля", "Платежей"]):
    c = ws.cell(row=pm0 + 1, column=i + 1, value=h)
    c.fill = fill(TRQ)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.row_dimensions[pm0 + 1].height = 26
for k in range(6):
    r = pm0 + 2 + k
    ws.row_dimensions[r].height = 21
    ws.cell(row=r, column=1, value=f'=IF(Справочники!$C${11+k}="","",Справочники!$C${11+k})')
    ws.cell(row=r, column=1).font = Font(F, 10.5, color=INK)
    ws.cell(row=r, column=1).alignment = A_L
    ws.cell(row=r, column=2, value=f'=IF($A{r}="","",SUMIFS(J_SUM,J_PAY,$A{r}))')
    ws.cell(row=r, column=2).number_format = RUB
    ws.cell(row=r, column=2).alignment = A_R
    ws.cell(row=r, column=2).font = Font(F, 10.5, bold=True, color=TRQ_DEEP)
    ws.cell(row=r, column=3, value=f'=IF($A{r}="","",IFERROR($B{r}/SUM(J_SUM),0))')
    ws.cell(row=r, column=3).number_format = PCT
    ws.cell(row=r, column=3).alignment = A_C
    ws.cell(row=r, column=4, value=f'=IF($A{r}="","",COUNTIFS(J_PAY,$A{r}))')
    ws.cell(row=r, column=4).number_format = '0" шт."'
    ws.cell(row=r, column=4).alignment = A_C
    ws.cell(row=r, column=4).font = Font(F, 10, color=MUTED)
    for col in range(1, 5):
        ws.cell(row=r, column=col).border = Border(bottom=side("EDE9F5"),
                                                   left=side("EDE9F5") if col == 1 else None,
                                                   right=side("EDE9F5"))
ws.conditional_formatting.add(f"C{pm0+2}:C{pm0+7}", DataBarRule(
    start_type="num", start_value=0, end_type="num", end_value=1,
    color=TRQ_SOFT, showValue=True))

page(ws, f"A1:G{pm0+8}", titles="1:5", fit_h=1)
ws.sheet_view.zoomScale = 100

# =====================================================================
#  СПРАВОЧНИКИ
# =====================================================================
ws = ref
for c, w in zip("ABCDE", (30, 16, 22, 22, 22)):
    ws.column_dimensions[c].width = w
paint(ws, "A1:E36", bg=WHITE)

banner(ws, "A1:E1", "СПРАВОЧНИКИ И НАСТРОЙКИ", "A2:E2",
       "Списки ниже подставляются в выпадающие меню журнала — их можно менять", color=LIL_DEEP)
ws.row_dimensions[3].height = 6

section(ws, "A4:E4", "  НАСТРОЙКИ РАСЧЁТА")
settings = [
    (5, "Ставка налога (НПД/НДФЛ)", 0.06, PCT, "Используется в карточке «Оплачено налогов» для справочного расчёта"),
    (6, "Плановая коммуналка, ₽/мес", 5000, RUB, "Ориентир для сравнения фактических платежей"),
    (7, "Напомнить за N дней до срока", 3, '0" дн."', "Через сколько дней до срока подсвечивать платёж"),
]
for r, label, val, fmt, note in settings:
    put(ws, f"A{r}", label, bg=WHITE, font=Font(F, 10.5, color=MUTED), align=A_L, h=24)
    c = put(ws, f"B{r}", val, bg=WHITE, font=Font(F, 11.5, bold=True, color=INK),
            align=A_R, fmt=fmt, unlock=True)
    box(ws, f"B{r}", TRQ_SOFT)
    put(ws, f"C{r}:E{r}", note, bg=WHITE, font=Font(F, 9, color=MUTED), align=A_L)
ws.row_dimensions[8].height = 12

section(ws, "A9:E9", "  СПИСКИ ДЛЯ ВЫПАДАЮЩИХ МЕНЮ")
for i, h in enumerate(["Категории платежей", "", "Способы оплаты", "Статусы (справочно)", "Годы"]):
    if not h:
        continue
    c = ws.cell(row=10, column=i + 1, value=h)
    c.fill = fill(TRQ)
    c.font = Font(F, 10, bold=True, color=WHITE)
    c.alignment = A_C
ws.merge_cells("A10:B10")
ws.row_dimensions[10].height = 26

cats = ["Аренда", "Налог", "Коммунальные услуги", "Залог", "Прочее"]
pays = ["Наличные", "Перевод СБП", "Банковская карта", "Расчётный счёт", "Почтовый перевод", "Другое"]
stats_l = ["✔ Оплачено", "◐ Частично", "⚠ Просрочено", "⏳ Ожидается", "—"]
for i in range(6):
    r = 11 + i
    ws.row_dimensions[r].height = 21
    if i < len(cats):
        put(ws, f"A{r}:B{r}", cats[i], bg=LIL_BG, font=Font(F, 10.5, bold=True, color=LIL_DEEP),
            align=A_L, unlock=True)
        box(ws, f"A{r}:B{r}", LIL_SOFT)
    if i < len(pays):
        put(ws, f"C{r}", pays[i], bg=TRQ_BG, font=Font(F, 10.5, color=TRQ_DEEP), align=A_L, unlock=True)
        box(ws, f"C{r}", TRQ_SOFT)
    if i < len(stats_l):
        put(ws, f"D{r}", stats_l[i], bg=WHITE, font=Font(F, 10.5, color=MUTED), align=A_L)
        box(ws, f"D{r}", "EDE9F5")
    if i < 5:
        put(ws, f"E{r}", f'=IF(Главная!$B$7="","",YEAR(Главная!$B$7)+{i})', bg=WHITE,
            font=Font(F, 10.5, color=MUTED), align=A_C, fmt="0")
        box(ws, f"E{r}", "EDE9F5")

ws.row_dimensions[17].height = 12
section(ws, "A18:E18", "  ЛЕГЕНДА ОФОРМЛЕНИЯ")
legend = [
    (WHITE, TRQ_SOFT, "Белое поле с бирюзовой рамкой", "ячейка для ручного ввода — её можно заполнять"),
    (LIL_BG, LIL_SOFT, "Сиреневая ячейка со значком 🤖", "формула, защищена от изменений"),
    (GREEN_BG, GREEN_BG, "Зелёная подсветка", "оплачено полностью / ошибок нет"),
    (AMBER_BG, AMBER_BG, "Янтарная подсветка", "частичная оплата или незаполненное поле"),
    (RED_BG, RED_BG, "Красная подсветка", "просрочка, долг или ошибка ввода"),
]
for i, (bg, brd, name, note) in enumerate(legend):
    r = 19 + i
    ws.row_dimensions[r].height = 21
    put(ws, f"A{r}", name, bg=bg, font=Font(F, 10, bold=True, color=INK), align=A_L)
    box(ws, f"A{r}", brd)
    put(ws, f"B{r}:E{r}", note, bg=WHITE, font=Font(F, 9.5, color=MUTED), align=A_L)

ws.row_dimensions[24].height = 12
section(ws, "A25:E25", "  ПАМЯТКА: ПРИМЕР ЗАПОЛНЕНИЯ СТРОКИ ЖУРНАЛА")
example = [
    ("Дата", "05.08.2026"), ("Категория", "Аренда"), ("Месяц (период)", "август 2026"),
    ("Сумма", "45 000 ₽"), ("Способ", "Перевод СБП"),
]
for i, (k, v) in enumerate(example):
    r = 26 + i
    ws.row_dimensions[r].height = 20
    put(ws, f"A{r}", k, bg=WHITE, font=Font(F, 10, color=MUTED), align=A_L)
    put(ws, f"B{r}:C{r}", v, bg=LIL_BG, font=Font(F, 10.5, bold=True, color=LIL_DEEP), align=A_L)
    box(ws, f"B{r}:C{r}", LIL_SOFT)
put(ws, "D26:E30",
    "Это только образец на память — копировать ничего не нужно. "
    "Столбец «Месяц» можно не заполнять: платёж зачтётся за месяц своей даты, "
    "а колонка «🤖 Учтён за месяц» покажет результат. "
    "Значения можно выбирать из списка или вписывать вручную. "
    "Листы защищены без пароля: «Рецензирование → Снять защиту листа».",
    bg=TRQ_BG, font=Font(F, 9.5, color=TRQ_DEEP),
    align=Alignment(horizontal="left", vertical="top", wrap_text=True))
box(ws, "D26:E30", TRQ_SOFT)

page(ws, "A1:E31")
ws.sheet_view.zoomScale = 100

# =====================================================================
#  ИМЕНОВАННЫЕ ДИАПАЗОНЫ
# =====================================================================
names = {
    "RENT":      f"Главная!$B$9",
    "DEPOSIT":   f"Главная!$E$9",
    "DOG_DATE":  f"Главная!$B$7",
    "TERM_M":    f"Главная!$E$7",
    "PAY_DAY":   f"Главная!$B$10",
    "END_DATE":  f"Главная!$B$8",
    "TAX_RATE":  f"Справочники!$B$5",
    "COMM_PLAN": f"Справочники!$B$6",
    "REMIND_D":  f"Справочники!$B$7",
    "L_CAT":     f"Справочники!$A$11:$A$15",
    "L_PAY":     f"Справочники!$C$11:$C$16",
    "L_PER":     f"История!$A${HS_FIRST}:$A${HS_LAST}",
    "J_DATE":    f"Регистрация!$B${JR_FIRST}:$B${JR_LAST}",
    "J_CAT":     f"Регистрация!$C${JR_FIRST}:$C${JR_LAST}",
    "J_PER":     f"Регистрация!$I${JR_FIRST}:$I${JR_LAST}",
    "J_SUM":     f"Регистрация!$E${JR_FIRST}:$E${JR_LAST}",
    "J_PAY":     f"Регистрация!$F${JR_FIRST}:$F${JR_LAST}",
}
for n, t in names.items():
    wb.defined_names.add(DefinedName(n, attr_text=t))

for ws_ in wb.worksheets:
    protect(ws_, rows=(ws_ is reg))

wb.calculation.fullCalcOnLoad = True   # Excel/мобильный Excel пересчитает всё при открытии
wb.active = 0
wb.save(OUT)
print("saved:", OUT)
