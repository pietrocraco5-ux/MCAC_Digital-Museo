@echo off
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (
  py -3 seed.py
  py -3 server.py
) else (
  python seed.py
  python server.py
)
pause
