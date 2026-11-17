@echo off
echo Atualizando arquivos...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/narutojgdr-jpg/local-profile-setup/main/gui.py' -OutFile 'gui.py'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/narutojgdr-jpg/local-profile-setup/main/ProfileManager.bat' -OutFile 'ProfileManager.bat'"

echo.
echo Atualizado.
pause
