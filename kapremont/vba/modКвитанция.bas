Attribute VB_Name = "modКвитанция"
'==========================================================================
' Квитанция на взнос за капитальный ремонт (специальный счёт МКД)
' Модуль интеграции бланка КВИТАНЦИЯ с таблицей разноски.
'
' Импорт: Alt+F11 -> File -> Import File -> modКвитанция.bas
' Книгу после этого сохранить как .xlsm.
'
' Что здесь есть:
'   ПодставитьСуммы          — записать начисления по лицевому счёту
'   СформироватьКвитанцию    — показать бланк по лицевому счёту
'   СхемаЧБ / СхемаЦвет      — переключить оформление вручную
'   ПечатьКвитанции          — печать на А4 в чёрно-белом виде
'   ЭкспортКвитанцииВPDF     — цветной PDF для отправки жителю
'   ПакетныйЭкспортPDF       — цветные PDF по всем лицевым счетам
'   СтрокаQR                 — строка платежа по ГОСТ Р 56042-2014
'==========================================================================
Option Explicit

Private Const ЛИСТ_КВИТАНЦИИ As String = "КВИТАНЦИЯ"
Private Const ЛИСТ_ДАННЫХ As String = "ДАННЫЕ"
Private Const ЛИСТ_НАСТРОЕК As String = "НАСТРОЙКИ"
Private Const ЛИСТ_СХЕМЫ As String = "СХЕМА"

Private Const СХЕМА_ЧБ As String = "ЧБ"
Private Const СХЕМА_ЦВЕТ As String = "ЦВЕТ"

' Столбцы листа ДАННЫЕ
Private Const К_ЛС As Long = 1
Private Const К_КВАРТИРА As Long = 2
Private Const К_ФИО As Long = 3
Private Const К_АДРЕС As Long = 4
Private Const К_ПЛОЩАДЬ As Long = 5
Private Const К_ТАРИФ As Long = 6
Private Const К_НАЧИСЛЕНО As Long = 7
Private Const К_ДОЛГ As Long = 8
Private Const К_ПЕРЕРАСЧЕТ As Long = 9
Private Const К_ИТОГО As Long = 10
Private Const К_ОПЛАЧЕНО As Long = 11
Private Const К_ОСТАТОК As Long = 12
Private Const К_ПЕРИОД As Long = 13
Private Const К_ДАТА_ПЕРИОДА As Long = 14
Private Const К_СРОК As Long = 15

Private Const ПОСЛЕДНИЙ_СТОЛБЕЦ As Long = 15


'==========================================================================
' 1. Разноска -> лист ДАННЫЕ
'==========================================================================

' Записать начисления по одному лицевому счёту.
' Строка создаётся, если её ещё нет; существующая — обновляется.
' Пустые (Empty) аргументы не затирают то, что уже лежит в листе.
' Пени в этом доме не начисляются, поэтому их здесь нет — ни в аргументах,
' ни в листе ДАННЫЕ, ни в бланке.
Public Sub ПодставитьСуммы(ByVal ЛицевойСчет As Variant, _
                           Optional ByVal Начислено As Variant, _
                           Optional ByVal Долг As Variant, _
                           Optional ByVal Перерасчет As Variant, _
                           Optional ByVal Итого As Variant, _
                           Optional ByVal Оплачено As Variant)
    Dim ws As Worksheet, стр As Long

    Set ws = ЛистПоИмени(ЛИСТ_ДАННЫХ)
    стр = НайтиИлиДобавитьСтроку(ws, ЛицевойСчет)

    ЗаписатьЕслиЗадано ws, стр, К_НАЧИСЛЕНО, Начислено
    ЗаписатьЕслиЗадано ws, стр, К_ДОЛГ, Долг
    ЗаписатьЕслиЗадано ws, стр, К_ПЕРЕРАСЧЕТ, Перерасчет
    ЗаписатьЕслиЗадано ws, стр, К_ИТОГО, Итого
    ЗаписатьЕслиЗадано ws, стр, К_ОПЛАЧЕНО, Оплачено

    ' Итог не передали — считаем его сами, чтобы бланк не пересчитывал вслепую.
    If IsMissing(Итого) Or IsEmpty(Итого) Then
        ws.Cells(стр, К_ИТОГО).Value = Round( _
            Ноль(ws.Cells(стр, К_НАЧИСЛЕНО).Value) + _
            Ноль(ws.Cells(стр, К_ДОЛГ).Value) + _
            Ноль(ws.Cells(стр, К_ПЕРЕРАСЧЕТ).Value), 2)
    End If
