# Guide de Migration des Régions Cortex XDR

## 🌍 Présentation

Ce guide vous accompagne dans la migration de CortexDFIR-Forge d'une région Cortex XDR à une autre. Le projet est maintenant configuré par défaut pour la région **Europe (EU)**, mais peut facilement être adapté pour d'autres régions.

## 📍 Régions Disponibles

| Région | URL de Base | Code |
|--------|-------------|------|
| Europe | `https://api-eu.xdr.paloaltonetworks.com` | EU |
| États-Unis | `https://api-us.xdr.paloaltonetworks.com` | US |
| Asie-Pacifique | `https://api-apac.xdr.paloaltonetworks.com` | APAC |

## 🔄 Étapes de Migration

### 1. Identifier votre région actuelle

```bash
# Vérifier la configuration actuelle
python src/utils/test_cortex_connection.py
```

La région actuelle sera affichée dans la section "Test du client Cortex XDR".

### 2. Sauvegarder la configuration actuelle

```bash
# Créer une sauvegarde
cp .env .env.backup
cp config/config.yaml config/config.yaml.backup
```

### 3. Mettre à jour la configuration

#### Option A : Via le fichier .env (Recommandé)

Éditez votre fichier `.env` :

```bash
# Pour EU (par défaut)
CORTEX_BASE_URL=https://api-eu.xdr.paloaltonetworks.com

# Pour US
CORTEX_BASE_URL=https://api-us.xdr.paloaltonetworks.com

# Pour APAC
CORTEX_BASE_URL=https://api-apac.xdr.paloaltonetworks.com
```

#### Option B : Via config.yaml

Éditez `config/config.yaml` :

```yaml
cortex:
  base_url: https://api-eu.xdr.paloaltonetworks.com  # Remplacez par votre région
  use_env_secrets: true
```

### 4. Vérifier les clés API

⚠️ **Important** : Les clés API sont spécifiques à chaque région. Si vous changez de région, vous devrez :

1. Vous connecter à la console Cortex XDR de la nouvelle région
2. Générer de nouvelles clés API
3. Mettre à jour votre fichier `.env` :

```bash
CORTEX_API_KEY=nouvelle_cle_api
CORTEX_API_KEY_ID=nouveau_id_cle_api
CORTEX_TENANT_ID=nouveau_tenant_id
```

### 5. Tester la nouvelle configuration

```bash
# Test de connexion
python src/utils/test_cortex_connection.py

# Test unitaire
python -m pytest tests/test_cortex_client.py -v
```

### 6. Redémarrer les services

#### Pour Docker

```bash
docker-compose down
docker-compose up -d
```

#### Pour l'installation locale

```bash
# Arrêter l'application
# Ctrl+C ou fermer le terminal

# Redémarrer
python src/main.py
```

## 🔧 Script de Migration Automatique

Vous pouvez utiliser ce script pour automatiser la migration :

```bash
#!/bin/bash
# migrate_region.sh

REGION=$1

if [ -z "$REGION" ]; then
    echo "Usage: ./migrate_region.sh [EU|US|APAC]"
    exit 1
fi

case $REGION in
    EU)
        URL="https://api-eu.xdr.paloaltonetworks.com"
        ;;
    US)
        URL="https://api-us.xdr.paloaltonetworks.com"
        ;;
    APAC)
        URL="https://api-apac.xdr.paloaltonetworks.com"
        ;;
    *)
        echo "Région invalide. Utilisez EU, US ou APAC"
        exit 1
        ;;
esac

# Backup
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update .env
if [ -f .env ]; then
    sed -i "s|CORTEX_BASE_URL=.*|CORTEX_BASE_URL=$URL|" .env
else
    echo "CORTEX_BASE_URL=$URL" >> .env
fi

echo "✅ Migration vers la région $REGION terminée"
echo "📍 Nouvelle URL : $URL"
echo ""
echo "⚠️  N'oubliez pas de :"
echo "1. Générer de nouvelles clés API pour cette région"
echo "2. Mettre à jour CORTEX_API_KEY, CORTEX_API_KEY_ID et CORTEX_TENANT_ID"
echo "3. Tester la connexion avec : python src/utils/test_cortex_connection.py"
```

## 📊 Comparaison des Régions

### Performances

| Région | Latence depuis l'Europe | Latence depuis US | Latence depuis Asie |
|--------|------------------------|-------------------|---------------------|
| EU | < 50ms | 100-150ms | 200-300ms |
| US | 100-150ms | < 50ms | 150-250ms |
| APAC | 200-300ms | 150-250ms | < 50ms |

### Conformité

| Région | GDPR | SOC 2 | ISO 27001 |
|--------|------|-------|-----------|
| EU | ✅ Prioritaire | ✅ | ✅ |
| US | ✅ | ✅ Prioritaire | ✅ |
| APAC | ✅ | ✅ | ✅ Prioritaire |

## ❓ FAQ

### Q : Puis-je utiliser les mêmes clés API pour plusieurs régions ?
**R :** Non, les clés API sont spécifiques à chaque région. Vous devez générer de nouvelles clés pour chaque région.

### Q : Mes données sont-elles synchronisées entre les régions ?
**R :** Non, chaque région Cortex XDR est indépendante. Les incidents, alertes et configurations ne sont pas partagés entre régions.

### Q : Comment choisir la bonne région ?
**R :** Choisissez la région la plus proche de vos utilisateurs principaux ou celle qui correspond à vos exigences de conformité.

### Q : Puis-je connecter plusieurs régions simultanément ?
**R :** Non, une instance de CortexDFIR-Forge ne peut se connecter qu'à une seule région à la fois. Pour plusieurs régions, déployez plusieurs instances.

## 🚨 Problèmes Courants

### Erreur d'authentification après migration

```
❌ Échec de l'authentification. Vérifiez vos clés API.
```

**Solution :** Vous utilisez probablement des clés API de l'ancienne région. Générez de nouvelles clés dans la console Cortex XDR de la nouvelle région.

### Timeout de connexion

```
❌ Erreur lors du test de connexion : timeout
```

**Solution :** 
1. Vérifiez votre connexion internet
2. Vérifiez que l'URL de la région est correcte
3. Vérifiez les règles de pare-feu pour autoriser les connexions HTTPS sortantes

### Incidents/Alertes manquants

**Solution :** Les données ne sont pas synchronisées entre régions. Vous devrez exporter/importer manuellement si nécessaire.

## 📞 Support

Pour toute question sur la migration :
- 📧 Email : support@cortexdfir-forge.com
- 💬 GitHub Issues : [Signaler un problème](https://github.com/servais1983/CortexDFIR-Forge/issues)
- 📚 Documentation : [Guide complet](https://cortexdfir-forge.readthedocs.io)

---

*Dernière mise à jour : Juin 2025*
