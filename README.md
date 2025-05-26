![e6df189a-c17b-44f6-9eb5-9ad87816ba48](https://github.com/user-attachments/assets/934cca7c-2f04-442c-8cca-f8455004efb5)




# CortexDFIR-Forge

![GitHub last commit](https://img.shields.io/github/last-commit/servais1983/CortexDFIR-Forge)
![License](https://img.shields.io/badge/license-MIT-blue)
![Python Version](https://img.shields.io/badge/python-3.8%2B-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)



## 🔍 Présentation

CortexDFIR-Forge est une solution complète qui industrialise l'utilisation de Cortex XDR pour les investigations DFIR (Digital Forensics & Incident Response). Ce projet transforme l'approche "cas par cas" en une méthodologie standardisée et automatisée.

### 🌟 Caractéristiques principales

- **🔄 Standardisation** : Workflows prédéfinis et reproductibles
- **⚙️ Automatisation** : Réduction des tâches manuelles
- **📊 Multi-format** : Support de différents types de fichiers (VMDK, logs, CSV, etc.)
- **🔌 Intégration** : Connexion native avec Cortex XDR
- **🧩 Extensibilité** : Architecture modulaire et évolutive
- **📝 Reporting** : Génération automatique de rapports détaillés

## 📋 Structure du projet

```
CortexDFIR-Forge/
├── src/                # Code source principal
├── rules/              # Règles YARA et autres règles de détection
├── templates/          # Templates pour les rapports HTML
├── static/             # Ressources statiques (CSS, JS, images)
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

## 🚀 Installation

### Prérequis

- Python 3.8 ou supérieur
- Cortex XDR API credentials
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

## 📊 Fonctionnalités

### Analyse multi-format

- **Fichiers VMDK** : Analyse des disques virtuels
- **Fichiers logs** : Détection d'indicateurs de compromission
- **Fichiers CSV** : Identification de données suspectes
- **Exécutables** : Détection de malwares et comportements suspects
- **Scripts** : Analyse de code potentiellement malveillant

### Détection avancée

- **Intégration Cortex XDR** : Utilisation des capacités avancées de Cortex
- **Règles YARA personnalisables** : Détection basée sur des signatures
- **Détection de ransomwares** : Focus particulier sur LockBit 3.0
- **Analyse de phishing** : Identification des tentatives de phishing
- **Détection de persistance** : Identification des mécanismes de persistance

### Système de scoring et reporting

- **Scoring des menaces** : Évaluation de la criticité des menaces détectées
- **Priorisation** : Classement des menaces par niveau de risque
- **Rapports HTML détaillés** : Documentation complète des résultats

## 📚 Documentation

Une documentation complète est disponible dans le dossier `docs/` :

- **[Documentation technique](docs/technical/README.md)** : Architecture détaillée, modules, API
- **[Guide d'utilisation](docs/user_guide.md)** : Instructions d'installation et d'utilisation
- **[Roadmap et améliorations](docs/improvements.md)** : Évolutions futures prévues

## 🔧 Utilisation

L'application CortexDFIR-Forge peut être lancée via l'invite de commande Windows ou un terminal Linux. Elle offre une interface graphique intuitive permettant de:

1. Sélectionner les fichiers à analyser
2. Choisir les types d'analyses à effectuer
3. Lancer l'analyse automatisée
4. Visualiser les résultats et le scoring des menaces
5. Générer et exporter des rapports détaillés

## 🤝 Contribution

Les contributions à ce projet sont les bienvenues. Veuillez consulter les directives de contribution pour plus d'informations.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.