End Sub

' Записать сведения о помещении и собственнике (обычно один раз на дом).
Public Sub ПодставитьПлательщика(ByVal ЛицевойСчет As Variant, _
                                 Optional ByVal Квартира As Variant, _
                                 Optional ByVal ФИО As Variant, _
                                 Optional ByVal Адрес As Variant, _
                                 Optional ByVal Площадь As Variant, _
                                 Optional ByVal Тариф As Variant)
    Dim ws As Worksheet, стр As Long

    Set ws = ЛистПоИмени(ЛИСТ_ДАННЫХ)
    стр = НайтиИлиДобавитьСтроку(ws, ЛицевойСчет)

    ЗаписатьЕслиЗадано ws, стр, К_КВАРТИРА, Квартира
    ЗаписатьЕслиЗадано ws, стр, К_ФИО, ФИО
    ЗаписатьЕслиЗадано ws, стр, К_АДРЕС, Адрес
    ЗаписатьЕслиЗадано ws, стр, К_ПЛОЩАДЬ, Площадь
    ЗаписатьЕслиЗадано ws, стр, К_ТАРИФ, Тариф
End Sub

' Проставить расчётный период и, если он отличается от общего, срок оплаты.
' Номера документа в квитанции нет — период начисления его заменяет.
Public Sub ПодставитьПериод(ByVal ЛицевойСчет As Variant, _
                            Optional ByVal ПериодТекст As Variant, _
                            Optional ByVal ДатаПериода As Variant, _
                            Optional ByVal СрокОплаты As Variant)
    Dim ws As Worksheet, стр As Long

    Set ws = ЛистПоИмени(ЛИСТ_ДАННЫХ)
    стр = НайтиИлиДобавитьСтроку(ws, ЛицевойСчет)

    ЗаписатьЕслиЗадано ws, стр, К_ПЕРИОД, ПериодТекст
    ЗаписатьЕслиЗадано ws, стр, К_ДАТА_ПЕРИОДА, ДатаПериода
    ЗаписатьЕслиЗадано ws, стр, К_СРОК, СрокОплаты
End Sub

' Показать бланк по лицевому счёту. Всё остальное подтянут формулы.
Public Sub СформироватьКвитанцию(ByVal ЛицевойСчет As Variant)
    Dim ws As Worksheet

    Set ws = ЛистПоИмени(ЛИСТ_КВИТАНЦИИ)
    ws.Range("КВ_ЛС").Value = ЛицевойСчет
    Application.Calculate
End Sub


'==========================================================================
' 2. Цветовые схемы
'==========================================================================

' Перекрасить бланк по таблице на листе СХЕМА.
' Схема: "ЧБ" — для печати на бумаге, "ЦВЕТ" — для PDF.
Public Sub ПрименитьСхему(ByVal Схема As String)
    Dim wsБланк As Worksheet, wsСхема As Worksheet
    Dim стр As Long, столбЗаливки As Long, столбШрифта As Long
    Dim диапазоны As Variant, i As Long
    Dim адрес As String

    Set wsБланк = ЛистПоИмени(ЛИСТ_КВИТАНЦИИ)
    Set wsСхема = ЛистПоИмени(ЛИСТ_СХЕМЫ)

    If UCase$(Схема) = UCase$(СХЕМА_ЦВЕТ) Then
        столбЗаливки = 5: столбШрифта = 6
    Else
        Схема = СХЕМА_ЧБ
        столбЗаливки = 3: столбШрифта = 4
    End If

    Application.ScreenUpdating = False

    стр = 2
    Do While Len(Trim$(CStr(wsСхема.Cells(стр, 1).Value))) > 0
        диапазоны = Split(CStr(wsСхема.Cells(стр, 2).Value), ",")
        For i = LBound(диапазоны) To UBound(диапазоны)
            адрес = Trim$(диапазоны(i))
            If Len(адрес) > 0 Then
                With wsБланк.Range(адрес)
                    .Interior.Color = ЦветИзHex(wsСхема.Cells(стр, столбЗаливки).Value)
                    .Font.Color = ЦветИзHex(wsСхема.Cells(стр, столбШрифта).Value)
                End With
            End If
        Next i
        стр = стр + 1
    Loop

    ЛистПоИмени(ЛИСТ_НАСТРОЕК).Range("КВ_СХЕМА").Value = Схема
    Application.ScreenUpdating = True
