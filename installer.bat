@echo off
echo Installation de CortexDFIR-Forge...
echo.

:: Vérification de Python
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python n'est pas installé ou n'est pas dans le PATH.
    echo Veuillez installer Python 3.8 ou supérieur depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Création de l'environnement virtuel
echo Création de l'environnement virtuel...
python -m venv venv
if %errorlevel% neq 0 (
    echo Erreur lors de la création de l'environnement virtuel.
    pause
    exit /b 1
)

:: Activation de l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

:: Installation des dépendances
echo Installation des dépendances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Erreur lors de l'installation des dépendances.
    pause
    exit /b 1
)

:: Création du fichier de configuration
echo Création du fichier de configuration...
if not exist "config" mkdir config
echo # Configuration de Cortex XDR > config\config.yaml
echo api_key: votre_api_key >> config\config.yaml
echo api_key_id: votre_api_key_id >> config\config.yaml
echo tenant_id: votre_tenant_id >> config\config.yaml
echo base_url: https://api.xdr.paloaltonetworks.com >> config\config.yaml

echo.
echo Installation terminée avec succès !
echo Pour lancer l'application, exécutez "run.bat"
echo.
pause
