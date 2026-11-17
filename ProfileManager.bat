@echo off
if exist "dist\ProfileManager.exe" (
    start "" "dist\ProfileManager.exe"
    exit
)

where pythonw >nul 2>&1
if %errorlevel%==0 (
    start "" pythonw gui.py
    exit
)

where python >nul 2>&1
if %errorlevel%==0 (
    start "" python gui.py
    exit
)

echo Python nao encontrado. Instale o Python ou use o ProfileManager.exe da pasta dist.
pause
