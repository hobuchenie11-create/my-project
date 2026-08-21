<#
.SYNOPSIS
    Автозапуск Домоведа отдельным процессом — задание в Планировщике Windows.

.DESCRIPTION
    Бот жил в терминале VS Code и умирал вместе с редактором. Задание
    «DH OS (Домовед)» запускает его при входе в систему через pythonw.exe —
    без окна, отдельным процессом, независимо от терминала.

    Задание повторяется каждые 5 минут с политикой IgnoreNew: пока бот жив,
    новый запуск игнорируется, а если процесс упал (или не поднялся, потому
    что прокси ещё не стартовал), следующая попытка вернёт его в строй.
    Прав администратора не требует — задание пользовательское.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\autostart.ps1 -Install
    powershell -ExecutionPolicy Bypass -File scripts\autostart.ps1 -Status
    powershell -ExecutionPolicy Bypass -File scripts\autostart.ps1 -Remove
#>
[CmdletBinding(DefaultParameterSetName = 'Status')]
param(
    [Parameter(ParameterSetName = 'Install')][switch]$Install,
    [Parameter(ParameterSetName = 'Remove')][switch]$Remove,
    [Parameter(ParameterSetName = 'Status')][switch]$Status
)

$ErrorActionPreference = 'Stop'

$TaskName = 'DH OS (Домовед)'
$ProjectDir = Split-Path -Parent $PSScriptRoot
$Entry = Join-Path $ProjectDir 'run.py'

function Get-PythonwPath {
    # pythonw.exe — тот же интерпретатор, что и python.exe, но без окна консоли
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $python) { throw 'python.exe не найден в PATH.' }
    # Псевдоним из WindowsApps сам по себе не годится — ищем настоящий каталог
    if ($python -like '*\WindowsApps\*') {
        $real = Get-ChildItem "$env:LOCALAPPDATA\Python\pythoncore-*\pythonw.exe" -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending | Select-Object -First 1
        if ($real) { return $real.FullName }
    }
    $pythonw = Join-Path (Split-Path -Parent $python) 'pythonw.exe'
    if (-not (Test-Path $pythonw)) { throw "pythonw.exe не найден рядом с $python" }
    return $pythonw
}

function Install-Autostart {
    $pythonw = Get-PythonwPath
    if (-not (Test-Path $Entry)) { throw "Не найден $Entry" }

    $action = New-ScheduledTaskAction -Execute $pythonw -Argument 'run.py' `
        -WorkingDirectory $ProjectDir

    # Вход в систему + пауза: прокси (Nekobox/Hiddify) должен успеть подняться,
    # иначе первая попытка упадёт на обращении к api.telegram.org
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
    $trigger.Delay = 'PT2M'
    # Повтор каждые 5 минут навсегда — сторож на случай падения
    $trigger.Repetition = (New-ScheduledTaskTrigger -Once -At (Get-Date) `
        -RepetitionInterval (New-TimeSpan -Minutes 5)).Repetition

    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
        -StartWhenAvailable -DontStopOnIdleEnd `
        -ExecutionTimeLimit ([TimeSpan]::Zero)

    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
        -LogonType Interactive -RunLevel Limited

    Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
        -Settings $settings -Principal $principal -Force `
        -Description 'Домовед: приём показаний счётчиков, ведомость и реестр ОЭК.' | Out-Null

    Write-Host "Задание «$TaskName» создано."
    Write-Host "  запуск:  $pythonw run.py"
    Write-Host "  папка:   $ProjectDir"
    Write-Host "  журнал:  $(Join-Path $ProjectDir 'logs\dhos.log')"
}

function Remove-Autostart {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Задание «$TaskName» удалено. Автозапуск выключен."
    } else {
        Write-Host "Задание «$TaskName» не найдено — автозапуск и так выключен."
    }
}

function Show-Status {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Host "Автозапуск не настроен (задания «$TaskName» нет)."
    } else {
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "Задание:          $TaskName"
        Write-Host "Состояние:        $($task.State)"
        Write-Host "Последний запуск: $($info.LastRunTime) (код $($info.LastTaskResult))"
        Write-Host "Следующий:        $($info.NextRunTime)"
    }
    $running = Get-CimInstance Win32_Process -Filter "Name like 'python%'" |
        Where-Object { $_.CommandLine -like '*run.py*' }
    if ($running) {
        foreach ($p in $running) {
            Write-Host "Процесс бота:     PID $($p.ProcessId)"
        }
    } else {
        Write-Host 'Процесс бота:     не запущен'
    }
}

switch ($PSCmdlet.ParameterSetName) {
    'Install' { Install-Autostart }
    'Remove'  { Remove-Autostart }
    default   { Show-Status }
}
