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

:: Installation des dépendances de sécurité supplémentaires
echo Installation des dépendances de sécurité...
pip install cryptography python-dotenv
if %errorlevel% neq 0 (
    echo Erreur lors de l'installation des dépendances de sécurité.
    pause
    exit /b 1
)

:: Création du fichier de configuration sécurisé
echo Création du fichier de configuration sécurisé...
if not exist "config" mkdir config

:: Création d'un fichier de configuration template sans secrets
echo # Configuration de Cortex XDR > config\config.yaml
echo # NE PAS STOCKER DE SECRETS DANS CE FICHIER >> config\config.yaml
echo # Les secrets doivent être définis dans le fichier .env >> config\config.yaml
echo use_env_secrets: true >> config\config.yaml
echo base_url: https://api.xdr.paloaltonetworks.com >> config\config.yaml

:: Création d'un fichier .env template pour les secrets
echo # Fichier de variables d'environnement pour les secrets > config\.env.template
echo # IMPORTANT: Renommez ce fichier en .env et remplissez les valeurs >> config\.env.template
echo # Ne partagez jamais votre fichier .env >> config\.env.template
echo CORTEX_API_KEY=votre_api_key_ici >> config\.env.template
echo CORTEX_API_KEY_ID=votre_api_key_id_ici >> config\.env.template
echo CORTEX_TENANT_ID=votre_tenant_id_ici >> config\.env.template
echo # Clé de chiffrement pour le stockage local des tokens (32 caractères aléatoires) >> config\.env.template
echo ENCRYPTION_KEY=changez_cette_cle_par_une_valeur_aleatoire >> config\.env.template

echo.
echo Installation terminée avec succès !
echo.
echo IMPORTANT: Avant de lancer l'application, vous devez:
echo 1. Renommer le fichier config\.env.template en config\.env
echo 2. Éditer config\.env pour y ajouter vos informations d'identification
echo 3. Générer une clé de chiffrement aléatoire pour ENCRYPTION_KEY
echo.
echo Pour lancer l'application, exécutez "run.bat"
echo.
pause
