@echo off
echo Atualizando...
git pull origin main
echo.
python setup.py
pause
