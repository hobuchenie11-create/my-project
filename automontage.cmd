@echo off
rem automontage - video in, edited cut out.
rem
rem   .\automontage.cmd input\video\zapis.mp4
rem   .\automontage.cmd "C:\Users\home\Videos\zapis.mp4" --target 45 --title "Otchet"
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Engine not provisioned yet. Run:  python setup.py
  exit /b 1
)

"%PY%" "%ROOT%montage\pipeline.py" %*
exit /b %ERRORLEVEL%
