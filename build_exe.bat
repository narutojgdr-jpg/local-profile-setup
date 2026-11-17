@echo off
echo Instalando pyinstaller...
python -m pip install pyinstaller requests
echo.
echo Gerando executavel com console (pra ver erros)...
python -m PyInstaller --onefile --name ProfileManager gui.py
echo.
echo Pronto! Rode o dist\ProfileManager.exe e veja se aparece algum erro.
pause
