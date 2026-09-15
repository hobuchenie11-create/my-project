@echo off
rem autophotos - a folder of photos in, a video out.
rem
rem   .\autophotos.cmd input\photos
rem   .\autophotos.cmd "C:\Users\home\Pictures\Leto" --order date --title "Lето 2024"
rem   .\autophotos.cmd input\photos --style collage --music track.mp3
setlocal
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo Engine not provisioned yet. Run:  python setup.py
  exit /b 1
)

"%PY%" "%ROOT%montage\photos.py" %*
exit /b %ERRORLEVEL%
