@echo off
echo Atualizando...
echo.
if not exist ".git" (
    echo Nao e um repositorio git.
    echo Clone novamente: git clone https://github.com/narutojgdr-jpg/local-profile-setup.git
    echo.
    pause
    exit /b 1
)
git pull
echo.
echo Atualizado.
pause
