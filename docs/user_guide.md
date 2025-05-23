# Guide d'installation et d'utilisation - CortexDFIR-Forge

## Installation

### Prérequis

- Windows 10/11 ou Linux
- Python 3.8 ou supérieur
- Accès à l'API Cortex XDR (optionnel mais recommandé)

### Installation sur Windows

1. Clonez le dépôt GitHub :
   ```
   git clone https://github.com/servais1983/CortexDFIR-Forge.git
   cd CortexDFIR-Forge
   ```

2. Exécutez le script d'installation :
   ```
   installer.bat
   ```

3. Configurez vos identifiants Cortex XDR dans le fichier `config/config.yaml`

4. Lancez l'application :
   ```
   run.bat
   ```

### Installation sur Linux

1. Clonez le dépôt GitHub :
   ```bash
   git clone https://github.com/servais1983/CortexDFIR-Forge.git
   cd CortexDFIR-Forge
   ```

2. Créez un environnement virtuel et installez les dépendances :
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Configurez vos identifiants Cortex XDR dans le fichier `config/config.yaml`

4. Lancez l'application :
   ```bash
   python src/main.py
   ```

## Guide d'utilisation rapide

### 1. Configuration initiale

Avant la première utilisation, configurez vos identifiants Cortex XDR dans le fichier `config/config.yaml` :

```yaml
cortex:
  api_key: "votre_api_key"
  api_key_id: "votre_api_key_id"
  tenant_id: "votre_tenant_id"
  base_url: "https://api.xdr.paloaltonetworks.com"
```

### 2. Interface principale

L'interface principale de CortexDFIR-Forge est divisée en plusieurs sections :

![Interface principale](../screenshots/main_interface.png)

1. **Sélection de fichiers** : Permet de choisir les fichiers à analyser
2. **Types d'analyse** : Options pour sélectionner les types d'analyse à effectuer
3. **Résultats** : Affichage des résultats d'analyse
4. **Barre de progression** : Indique l'avancement de l'analyse
5. **Génération de rapport** : Permet de générer un rapport HTML des résultats

### 3. Analyse de fichiers

Pour analyser des fichiers :

1. Cliquez sur "Sélectionner des fichiers" et choisissez les fichiers à analyser
2. Cochez les types d'analyse souhaités (Malware, Ransomware, Phishing, Persistance)
3. Cliquez sur "Démarrer l'analyse"
4. Attendez que l'analyse soit terminée
5. Consultez les résultats dans l'interface

### 4. Génération de rapports

Pour générer un rapport d'analyse :

1. Après une analyse réussie, cliquez sur "Générer un rapport"
2. Sélectionnez le dossier de destination pour le rapport
3. Le rapport HTML sera généré et ouvert automatiquement dans votre navigateur

### 5. Configuration avancée

Pour accéder aux paramètres avancés :

1. Allez dans l'onglet "Configuration"
2. Cliquez sur "Paramètres Cortex XDR" pour configurer l'API
3. Vous pouvez également personnaliser les paramètres de reporting et d'analyse

## Fonctionnalités principales

### Analyse multi-format

CortexDFIR-Forge prend en charge l'analyse de différents types de fichiers :

- **Fichiers VMDK** : Analyse des disques virtuels
- **Fichiers logs** : Détection d'indicateurs de compromission
- **Fichiers CSV** : Identification de données suspectes
- **Exécutables** : Détection de malwares et comportements suspects
- **Scripts** : Analyse de code potentiellement malveillant

### Détection avancée

L'application offre plusieurs mécanismes de détection :

- **Intégration Cortex XDR** : Utilisation des capacités avancées de Cortex
- **Règles YARA personnalisables** : Détection basée sur des signatures
- **Détection de ransomwares** : Focus particulier sur LockBit 3.0
- **Analyse de phishing** : Identification des tentatives de phishing
- **Détection de persistance** : Identification des mécanismes de persistance

### Système de scoring

Le système de scoring évalue la criticité des menaces détectées sur une échelle de 0 à 100 :

- **0-24** : Risque faible
- **25-49** : Risque moyen
- **50-74** : Risque élevé
- **75-100** : Risque critique

### Rapports détaillés

Les rapports HTML générés incluent :

- Résumé de l'analyse
- Statistiques globales
- Liste détaillée des menaces détectées
- Visualisations graphiques
- Recommandations

## Dépannage

### Problèmes courants

#### Erreur "ModuleNotFoundError: No module named 'PyQt5'"

**Solution** : Réinstallez PyQt5 avec pip :
```bash
pip install PyQt5
```

#### Erreur lors de la connexion à l'API Cortex XDR

**Solution** : Vérifiez vos identifiants API et votre connexion internet. L'application fonctionnera en mode dégradé sans connexion à l'API.

#### Erreur lors du chargement des règles YARA

**Solution** : Vérifiez la syntaxe de vos règles YARA. Des règles par défaut seront créées si aucune n'est trouvée.

### Support

Pour toute question ou problème, veuillez créer une issue sur le dépôt GitHub :
[https://github.com/servais1983/CortexDFIR-Forge/issues](https://github.com/servais1983/CortexDFIR-Forge/issues)
