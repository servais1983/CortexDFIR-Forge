![CortexDFIR-Forge Logo](https://github.com/user-attachments/assets/934cca7c-2f04-442c-8cca-f8455004efb5)

# CortexDFIR-Forge

![GitHub last commit](https://img.shields.io/github/last-commit/servais1983/CortexDFIR-Forge)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)

## 🔍 Présentation

CortexDFIR-Forge est une solution professionnelle complète qui industrialise l'utilisation de Cortex XDR pour les investigations DFIR (Digital Forensics & Incident Response). Ce projet transforme l'approche "cas par cas" en une méthodologie standardisée et automatisée, permettant aux analystes de sécurité de traiter efficacement de grands volumes de données forensiques.

### 🌟 Caractéristiques principales

- **🔄 Standardisation** : Workflows prédéfinis et reproductibles pour les investigations
- **⚙️ Automatisation** : Réduction des tâches manuelles et accélération des analyses
- **📊 Multi-format** : Support de différents types de fichiers (VMDK, logs, CSV, etc.)
- **🔌 Intégration avancée** : Connexion native avec Cortex XDR via API
- **🧩 Extensibilité** : Architecture modulaire et évolutive
- **📝 Reporting** : Génération automatique de rapports détaillés au format HTML

## 📋 Architecture

CortexDFIR-Forge utilise une architecture modulaire pour maximiser la flexibilité et l'extensibilité :

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Utilisateur                    │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                      Moteur d'Analyse                        │
├─────────────┬─────────────┬──────────────┬──────────────────┤
│  Analyseur  │  Scanner    │ Intégration  │  Générateur de   │
│  de Fichiers│    YARA     │  Cortex XDR  │     Rapport      │
└─────────────┴─────────────┴──────────────┴──────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                    Sources de Données                        │
├─────────────┬─────────────┬──────────────┬──────────────────┤
│   Fichiers  │   Fichiers  │   Fichiers   │     Données      │
│    VMDK     │    Logs     │     CSV      │   Cortex XDR     │
└─────────────┴─────────────┴──────────────┴──────────────────┘
```

## 📂 Structure du projet

```
CortexDFIR-Forge/
├── src/                # Code source principal
│   ├── core/           # Composants principaux
│   │   ├── analyzer.py         # Analyseur de fichiers
│   │   ├── cortex_client.py    # Client API Cortex XDR
│   │   └── report_generator.py # Générateur de rapports
│   ├── ui/             # Interface utilisateur
│   │   └── main_window.py      # Fenêtre principale
│   ├── utils/          # Utilitaires
│   │   ├── config_manager.py   # Gestionnaire de configuration
│   │   ├── file_analyzer.py    # Analyseur de fichiers spécifiques
│   │   └── yara_scanner.py     # Scanner YARA
│   └── main.py         # Point d'entrée de l'application
├── rules/              # Règles YARA et autres règles de détection
│   ├── malware/        # Règles pour la détection de malwares
│   ├── ransomware/     # Règles pour la détection de ransomwares
│   ├── backdoors/      # Règles pour la détection de backdoors
│   ├── phishing/       # Règles pour la détection de phishing
│   ├── antidebug/      # Règles pour la détection d'anti-débogage
│   ├── exploits/       # Règles pour la détection d'exploits
│   ├── webshells/      # Règles pour la détection de webshells
│   ├── maldocs/        # Règles pour la détection de documents malveillants
│   └── crypto/         # Règles pour la détection d'algorithmes cryptographiques
├── templates/          # Templates pour les rapports HTML
│   ├── report/         # Templates de rapport
│   └── dashboard/      # Templates de tableau de bord
├── static/             # Ressources statiques
│   ├── css/            # Feuilles de style
│   ├── js/             # Scripts JavaScript
│   └── images/         # Images et icônes
├── docs/               # Documentation complète
│   ├── technical/      # Documentation technique détaillée
│   ├── user_guide.md   # Guide d'utilisation
│   └── improvements.md # Roadmap et améliorations futures
├── installer.bat       # Script d'installation pour Windows
├── run.bat             # Script de lancement pour Windows
├── requirements.txt    # Dépendances Python
├── LICENSE             # Licence du projet
└── README.md           # Documentation principale
```

## 🔧 Intégration avec Cortex XDR

CortexDFIR-Forge s'intègre nativement avec Cortex XDR via son API, offrant des fonctionnalités avancées :

### Fonctionnalités d'intégration

- **Authentification sécurisée** : Gestion des API keys et tokens avec cache intelligent
- **Analyse de fichiers** : Envoi de fichiers à Cortex XDR pour analyse approfondie
- **Requêtes XQL** : Support du XDR Query Language pour des recherches avancées
- **Corrélation** : Corrélation entre les résultats YARA locaux et les données Cortex XDR
- **Gestion des incidents** : Récupération et analyse des incidents Cortex XDR
- **Alertes et endpoints** : Accès aux alertes et aux informations sur les endpoints

### Configuration de l'intégration

Pour configurer l'intégration avec Cortex XDR :

1. Obtenez vos identifiants API Cortex XDR (API Key et API Key ID)
2. Configurez ces identifiants dans le fichier de configuration
3. Spécifiez l'URL de base de votre instance Cortex XDR

Exemple de configuration :

```json
{
  "cortex_xdr": {
    "base_url": "https://api.xdr.paloaltonetworks.com",
    "api_key": "votre_api_key",
    "api_key_id": "votre_api_key_id",
    "tenant_id": "votre_tenant_id",
    "advanced_api": true
  }
}
```

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- Cortex XDR API credentials (pour l'intégration complète)
- Bibliothèques Python (voir requirements.txt)

### Installation sur Windows

1. Clonez ce dépôt sur votre machine Windows
   ```
   git clone https://github.com/servais1983/CortexDFIR-Forge.git
   cd CortexDFIR-Forge
   ```

2. Exécutez `installer.bat` pour installer les dépendances nécessaires
   ```
   installer.bat
   ```

3. Configurez vos identifiants Cortex XDR dans le fichier de configuration
4. Lancez l'application via le script principal
   ```
   run.bat
   ```

### Installation sur Linux

```bash
git clone https://github.com/servais1983/CortexDFIR-Forge.git
cd CortexDFIR-Forge
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python src/main.py
```

## 📊 Fonctionnalités détaillées

### Analyse multi-format

CortexDFIR-Forge prend en charge l'analyse de différents types de fichiers :

- **Fichiers VMDK** : Analyse des disques virtuels jusqu'à 60GB
- **Fichiers logs** : Détection d'indicateurs de compromission dans les journaux
- **Fichiers CSV** : Identification de données suspectes dans les exports
- **Exécutables** : Détection de malwares et comportements suspects
- **Scripts** : Analyse de code potentiellement malveillant

### Détection avancée

L'outil intègre plusieurs mécanismes de détection :

- **Intégration Cortex XDR** : Utilisation des capacités avancées de Cortex
- **Règles YARA personnalisables** : Plus de 1000 règles issues des meilleures sources
- **Détection de ransomwares** : Focus particulier sur LockBit 3.0 et autres familles
- **Analyse de phishing** : Identification des tentatives de phishing
- **Détection de persistance** : Identification des mécanismes de persistance

### Système de scoring et reporting

- **Scoring des menaces** : Évaluation de la criticité des menaces détectées
- **Priorisation** : Classement des menaces par niveau de risque
- **Rapports HTML détaillés** : Documentation complète des résultats avec visualisations

## 📈 Cas d'usage

### Cas d'usage 1 : Analyse d'un disque virtuel compromis

1. Chargez un fichier VMDK dans l'application
2. Sélectionnez les types d'analyses à effectuer (malware, ransomware, backdoors)
3. Lancez l'analyse automatisée
4. Consultez les résultats avec le scoring des menaces
5. Générez un rapport détaillé pour documentation

### Cas d'usage 2 : Investigation d'un incident avec Cortex XDR

1. Configurez l'intégration Cortex XDR
2. Récupérez les alertes et incidents depuis Cortex XDR
3. Analysez les fichiers suspects identifiés
4. Corrélation automatique entre les résultats YARA et les données Cortex XDR
5. Exportez un rapport consolidé pour l'équipe de réponse aux incidents

### Cas d'usage 3 : Analyse de logs de sécurité

1. Importez des fichiers de logs dans l'application
2. Sélectionnez les règles de détection appropriées
3. Lancez l'analyse automatisée
4. Identifiez les patterns suspects et les indicateurs de compromission
5. Générez un rapport avec timeline des événements

## 🔍 Règles YARA

CortexDFIR-Forge intègre plus de 1000 règles YARA issues des meilleures sources :

- **YARA-Rules Project** : Collection complète et maintenue de règles YARA
- **Signature-Base** : Dépôt de référence de Florian Roth (Neo23x0)
- **Règles personnalisées** : Développées spécifiquement pour ce projet

Les règles sont organisées par catégories pour faciliter la maintenance et l'utilisation.

## 📝 Génération de rapports

L'outil génère des rapports HTML professionnels incluant :

- **Résumé exécutif** : Vue d'ensemble des résultats
- **Détails des menaces** : Description détaillée des menaces détectées
- **Visualisations** : Graphiques et diagrammes pour une meilleure compréhension
- **Indicateurs de compromission** : Liste des IoCs identifiés
- **Recommandations** : Actions suggérées pour remédiation

## 🛠️ Développement et contribution

### Guide de contribution

Les contributions à ce projet sont les bienvenues. Pour contribuer :

1. Forkez le dépôt
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Committez vos changements (`git commit -m 'Ajout d'une nouvelle fonctionnalité'`)
4. Poussez vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Ouvrez une Pull Request

### Ajout de règles YARA

Pour ajouter de nouvelles règles YARA :

1. Créez un fichier .yar ou .yara dans le sous-répertoire approprié
2. Suivez les conventions de nommage existantes
3. Incluez des métadonnées complètes (description, auteur, date, etc.)
4. Testez la règle sur des échantillons connus avant de la soumettre

## 📚 Documentation

Une documentation complète est disponible dans le dossier `docs/` :

- **[Documentation technique](docs/technical/README.md)** : Architecture détaillée, modules, API
- **[Guide d'utilisation](docs/user_guide.md)** : Instructions d'installation et d'utilisation
- **[Roadmap et améliorations](docs/improvements.md)** : Évolutions futures prévues

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
