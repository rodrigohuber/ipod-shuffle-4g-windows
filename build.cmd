@echo off
rem Builds dist\ipod-shuffle-4g-windows.exe from src\.
rem First run creates a virtual environment in .venv and installs requirements-build.txt.
rem Needs Python 3.12 for Windows (the "py" launcher comes with it).
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    py -3.12 -m venv .venv || exit /b 1
    ".venv\Scripts\python.exe" -m pip install --upgrade pip || exit /b 1
    ".venv\Scripts\python.exe" -m pip install -r requirements-build.txt || exit /b 1
)

".venv\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed --name "ipod-shuffle-4g-windows" ^
  --workpath build --distpath dist --specpath build ^
  --add-data "%~dp0src\ipod_shuffle_4g.py;." --add-data "%~dp0LICENSE;." ^
  --hidden-import urllib.request --hidden-import urllib.parse --hidden-import urllib.error ^
  --hidden-import hashlib --hidden-import struct --hidden-import tempfile --hidden-import signal ^
  --hidden-import errno --hidden-import collections --hidden-import argparse ^
  --collect-submodules mutagen --collect-all tkinterdnd2 src\shuffle_manager.py
if errorlevel 1 exit /b 1

echo.
echo Built: %~dp0dist\ipod-shuffle-4g-windows.exe
