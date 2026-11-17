@echo off
echo Instalando pyinstaller...
pip install pyinstaller requests
echo.
echo Gerando executavel...
pyinstaller --onefile --windowed --name ProfileManager gui.py
echo.
echo Pronto! O arquivo esta em dist\ProfileManager.exe
pause
