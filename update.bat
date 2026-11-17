@echo off
echo Atualizando arquivos...
echo.

powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/narutojgdr-jpg/local-profile-setup/main/gui.py' -OutFile 'gui.py' -UseBasicParsing"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/narutojgdr-jpg/local-profile-setup/main/ProfileManager.bat' -OutFile 'ProfileManager.bat' -UseBasicParsing"
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/narutojgdr-jpg/local-profile-setup/main/update.bat' -OutFile 'update.bat' -UseBasicParsing"

echo.
echo Atualizado.
pause
