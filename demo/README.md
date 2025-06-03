# Démonstration Cortex XDR

Ce dossier contient des exemples d'utilisation du client Cortex XDR pour tester les fonctionnalités principales.

## Configuration

1. Copiez le fichier `config.json` et modifiez les valeurs suivantes :
   ```json
   {
       "cortex": {
           "base_url": "https://api.xdr.paloaltonetworks.com",
           "api_key": "VOTRE_API_KEY",
           "api_key_id": "VOTRE_API_KEY_ID",
           "tenant_id": "VOTRE_TENANT_ID",
           "advanced_api": true
       }
   }
   ```

2. Assurez-vous d'avoir installé toutes les dépendances :
   ```bash
   pip install -r ../requirements.txt
   ```

## Utilisation

Pour lancer la démonstration :
```bash
python demo_client.py
```

La démonstration va :
1. Analyser un fichier de test
2. Récupérer les incidents des dernières 24h
3. Exécuter une requête XQL exemple
4. Lister les endpoints

## Fonctionnalités démontrées

- Analyse de fichiers
- Gestion des incidents
- Requêtes XQL
- Gestion des endpoints

## Structure des fichiers

```
demo/
├── config.json          # Configuration
├── demo_client.py       # Script de démonstration
├── README.md           # Ce fichier
└── samples/            # Dossier pour les fichiers de test
    └── test_file.txt   # Fichier de test
```

## Notes

- Les résultats sont affichés dans la console avec un formatage JSON
- Les erreurs sont capturées et affichées de manière appropriée
- Le script utilise le mode simulation si les identifiants ne sont pas configurés 