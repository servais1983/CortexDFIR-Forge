# Guide d'intégration avec Cortex XDR

## Introduction

Ce guide détaille l'intégration avancée entre CortexDFIR-Forge et Cortex XDR. Il explique comment configurer, utiliser et tirer parti des fonctionnalités d'intégration pour améliorer vos capacités d'analyse forensique.

## Prérequis

Avant de commencer, assurez-vous de disposer des éléments suivants :

- Un compte Cortex XDR avec accès administrateur
- Des identifiants API Cortex XDR (API Key et API Key ID)
- L'ID de votre tenant Cortex XDR
- Python 3.8 ou supérieur
- CortexDFIR-Forge installé et configuré

## Obtention des identifiants API Cortex XDR

Pour obtenir vos identifiants API Cortex XDR :

1. Connectez-vous à votre console Cortex XDR
2. Accédez à **Paramètres > API Keys**
3. Cliquez sur **Ajouter une clé API**
4. Sélectionnez les autorisations suivantes :
   - `Incidents - Read & Update`
   - `Endpoints - Read`
   - `Alerts - Read`
   - `XQL - Read`
   - `Files - Read & Upload`
5. Notez l'API Key et l'API Key ID générés

## Configuration de l'intégration

### Configuration via l'interface graphique

1. Lancez CortexDFIR-Forge
2. Accédez à **Paramètres > Intégration Cortex XDR**
3. Remplissez les champs suivants :
   - URL de base : `https://api.xdr.paloaltonetworks.com` (ou l'URL de votre instance)
   - API Key : Votre clé API Cortex XDR
   - API Key ID : L'identifiant de votre clé API
   - Tenant ID : L'identifiant de votre tenant
4. Cliquez sur **Tester la connexion** pour vérifier la configuration
5. Cliquez sur **Enregistrer** pour sauvegarder la configuration

### Configuration manuelle

Vous pouvez également configurer l'intégration en modifiant directement le fichier de configuration :

1. Ouvrez le fichier `config.json` dans le répertoire de l'application
2. Modifiez la section `cortex_xdr` comme suit :

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

3. Sauvegardez le fichier

## Fonctionnalités d'intégration

### Analyse de fichiers avec Cortex XDR

CortexDFIR-Forge peut envoyer des fichiers à Cortex XDR pour une analyse approfondie :

1. Dans l'interface principale, sélectionnez un fichier à analyser
2. Cochez l'option **Analyser avec Cortex XDR**
3. Cliquez sur **Lancer l'analyse**
4. Les résultats de l'analyse Cortex XDR seront intégrés au rapport final

### Requêtes XQL (XDR Query Language)

Vous pouvez exécuter des requêtes XQL directement depuis CortexDFIR-Forge :

1. Accédez à l'onglet **Requêtes XQL**
2. Saisissez votre requête XQL dans l'éditeur
3. Sélectionnez la période de temps (dernières 24h, 7 jours, 30 jours)
4. Cliquez sur **Exécuter**
5. Les résultats s'afficheront dans le tableau inférieur

Exemples de requêtes XQL utiles :

```sql
-- Recherche de processus suspects
dataset=xdr_data | filter event_type="PROCESS" AND process_name="powershell.exe" AND command_line CONTAINS "-enc" | limit 100

-- Recherche de connexions réseau vers des domaines suspects
dataset=xdr_data | filter event_type="NETWORK" AND dst_domain CONTAINS "pastebin" | limit 100

-- Recherche de fichiers récemment créés dans des dossiers sensibles
dataset=xdr_data | filter event_type="FILE" AND action_type="CREATION" AND file_path CONTAINS "\\Windows\\Temp\\" | limit 100
```

### Corrélation YARA et Cortex XDR

CortexDFIR-Forge peut corréler automatiquement les résultats des analyses YARA locales avec les données Cortex XDR :

1. Analysez un fichier avec les règles YARA locales
2. Activez l'option **Corréler avec Cortex XDR**
3. L'application recherchera automatiquement dans Cortex XDR des informations liées aux indicateurs détectés
4. Les corrélations seront affichées dans la section **Corrélations** du rapport

### Récupération des incidents et alertes

Vous pouvez récupérer et analyser les incidents et alertes Cortex XDR :

1. Accédez à l'onglet **Incidents & Alertes**
2. Sélectionnez la période de temps souhaitée
3. Cliquez sur **Récupérer les incidents** ou **Récupérer les alertes**
4. Les données s'afficheront dans le tableau
5. Cliquez sur un incident pour afficher les détails
6. Vous pouvez exporter ces données au format CSV ou les inclure dans un rapport

## Utilisation avancée

### Intégration programmatique

Vous pouvez utiliser le client Cortex XDR dans vos propres scripts Python :

```python
from src.core.cortex_client import CortexClient
from src.utils.config_manager import ConfigManager

# Initialisation du gestionnaire de configuration
config_manager = ConfigManager("config.json")

# Initialisation du client Cortex XDR
cortex_client = CortexClient(config_manager)

# Analyse d'un fichier
results = cortex_client.analyze_file("/chemin/vers/fichier.exe")

# Exécution d'une requête XQL
xql_results = cortex_client.execute_xql_query(
    "dataset=xdr_data | filter event_type='PROCESS' | limit 10",
    timeframe="last_24_hours"
)

# Récupération des alertes
alerts = cortex_client.get_alerts(time_frame="last_7_days", limit=50)

# Corrélation avec des résultats YARA
yara_results = [...] # Résultats d'une analyse YARA
correlation = cortex_client.correlate_yara_with_xdr(yara_results, "/chemin/vers/fichier.exe")
```

### Automatisation des workflows

Vous pouvez créer des workflows automatisés combinant l'analyse locale et Cortex XDR :

1. Créez un script Python utilisant le client Cortex XDR
2. Définissez les étapes de votre workflow (analyse, corrélation, rapport)
3. Planifiez l'exécution du script via une tâche cron ou Windows Task Scheduler
4. Les résultats peuvent être envoyés par email ou stockés dans un dossier partagé

## Dépannage

### Problèmes d'authentification

Si vous rencontrez des problèmes d'authentification :

1. Vérifiez que vos identifiants API sont corrects
2. Assurez-vous que votre clé API n'a pas expiré
3. Vérifiez que les autorisations de la clé API sont correctes
4. Vérifiez la connectivité réseau vers l'API Cortex XDR

### Erreurs lors de l'analyse de fichiers

Si l'analyse de fichiers échoue :

1. Vérifiez que le fichier n'est pas trop volumineux (limite de 32 Mo pour l'API)
2. Assurez-vous que le type de fichier est supporté par Cortex XDR
3. Vérifiez les logs pour plus de détails sur l'erreur

### Problèmes de performance

Si vous rencontrez des problèmes de performance :

1. Limitez le nombre de requêtes simultanées à l'API Cortex XDR
2. Utilisez le cache de token pour réduire les authentifications
3. Optimisez vos requêtes XQL pour limiter le volume de données

## Bonnes pratiques

- **Sécurité des identifiants** : Ne partagez jamais vos identifiants API et stockez-les de manière sécurisée
- **Limitation des requêtes** : Évitez de surcharger l'API avec trop de requêtes simultanées
- **Optimisation des requêtes XQL** : Utilisez des filtres appropriés pour limiter le volume de données
- **Mise à jour régulière** : Mettez à jour régulièrement CortexDFIR-Forge pour bénéficier des dernières fonctionnalités d'intégration

## Ressources additionnelles

- [Documentation API Cortex XDR](https://docs.paloaltonetworks.com/cortex/cortex-xdr/cortex-xdr-api)
- [Guide XQL](https://docs.paloaltonetworks.com/cortex/cortex-xdr/cortex-xdr-analytics/cortex-xdr-query-language)
- [Forum Cortex XDR](https://live.paloaltonetworks.com/t5/cortex-xdr/ct-p/Cortex_XDR)
