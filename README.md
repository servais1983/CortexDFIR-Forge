![image](https://github.com/user-attachments/assets/d981c5a5-1ea9-44f9-a794-911dbbed4bf8)


# CortexDFIR-Forge

## Présentation

CortexDFIR-Forge est une solution industrialisée pour l'utilisation de Cortex XDR dans le cadre d'investigations de Digital Forensics and Incident Response (DFIR). Ce projet vise à automatiser et standardiser les processus d'analyse forensique qui étaient auparavant réalisés au cas par cas.

## Fonctionnalités

- Automatisation des workflows d'analyse DFIR avec Cortex XDR
- Support multi-format pour l'analyse de différents types de fichiers (VMDK, logs, CSV, etc.)
- Intégration de règles YARA personnalisables
- Système de scoring pour prioriser les menaces
- Génération de rapports HTML détaillés et lisibles
- Interface utilisateur intuitive pour les analystes

## Structure du projet

```
CortexDFIR-Forge/
├── src/                # Code source principal
├── rules/              # Règles YARA et autres règles de détection
├── templates/          # Templates pour les rapports HTML
├── static/             # Ressources statiques (CSS, JS, images)
├── installer.bat       # Script d'installation pour Windows
├── requirements.txt    # Dépendances Python
├── LICENSE             # Licence du projet
└── README.md           # Documentation principale
```

## Prérequis

- Python 3.8 ou supérieur
- Cortex XDR API credentials
- Bibliothèques Python (voir requirements.txt)

## Installation

1. Clonez ce dépôt sur votre machine Windows
2. Exécutez `installer.bat` pour installer les dépendances nécessaires
3. Configurez vos identifiants Cortex XDR dans le fichier de configuration
4. Lancez l'application via le script principal

## Utilisation

L'application CortexDFIR-Forge peut être lancée via l'invite de commande Windows. Elle offre une interface graphique intuitive permettant de:

1. Sélectionner les fichiers à analyser
2. Choisir les types d'analyses à effectuer
3. Lancer l'analyse automatisée
4. Visualiser les résultats et le scoring des menaces
5. Générer et exporter des rapports détaillés

## Contribution

Les contributions à ce projet sont les bienvenues. Veuillez consulter les directives de contribution pour plus d'informations.

## Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails.
