# 📦 Guide d'Installation Détaillé - CortexDFIR-Forge

Ce guide fournit des instructions complètes pour installer et configurer CortexDFIR-Forge dans différents environnements.

## 📋 Table des Matières

- [Prérequis Système](#prérequis-système)
- [Installation Rapide](#installation-rapide)
- [Installation Détaillée](#installation-détaillée)
- [Configuration](#configuration)
- [Vérification](#vérification)
- [Dépannage](#dépannage)
- [Désinstallation](#désinstallation)

## 🔧 Prérequis Système

### Système d'Exploitation
- **Windows 10/11** (64-bit) - Recommandé
- **Ubuntu 20.04 LTS** ou plus récent
- **CentOS 8** ou plus récent
- **macOS 10.15** ou plus récent (support limité)

### Logiciels Requis

#### Python
```bash
# Version requise : Python 3.8 - 3.11
python --version  # Doit afficher Python 3.8.x à 3.11.x
```

#### Git
```bash
git --version  # Requis pour cloner le repository
```

#### Ressources Système
- **RAM** : Minimum 8 GB, Recommandé 16 GB
- **Stockage** : Minimum 5 GB d'espace libre
- **Processeur** : x64, minimum 2 cœurs
- **Réseau** : Accès Internet pour l'API Cortex XDR

## ⚡ Installation Rapide

### Option 1 : Script Automatique (Windows)

```batch
# Télécharger et exécuter le script d'installation
curl -O https://raw.githubusercontent.com/servais1983/CortexDFIR-Forge/master/install-windows.bat
install-windows.bat
```

### Option 2 : Script Automatique (Linux/macOS)

```bash
# Télécharger et exécuter le script d'installation
curl -fsSL https://raw.githubusercontent.com/servais1983/CortexDFIR-Forge/master/install-unix.sh | bash
```

## 🔨 Installation Détaillée

### Étape 1 : Préparation de l'Environnement

#### Windows

```powershell
# 1. Installer Python depuis Microsoft Store ou python.org
# 2. Installer Git depuis git-scm.com
# 3. Ouvrir PowerShell en tant qu'administrateur

# Vérifier l'installation
python --version
git --version
pip --version
```

#### Ubuntu/Debian

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
sudo apt install -y python3 python3-pip python3-venv git build-essential
sudo apt install -y libmagic1 libmagic-dev
sudo apt install -y libssl-dev libffi-dev python3-dev

# Installation des dépendances pour l'interface graphique (si nécessaire)
sudo apt install -y python3-pyqt5 python3-pyqt5.qtwebkit
```

#### CentOS/RHEL

```bash
# Installation des dépendances
sudo dnf update -y
sudo dnf install -y python3 python3-pip git gcc gcc-c++ make
sudo dnf install -y file-devel openssl-devel libffi-devel python3-devel

# Installation d'EPEL pour des packages supplémentaires
sudo dnf install -y epel-release
```

### Étape 2 : Clonage du Repository

```bash
# Cloner le repository
git clone https://github.com/servais1983/CortexDFIR-Forge.git
cd CortexDFIR-Forge

# Vérifier le contenu
ls -la
```

### Étape 3 : Création de l'Environnement Virtuel

```bash
# Créer un environnement virtuel Python
python -m venv venv

# Activer l'environnement virtuel
# Windows :
venv\Scripts\activate
# Linux/macOS :
source venv/bin/activate

# Vérifier l'activation
which python  # Doit pointer vers venv/bin/python
```

### Étape 4 : Installation des Dépendances

```bash
# Mise à jour de pip
python -m pip install --upgrade pip setuptools wheel

# Installation des dépendances principales
pip install -r requirements-updated.txt

# Vérification de l'installation
pip list | grep -E "(PyQt5|requests|yara-python)"
```

### Étape 5 : Installation des Règles YARA

```bash
# Les règles YARA sont déjà incluses dans le repository
# Vérifier leur présence
ls -la rules/

# Compiler les règles (optionnel, pour vérification)
python -c "import yara; yara.compile(filepath='rules/apt_apt28.yar')"
```

## ⚙️ Configuration

### Configuration Cortex XDR

1. **Créer le fichier de configuration** :

```bash
cp config/config.example.json config/config.json
```

2. **Éditer la configuration** :

```json
{
  "cortex_xdr": {
    "base_url": "https://api-{fqdn}.xdr.paloaltonetworks.com",
    "api_key": "VOTRE_API_KEY",
    "api_key_id": "VOTRE_API_KEY_ID",
    "tenant_id": "VOTRE_TENANT_ID",
    "advanced_api": true
  },
  "analysis": {
    "max_file_size": "60GB",
    "timeout": 300,
    "parallel_analysis": true
  },
  "reporting": {
    "output_format": "html",
    "include_screenshots": true,
    "detailed_analysis": true
  }
}
```

3. **Sécuriser la configuration** :

```bash
# Limiter les permissions du fichier de configuration
chmod 600 config/config.json

# Optionnel : utiliser des variables d'environnement
export CORTEX_API_KEY="votre_api_key"
export CORTEX_API_KEY_ID="votre_api_key_id"
```

### Configuration des Logs

```bash
# Créer le répertoire de logs
mkdir -p logs

# Configurer la rotation des logs (Linux)
sudo tee /etc/logrotate.d/cortexdfir-forge > /dev/null <<EOF
/path/to/CortexDFIR-Forge/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

## ✅ Vérification de l'Installation

### Test Basique

```bash
# Tester l'importation des modules principaux
python -c "
from src.core.cortex_client import CortexClient
from src.core.analyzer import FileAnalyzer
from src.core.report_generator import ReportGenerator
print('✅ Tous les modules s\'importent correctement')
"
```

### Test de Connectivité Cortex XDR

```bash
# Tester la connexion (sans fichier sensible)
python src/main.py --test-connection
```

### Test Complet

```bash
# Exécuter les tests unitaires
python -m pytest tests/ -v

# Test de performance
python src/main.py --benchmark
```

## 🔧 Dépannage

### Problèmes Courants

#### 1. Erreur d'Import PyQt5

**Symptôme** :
```
ImportError: No module named 'PyQt5'
```

**Solution Windows** :
```batch
pip install PyQt5==5.15.10
# Si échec, essayer :
conda install pyqt5
```

**Solution Linux** :
```bash
sudo apt install python3-pyqt5
pip install PyQt5==5.15.10
```

#### 2. Erreur YARA

**Symptôme** :
```
ImportError: No module named 'yara'
```

**Solution** :
```bash
# Installation manuelle de YARA
pip uninstall yara-python
pip install --no-cache-dir yara-python==4.5.1

# Linux : installer depuis les sources si nécessaire
sudo apt install libyara-dev
pip install yara-python==4.5.1
```

#### 3. Erreur de Permissions

**Symptôme** :
```
PermissionError: [Errno 13] Permission denied
```

**Solution** :
```bash
# Vérifier les permissions
ls -la config/
chmod 755 src/
chmod 600 config/config.json

# Windows : exécuter en tant qu'administrateur si nécessaire
```

#### 4. Erreur Cortex XDR API

**Symptôme** :
```
ConnectionError: Failed to connect to Cortex XDR
```

**Solution** :
1. Vérifier la connectivité réseau
2. Valider les credentials API
3. Vérifier l'URL de base
4. Tester en mode simulation :

```bash
python src/main.py --simulate-cortex
```

### Logs de Débogage

```bash
# Activer le mode debug
export DEBUG=1
python src/main.py --log-level DEBUG

# Consulter les logs
tail -f logs/cortexdfir-forge.log
```

### Collecte d'Informations pour le Support

```bash
# Générer un rapport de diagnostic
python src/utils/diagnostic.py > diagnostic-report.txt
```

## 📊 Tests de Performance

### Test de Charge

```bash
# Test avec fichiers multiples
python tests/performance/load_test.py

# Benchmark YARA
python tests/performance/yara_benchmark.py
```

### Monitoring

```bash
# Surveiller l'utilisation des ressources
python src/utils/monitor.py --duration 300
```

## 🗑️ Désinstallation

### Désinstallation Complète

```bash
# 1. Arrêter tous les processus
pkill -f "cortexdfir-forge"

# 2. Supprimer l'environnement virtuel
deactivate
rm -rf venv/

# 3. Supprimer les fichiers de configuration (optionnel)
rm -rf config/config.json logs/

# 4. Supprimer le répertoire du projet
cd ..
rm -rf CortexDFIR-Forge/
```

### Nettoyage Partiel

```bash
# Nettoyer seulement les fichiers temporaires
python src/utils/cleanup.py --temp-only

# Réinitialiser la configuration
cp config/config.example.json config/config.json
```

## 📞 Support et Aide

### Documentation Supplémentaire
- [Guide Utilisateur](docs/user_guide.md)
- [Documentation API](docs/api_reference.md)
- [Guide de Développement](docs/development.md)

### Communauté
- **Issues GitHub** : [Signaler un problème](https://github.com/servais1983/CortexDFIR-Forge/issues)
- **Discussions** : [Forum communautaire](https://github.com/servais1983/CortexDFIR-Forge/discussions)

### Contact
- **Email** : support@cortexdfir-forge.com
- **Documentation** : https://cortexdfir-forge.readthedocs.io

---

**Note** : Ce guide est maintenu activement. Pour les dernières mises à jour, consultez la [documentation en ligne](https://github.com/servais1983/CortexDFIR-Forge/blob/master/docs/).
