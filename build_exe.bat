@echo off
echo Instalando pyinstaller...
python -m pip install pyinstaller requests
echo.
echo Gerando executavel...
python -m PyInstaller --onefile --windowed --name ProfileManager gui.py
echo.
echo Pronto! O arquivo esta em dist\ProfileManager.exe
pause
