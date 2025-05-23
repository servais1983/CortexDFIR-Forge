@echo off
echo Lancement de CortexDFIR-Forge...
echo.

:: Activation de l'environnement virtuel
call venv\Scripts\activate.bat

:: Lancement de l'application
python src\main.py
if %errorlevel% neq 0 (
    echo Erreur lors du lancement de l'application.
    pause
    exit /b 1
)

:: Désactivation de l'environnement virtuel
deactivate