End Sub

Public Sub СхемаЧБ()
    ПрименитьСхему СХЕМА_ЧБ
End Sub

Public Sub СхемаЦвет()
    ПрименитьСхему СХЕМА_ЦВЕТ
End Sub


'==========================================================================
' 3. Печать и PDF
'==========================================================================

' Печать на А4 в чёрно-белом виде.
Public Sub ПечатьКвитанции()
    Dim исходнаяСхема As String

    исходнаяСхема = ТекущаяСхема()
    ПрименитьСхему СХЕМА_ЧБ
    Application.Calculate
    ЛистПоИмени(ЛИСТ_КВИТАНЦИИ).PrintOut
    ПрименитьСхему исходнаяСхема
End Sub

' Цветной PDF — для отправки жителю по электронной почте.
' Возвращает путь к созданному файлу.
Public Function ЭкспортКвитанцииВPDF(Optional ByVal Папка As String = "", _
                                     Optional ByVal ИмяФайла As String = "") As String
    Dim ws As Worksheet
    Dim исходнаяСхема As String
    Dim путь As String

    Set ws = ЛистПоИмени(ЛИСТ_КВИТАНЦИИ)
    исходнаяСхема = ТекущаяСхема()

    If Len(Папка) = 0 Then Папка = ThisWorkbook.Path
    If Len(ИмяФайла) = 0 Then ИмяФайла = ИмяФайлаКвитанции(ws)
    путь = СклеитьПуть(Папка, ИмяФайла)

    ' Бумага остаётся чёрно-белой, в PDF уходит цветной вид.
    ПрименитьСхему СХЕМА_ЦВЕТ
    Application.Calculate

    ws.ExportAsFixedFormat Type:=xlTypePDF, _
                           Filename:=путь, _
                           Quality:=xlQualityStandard, _
                           IncludeDocProperties:=False, _
                           IgnorePrintAreas:=False, _
                           OpenAfterPublish:=False

    ПрименитьСхему исходнаяСхема
    ЭкспортКвитанцииВPDF = путь
End Function

' Обёртка для кнопки и списка макросов (функции в нём не показываются).
Public Sub ЭкспортPDF()
    Dim путь As String
    путь = ЭкспортКвитанцииВPDF()
    MsgBox "Квитанция сохранена:" & vbCrLf & путь, vbInformation, "Экспорт в PDF"
End Sub

' Цветные PDF по всем лицевым счетам листа ДАННЫЕ.
Public Sub ПакетныйЭкспортPDF(Optional ByVal Папка As String = "")
    Dim wsДанные As Worksheet, wsБланк As Worksheet
    Dim исходныйЛС As Variant, исходнаяСхема As String
    Dim стр As Long, последняя As Long, создано As Long

    Set wsДанные = ЛистПоИмени(ЛИСТ_ДАННЫХ)
    Set wsБланк = ЛистПоИмени(ЛИСТ_КВИТАНЦИИ)

    If Len(Папка) = 0 Then Папка = ВыбратьПапку()
    If Len(Папка) = 0 Then Exit Sub

    исходныйЛС = wsБланк.Range("КВ_ЛС").Value
    исходнаяСхема = ТекущаяСхема()
    последняя = wsДанные.Cells(wsДанные.Rows.Count, К_ЛС).End(xlUp).Row

    Application.ScreenUpdating = False
    ПрименитьСхему СХЕМА_ЦВЕТ

    For стр = 2 To последняя
        If Len(Trim$(CStr(wsДанные.Cells(стр, К_ЛС).Value))) > 0 Then
            wsБланк.Range("КВ_ЛС").Value = wsДанные.Cells(стр, К_ЛС).Value
            Application.Calculate
            wsБланк.ExportAsFixedFormat _
                Type:=xlTypePDF, _
                Filename:=СклеитьПуть(Папка, ИмяФайлаКвитанции(wsБланк)), _
                Quality:=xlQualityStandard, _
                IncludeDocProperties:=False, _
                IgnorePrintAreas:=False, _
                OpenAfterPublish:=False
            создано = создано + 1
        End If
    Next стр

    wsБланк.Range("КВ_ЛС").Value = исходныйЛС
    ПрименитьСхему исходнаяСхема
    Application.Calculate
    Application.ScreenUpdating = True

    MsgBox "Сформировано квитанций: " & создано & vbCrLf & "Папка: " & Папка, _
           vbInformation, "Экспорт в PDF"
