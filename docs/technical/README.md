# Documentation Technique - CortexDFIR-Forge

## Table des matières

1. [Introduction](#introduction)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Modules principaux](#modules-principaux)
6. [API Cortex XDR](#api-cortex-xdr)
7. [Règles YARA](#règles-yara)
8. [Système de scoring](#système-de-scoring)
9. [Génération de rapports](#génération-de-rapports)
10. [Exemples d'utilisation](#exemples-dutilisation)
11. [Dépannage](#dépannage)
12. [FAQ](#faq)

## Introduction

CortexDFIR-Forge est une solution industrialisée pour l'utilisation de Cortex XDR dans le cadre d'investigations de Digital Forensics and Incident Response (DFIR). Ce projet vise à automatiser et standardiser les processus d'analyse forensique qui étaient auparavant réalisés au cas par cas.

Cette documentation technique détaille l'architecture, les composants et l'utilisation de CortexDFIR-Forge pour les analystes et développeurs.

## Architecture

CortexDFIR-Forge est construit selon une architecture modulaire qui permet une grande flexibilité et extensibilité.

### Vue d'ensemble

![Architecture](../architecture.png)

### Composants principaux

- **Interface Utilisateur (PyQt5)** : Interface graphique permettant l'interaction avec l'utilisateur
- **Noyau d'Analyse (Core)** : Composant central qui orchestre les différentes analyses
- **Client Cortex XDR** : Module d'intégration avec l'API Cortex XDR
- **Analyseur de Fichiers** : Module d'analyse multi-format
- **Scanner YARA** : Module d'analyse basé sur les règles YARA
- **Générateur de Rapports** : Module de génération de rapports HTML
- **Gestionnaire de Configuration** : Module de gestion des paramètres

### Flux de données

1. L'utilisateur sélectionne des fichiers à analyser via l'interface
2. Le noyau d'analyse distribue les fichiers aux modules appropriés
3. Les analyseurs spécialisés traitent les fichiers selon leur type
4. Le client Cortex XDR enrichit l'analyse avec des données externes
5. Le système de scoring évalue la criticité des menaces détectées
6. Le générateur de rapports produit un rapport HTML détaillé

## Installation

### Prérequis

- Python 3.8 ou supérieur
- PyQt5
- Bibliothèques Python (voir requirements.txt)
- Accès à l'API Cortex XDR (optionnel mais recommandé)

### Procédure d'installation

1. Clonez le dépôt GitHub :
   ```bash
   git clone https://github.com/servais1983/CortexDFIR-Forge.git
   cd CortexDFIR-Forge
   ```

2. Sur Windows, exécutez le script d'installation :
   ```bash
   installer.bat
   ```

3. Sur Linux/macOS, utilisez pip :
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. Configurez vos identifiants Cortex XDR dans le fichier `config/config.yaml`

## Configuration

### Fichier de configuration

Le fichier de configuration principal se trouve dans `config/config.yaml`. Voici un exemple de configuration :

```yaml
cortex:
  api_key: "votre_api_key"
  api_key_id: "votre_api_key_id"
  tenant_id: "votre_tenant_id"
  base_url: "https://api.xdr.paloaltonetworks.com"

analysis:
  default_types: ["malware", "ransomware", "phishing", "persistence"]
  max_file_size: 104857600  # 100 MB

reporting:
  company_name: "Votre Entreprise"
  logo_path: ""
  default_output_dir: "C:/Users/username/Documents/CortexDFIR-Reports"
```

### Configuration de l'API Cortex XDR

Pour obtenir les identifiants API Cortex XDR :

1. Connectez-vous à votre console Cortex XDR
2. Accédez à "Paramètres" > "API"
3. Créez une nouvelle clé API avec les permissions appropriées
4. Copiez l'API Key et l'API Key ID dans votre fichier de configuration

## Modules principaux

### Interface Utilisateur (UI)

L'interface utilisateur est construite avec PyQt5 et offre les fonctionnalités suivantes :

- Sélection de fichiers à analyser
- Choix des types d'analyse à effectuer
- Visualisation des résultats en temps réel
- Génération et visualisation de rapports

Le code principal se trouve dans `src/ui/main_window.py`.

### Noyau d'Analyse (Core)

Le noyau d'analyse est le composant central qui :

- Coordonne les différents modules d'analyse
- Gère le flux de données entre les composants
- Calcule le score global des menaces
- Prépare les données pour le reporting

Le code principal se trouve dans `src/core/analyzer.py`.

### Analyseur de Fichiers

L'analyseur de fichiers prend en charge différents types de fichiers :

- **VMDK** : Analyse des disques virtuels
- **Logs** : Analyse des fichiers journaux
- **CSV** : Analyse des données tabulaires
- **Exécutables** : Analyse des fichiers binaires
- **Scripts** : Analyse des fichiers scripts

Le code principal se trouve dans `src/utils/file_analyzer.py`.

### Client Cortex XDR

Le client Cortex XDR permet l'intégration avec l'API Cortex XDR pour :

- Soumettre des fichiers pour analyse
- Récupérer des informations sur les menaces
- Enrichir les résultats d'analyse

Le code principal se trouve dans `src/core/cortex_client.py`.

## API Cortex XDR

### Endpoints utilisés

CortexDFIR-Forge utilise principalement les endpoints suivants de l'API Cortex XDR :

- `/public_api/v1/files/upload` : Pour l'analyse de fichiers
- `/public_api/v1/incidents/get_incident_extra_data` : Pour obtenir des détails sur les incidents

### Authentification

L'authentification à l'API Cortex XDR se fait via les en-têtes HTTP suivants :

```
x-xdr-auth-id: API_KEY_ID
Authorization: API_KEY
```

### Gestion des erreurs

Le client gère les erreurs d'API de manière gracieuse :

- Simulation des résultats en cas d'indisponibilité de l'API
- Journalisation détaillée des erreurs
- Mécanismes de retry pour les erreurs temporaires

## Règles YARA

### Structure des règles

Les règles YARA sont stockées dans le dossier `rules/` et suivent la syntaxe standard YARA :

```yara
rule nom_de_la_regle {
    meta:
        description = "Description de la règle"
        author = "Auteur"
        severity = "high"
    
    strings:
        $string1 = "chaîne suspecte 1"
        $string2 = "chaîne suspecte 2"
    
    condition:
        any of them
}
```

### Règles par défaut

CortexDFIR-Forge inclut plusieurs règles par défaut :

- `ransomware.yar` : Détection de ransomwares (dont LockBit 3.0)
- `backdoor.yar` : Détection de backdoors et mécanismes de persistance
- `phishing.yar` : Détection de tentatives de phishing

### Ajout de règles personnalisées

Pour ajouter vos propres règles YARA :

1. Créez un fichier `.yar` ou `.yara` dans le dossier `rules/`
2. Suivez la syntaxe YARA standard
3. Redémarrez l'application pour charger les nouvelles règles

## Système de scoring

### Méthodologie

Le système de scoring évalue la criticité des menaces détectées selon plusieurs critères :

- Type de menace (ransomware, backdoor, etc.)
- Sévérité des règles YARA correspondantes
- Résultats de l'analyse Cortex XDR
- Caractéristiques spécifiques au type de fichier

### Calcul du score

Le score est calculé sur une échelle de 0 à 100 :

- **0-24** : Risque faible
- **25-49** : Risque moyen
- **50-74** : Risque élevé
- **75-100** : Risque critique

Chaque menace détectée contribue au score global selon sa sévérité :

- Critique : +25 points
- Élevée : +15 points
- Moyenne : +7 points
- Faible : +3 points

## Génération de rapports

### Format des rapports

Les rapports sont générés au format HTML et incluent :

- Résumé de l'analyse
- Statistiques globales
- Liste détaillée des menaces détectées
- Visualisations graphiques
- Recommandations

### Personnalisation

Les rapports peuvent être personnalisés via :

- Le fichier de configuration (`config/config.yaml`)
- Les templates HTML (`templates/report.html`)
- Les styles CSS (`static/report.css`)

### Exemple de rapport

Un exemple de rapport généré est disponible dans le dossier `examples/`.

## Exemples d'utilisation

### Analyse de fichiers VMDK

```python
from core.analyzer import CortexAnalyzer
from utils.config_manager import ConfigManager

# Initialisation
config_manager = ConfigManager()
analyzer = CortexAnalyzer(config_manager)

# Analyse d'un fichier VMDK
results = analyzer.analyze_file(
    "C:/path/to/disk.vmdk", 
    ["malware", "ransomware", "persistence"]
)

# Affichage des résultats
print(f"Score: {results['score']}")
for threat in results["threats"]:
    print(f"- {threat['name']} ({threat['severity']}): {threat['description']}")
```

### Analyse de logs

```python
from core.analyzer import CortexAnalyzer
from utils.config_manager import ConfigManager

# Initialisation
config_manager = ConfigManager()
analyzer = CortexAnalyzer(config_manager)

# Analyse d'un fichier de logs
results = analyzer.analyze_file(
    "C:/path/to/server.log", 
    ["phishing", "backdoor"]
)

# Affichage des résultats
print(f"Score: {results['score']}")
for threat in results["threats"]:
    print(f"- {threat['name']} ({threat['severity']}): {threat['description']}")
```

### Génération de rapport

```python
from core.report_generator import ReportGenerator

# Initialisation
report_generator = ReportGenerator()

# Génération du rapport
report_path = report_generator.generate_html_report(
    analysis_results,
    "C:/path/to/output"
)

print(f"Rapport généré: {report_path}")
```

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

### Journalisation

Les logs de l'application sont stockés dans le fichier `cortexdfir.log` à la racine du projet. Consultez ce fichier pour des informations détaillées en cas de problème.

## FAQ

### Questions générales

**Q: CortexDFIR-Forge fonctionne-t-il sans accès à l'API Cortex XDR ?**

R: Oui, l'application peut fonctionner en mode dégradé sans accès à l'API Cortex XDR. Les analyses locales (YARA, analyse de fichiers) restent disponibles.

**Q: Quelle est la taille maximale des fichiers analysables ?**

R: Par défaut, la limite est fixée à 100 Mo, mais elle peut être modifiée dans le fichier de configuration.

**Q: Comment ajouter de nouveaux types d'analyse ?**

R: Vous pouvez étendre la classe `FileAnalyzer` dans `src/utils/file_analyzer.py` pour ajouter de nouveaux types d'analyse.

### Questions techniques

**Q: Comment intégrer CortexDFIR-Forge à d'autres outils ?**

R: Vous pouvez utiliser les modules Python directement dans vos scripts ou développer des plugins pour d'autres outils.

**Q: Comment contribuer au projet ?**

R: Vous pouvez soumettre des pull requests sur GitHub ou créer des issues pour signaler des bugs ou suggérer des améliorations.

**Q: Comment mettre à jour les règles YARA ?**

R: Ajoutez ou modifiez les fichiers dans le dossier `rules/` et redémarrez l'application.
