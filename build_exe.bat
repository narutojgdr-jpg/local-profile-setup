@echo off
echo Instalando pyinstaller...
python -m pip install pyinstaller requests
echo.
echo Gerando executavel (sem console)...
python -m PyInstaller --onefile --noconsole --name ProfileManager gui.py
echo.
echo Pronto! O arquivo esta em dist\ProfileManager.exe
pause