End Sub


'==========================================================================
' 4. QR-код
'==========================================================================

' Строка платежа по ГОСТ Р 56042-2014 (формат ST00012).
' Собирается формулой на листе НАСТРОЙКИ и обновляется вместе с бланком.
Public Function СтрокаQR() As String
    Application.Calculate
    СтрокаQR = CStr(ЛистПоИмени(ЛИСТ_НАСТРОЕК).Range("КВ_QR").Value)
End Function

' Заготовка под вставку картинки QR в зарезервированную область G31:H36.
' Готового генератора QR в Excel нет, поэтому подставьте свой:
'   • офлайн — библиотека/COM-компонент, отдающий PNG по строке;
'   • онлайн — сервис, возвращающий картинку по HTTP.
' Ниже — вариант с уже сохранённым на диск файлом PNG.
Public Sub ВставитьQR(Optional ByVal ФайлPNG As String = "")
    Dim ws As Worksheet, место As Range, рис As Object

    Set ws = ЛистПоИмени(ЛИСТ_КВИТАНЦИИ)
    Set место = ws.Range("G31:H36")

    УдалитьQR ws

    If Len(ФайлPNG) = 0 Or Dir(ФайлPNG) = "" Then
        ' Файл не передан — оставляем место пустым, бланк остаётся корректным.
        Exit Sub
    End If

    Set рис = ws.Shapes.AddPicture(Filename:=ФайлPNG, _
                                   LinkToFile:=msoFalse, _
                                   SaveWithDocument:=msoTrue, _
                                   Left:=место.Left + 4, Top:=место.Top + 4, _
                                   Width:=-1, Height:=-1)
    With рис
        .Name = "QR_КВИТАНЦИЯ"
        .LockAspectRatio = msoTrue
        .Height = место.Height - 8
        .Left = место.Left + (место.Width - .Width) / 2
        .Top = место.Top + 4
    End With
End Sub

Private Sub УдалитьQR(ByVal ws As Worksheet)
    Dim i As Long
    For i = ws.Shapes.Count To 1 Step -1
        If ws.Shapes(i).Name = "QR_КВИТАНЦИЯ" Then ws.Shapes(i).Delete
    Next i
End Sub


'==========================================================================
' 5. Служебные процедуры
'==========================================================================

Private Function ЛистПоИмени(ByVal Имя As String) As Worksheet
    On Error Resume Next
    Set ЛистПоИмени = ThisWorkbook.Worksheets(Имя)
    On Error GoTo 0
    If ЛистПоИмени Is Nothing Then
        Err.Raise vbObjectError + 513, "modКвитанция", _
                  "В книге нет листа «" & Имя & "». " & _
                  "Скопируйте листы КВИТАНЦИЯ, ДАННЫЕ, НАСТРОЙКИ и СХЕМА из шаблона."
    End If
End Function

