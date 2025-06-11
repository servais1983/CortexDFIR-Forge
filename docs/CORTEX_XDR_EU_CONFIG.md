# Configuration Cortex XDR pour la Région EU (Europe)

## 🇪🇺 Spécificités de la Région Europe

### URL de Base
```
https://api-eu.xdr.paloaltonetworks.com
```

### Localisation des Données
- **Data Centers**: Allemagne et Pays-Bas
- **Stockage**: Toutes les données sont stockées dans l'UE
- **Traitement**: Aucun transfert de données hors UE

## 🔒 Conformité GDPR

### Exigences Respectées
- ✅ **Localisation des données**: Données hébergées exclusivement dans l'UE
- ✅ **Droit à l'effacement**: Support complet du "droit à l'oubli"
- ✅ **Portabilité des données**: Export dans des formats standards
- ✅ **Consentement**: Gestion des consentements intégrée
- ✅ **Notification de violation**: Alertes automatisées sous 72h
- ✅ **Chiffrement**: AES-256 pour les données au repos, TLS 1.3 en transit

### Configuration Recommandée pour la Conformité

```yaml
# config/config.yaml - Configuration EU GDPR-compliant
cortex:
  base_url: https://api-eu.xdr.paloaltonetworks.com
  use_env_secrets: true
  advanced_api: true
  
security:
  enable_ssl: true
  verify_certificates: true
  timeout: 300
  min_tls_version: "1.2"
  
privacy:
  data_retention_days: 365  # Maximum 1 an par défaut
  anonymize_pii: true
  audit_logging: true
  
gdpr:
  enabled: true
  data_processor_agreement: true
  breach_notification_email: dpo@votre-entreprise.com
  retention_policy: "auto_delete"
  
logging:
  level: INFO
  anonymize_ip: true
  exclude_sensitive_data: true
```

## 🔐 Permissions API Recommandées

Pour une conformité maximale, limitez les permissions aux besoins stricts :

### Permissions Essentielles
- ✅ `incidents.read` - Lecture des incidents
- ✅ `alerts.read` - Lecture des alertes
- ✅ `endpoints.read` - Lecture des endpoints
- ✅ `files.upload` - Upload de fichiers pour analyse

### Permissions Optionnelles (selon besoins)
- ⚠️ `incidents.write` - Modification des incidents
- ⚠️ `alerts.write` - Modification des alertes
- ⚠️ `xql.execute` - Exécution de requêtes XQL
- ⚠️ `endpoints.write` - Actions sur les endpoints

### Permissions à Éviter (sauf nécessité absolue)
- ❌ `admin.*` - Permissions administratives
- ❌ `users.*` - Gestion des utilisateurs
- ❌ `settings.*` - Modification des paramètres globaux

## 📊 Limites et Quotas EU

| Ressource | Limite | Remarques |
|-----------|--------|-----------|
| Requêtes API | 100/minute | Par clé API |
| Upload fichiers | 100 MB | Par fichier |
| Résultats XQL | 10,000 lignes | Par requête |
| Retention données | 365 jours | Configurable |
| Incidents actifs | 10,000 | Par tenant |

## 🌐 Points d'Accès EU

### API Endpoints
- **Principal**: `api-eu.xdr.paloaltonetworks.com`
- **Backup**: `api-eu-backup.xdr.paloaltonetworks.com`

### Console Web
- **URL**: `https://eu.xdr.paloaltonetworks.com`
- **Support**: `support-eu@paloaltonetworks.com`

## 🔄 Configuration de Basculement

Pour la haute disponibilité en EU :

```python
# Configuration Python avec failover
CORTEX_EU_ENDPOINTS = [
    "https://api-eu.xdr.paloaltonetworks.com",
    "https://api-eu-backup.xdr.paloaltonetworks.com"
]

def get_cortex_client():
    for endpoint in CORTEX_EU_ENDPOINTS:
        try:
            client = CortexClient(base_url=endpoint)
            if client.test_connection():
                return client
        except:
            continue
    raise Exception("Aucun endpoint EU disponible")
```

## 📝 Checklist de Conformité EU

### Avant le Déploiement
- [ ] DPA (Data Processing Agreement) signé avec Palo Alto Networks
- [ ] Notification à l'autorité de protection des données (si requis)
- [ ] Évaluation d'impact (DPIA) complétée
- [ ] Procédures de notification de violation documentées

### Configuration Technique
- [ ] Clés API créées avec permissions minimales
- [ ] Chiffrement activé pour toutes les communications
- [ ] Logs d'audit configurés et sécurisés
- [ ] Retention des données configurée selon politique

### Opérationnel
- [ ] Personnel formé sur les procédures GDPR
- [ ] Processus de réponse aux demandes GDPR établi
- [ ] Tests de restauration et suppression validés
- [ ] Monitoring de la conformité en place

## 🚨 Alertes et Notifications

### Configuration des Alertes GDPR

```yaml
# alerts/gdpr_alerts.yaml
alerts:
  - name: "Accès aux données personnelles"
    condition: "access_to_pii = true"
    severity: "high"
    notification:
      - email: "dpo@votre-entreprise.com"
      - slack: "#gdpr-alerts"
      
  - name: "Export de données volumineux"
    condition: "export_size > 1GB"
    severity: "medium"
    notification:
      - email: "security@votre-entreprise.com"
      
  - name: "Tentative d'accès hors EU"
    condition: "source_country NOT IN ('EU')"
    severity: "critical"
    notification:
      - email: "dpo@votre-entreprise.com"
      - pagerduty: "gdpr-violations"
```

## 📞 Support EU

### Contacts Techniques
- **Email**: `cortex-support-eu@paloaltonetworks.com`
- **Téléphone**: +49 89 444 456 000 (Allemagne)
- **Horaires**: 8h00 - 18h00 CET/CEST

### Contacts Conformité
- **DPO Palo Alto EU**: `dpo-eu@paloaltonetworks.com`
- **Urgences GDPR**: +31 20 754 3000 (24/7)

## 🔍 Ressources Supplémentaires

- [Documentation Cortex XDR EU](https://docs-cortex.paloaltonetworks.com/eu)
- [Guide de Conformité GDPR](https://www.paloaltonetworks.com/gdpr)
- [Certificats de Conformité](https://trust.paloaltonetworks.com)
- [Status Page EU](https://status-eu.paloaltonetworks.com)

---

*Dernière mise à jour : Juin 2025*
*Version : 2.0*