' Найти строку по лицевому счёту; если её нет — добавить в конец.
Private Function НайтиИлиДобавитьСтроку(ByVal ws As Worksheet, _
                                        ByVal ЛицевойСчет As Variant) As Long
    Dim последняя As Long, стр As Long

    последняя = ws.Cells(ws.Rows.Count, К_ЛС).End(xlUp).Row
    For стр = 2 To последняя
        If CStr(ws.Cells(стр, К_ЛС).Value) = CStr(ЛицевойСчет) Then
            НайтиИлиДобавитьСтроку = стр
            Exit Function
        End If
    Next стр

    стр = последняя + 1
    If стр < 2 Then стр = 2

    ' Формат тянем с предыдущей строки данных, но не с шапки таблицы.
    If стр > 2 Then
        ws.Range(ws.Cells(стр - 1, 1), ws.Cells(стр - 1, ПОСЛЕДНИЙ_СТОЛБЕЦ)).Copy
        ws.Range(ws.Cells(стр, 1), ws.Cells(стр, ПОСЛЕДНИЙ_СТОЛБЕЦ)).PasteSpecial _
            Paste:=xlPasteFormats
        Application.CutCopyMode = False
    End If

    ws.Cells(стр, К_ЛС).Value = ЛицевойСчет
    НайтиИлиДобавитьСтроку = стр
End Function

Private Sub ЗаписатьЕслиЗадано(ByVal ws As Worksheet, ByVal стр As Long, _
                               ByVal столбец As Long, ByVal значение As Variant)
    If IsMissing(значение) Then Exit Sub
    If IsEmpty(значение) Then Exit Sub
    If VarType(значение) = vbString Then
        If Len(значение) = 0 Then Exit Sub
    End If
    ws.Cells(стр, столбец).Value = значение
End Sub

Private Function Ноль(ByVal значение As Variant) As Double
    If IsNumeric(значение) Then Ноль = CDbl(значение) Else Ноль = 0
End Function

Private Function ТекущаяСхема() As String
    Dim значение As String
    On Error Resume Next
    значение = CStr(ЛистПоИмени(ЛИСТ_НАСТРОЕК).Range("КВ_СХЕМА").Value)
    On Error GoTo 0
    If UCase$(значение) = UCase$(СХЕМА_ЦВЕТ) Then
        ТекущаяСхема = СХЕМА_ЦВЕТ
    Else
        ТекущаяСхема = СХЕМА_ЧБ
    End If
End Function

' "0F6B70" -> цвет для Interior.Color / Font.Color
Private Function ЦветИзHex(ByVal Hex6 As Variant) As Long
    Dim s As String
    s = Replace(Trim$(CStr(Hex6)), "#", "")
    If Len(s) = 8 Then s = Right$(s, 6)      ' на случай записи вида FF0F6B70
    If Len(s) <> 6 Then s = "FFFFFF"
    ЦветИзHex = RGB(CLng("&H" & Mid$(s, 1, 2)), _
                    CLng("&H" & Mid$(s, 3, 2)), _
                    CLng("&H" & Mid$(s, 5, 2)))
End Function

' КР_2026-07_л-с-3120249_кв-49.pdf
Private Function ИмяФайлаКвитанции(ByVal ws As Worksheet) As String
    Dim период As String, лс As String, кв As String

    период = ОчиститьИмя(CStr(ws.Range("КВ_ПЕРИОД").Text))
    лс = ОчиститьИмя(CStr(ws.Range("КВ_ЛС").Text))
    кв = ОчиститьИмя(CStr(ws.Range("КВ_КВАРТИРА").Text))

    ИмяФайлаКвитанции = "КР_" & период & "_л-с-" & лс & "_кв-" & кв & ".pdf"
End Function

Private Function ОчиститьИмя(ByVal s As String) As String
    Dim запрещённые As Variant, i As Long
    запрещённые = Array("\", "/", ":", "*", "?", """", "<", ">", "|", " ")
    For i = LBound(запрещённые) To UBound(запрещённые)
        s = Replace(s, запрещённые(i), "-")
    Next i
    Do While InStr(s, "--") > 0
        s = Replace(s, "--", "-")
    Loop
    ОчиститьИмя = s
End Function

Private Function СклеитьПуть(ByVal Папка As String, ByVal Имя As String) As String
    If Right$(Папка, 1) = Application.PathSeparator Then
        СклеитьПуть = Папка & Имя
    Else
        СклеитьПуть = Папка & Application.PathSeparator & Имя
    End If
End Function

Private Function ВыбратьПапку() As String
    Dim диалог As FileDialog
    Set диалог = Application.FileDialog(msoFileDialogFolderPicker)
    диалог.Title = "Куда сложить квитанции в PDF"
    If диалог.Show = -1 Then ВыбратьПапку = диалог.SelectedItems(1)
End Function
