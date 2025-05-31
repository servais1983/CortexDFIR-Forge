# 🚀 Guide de Déploiement en Production - CortexDFIR-Forge

Ce guide détaille les meilleures pratiques pour déployer CortexDFIR-Forge dans un environnement de production sécurisé.

## 📋 Table des Matières

- [Architecture de Production](#architecture-de-production)
- [Prérequis Infrastructure](#prérequis-infrastructure)
- [Déploiement avec Docker](#déploiement-avec-docker)
- [Configuration de Sécurité](#configuration-de-sécurité)
- [Monitoring et Observabilité](#monitoring-et-observabilité)
- [Sauvegarde et Récupération](#sauvegarde-et-récupération)
- [Maintenance et Mises à Jour](#maintenance-et-mises-à-jour)
- [Dépannage Production](#dépannage-production)

## 🏗️ Architecture de Production

### Architecture Recommandée

```
┌─────────────────────────────────────────────────────────────┐
│                    DMZ/Zone Sécurisée                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Load       │    │ CortexDFIR  │    │   Backup    │     │
│  │ Balancer    │────│   Forge     │────│   Server    │     │
│  │ (HAProxy)   │    │ (Primary)   │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   Reverse   │    │ CortexDFIR  │    │ Monitoring  │     │
│  │   Proxy     │    │   Forge     │    │ (Grafana)   │     │
│  │  (Nginx)    │    │ (Standby)   │    │             │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────────────────────┐
            │        Cortex XDR API          │
            │     (Palo Alto Networks)       │
            └─────────────────────────────────┘
```

## 🔧 Prérequis Infrastructure

### Spécifications Serveur

#### Serveur Principal (Production)
- **CPU** : 8+ cœurs (Intel Xeon ou AMD EPYC)
- **RAM** : 32 GB minimum, 64 GB recommandé
- **Stockage** : 
  - SSD 500 GB pour l'OS et applications
  - SSD 2 TB pour les données et analyses
  - Stockage réseau pour les sauvegardes
- **Réseau** : 1 Gbps minimum, 10 Gbps recommandé
- **OS** : Ubuntu 22.04 LTS ou RHEL 9

## 🐳 Déploiement avec Docker

### Dockerfile de Production

```dockerfile
# Dockerfile
FROM python:3.11-slim-bullseye

# Métadonnées
LABEL maintainer="CortexDFIR-Forge Team"
LABEL version="1.0.0"
LABEL description="CortexDFIR-Forge Production Container"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV APP_HOME=/app
ENV APP_USER=cortexdfir
ENV APP_GROUP=cortexdfir

# Création de l'utilisateur non-privilégié
RUN groupadd -r ${APP_GROUP} && \
    useradd -r -g ${APP_GROUP} -d ${APP_HOME} -s /bin/bash ${APP_USER}

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libmagic1 \
        libmagic-dev \
        build-essential \
        libssl-dev \
        libffi-dev \
        curl \
        wget \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Création du répertoire de travail
WORKDIR ${APP_HOME}

# Copie des fichiers de dépendances
COPY requirements-updated.txt ./

# Installation des dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-updated.txt

# Copie du code source
COPY --chown=${APP_USER}:${APP_GROUP} . .

# Configuration des permissions
RUN chown -R ${APP_USER}:${APP_GROUP} ${APP_HOME} && \
    chmod -R 755 ${APP_HOME}/src && \
    chmod -R 644 ${APP_HOME}/rules && \
    chmod 600 ${APP_HOME}/config/config.json

# Changement vers l'utilisateur non-privilégié
USER ${APP_USER}

# Exposition du port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python src/utils/health_check.py || exit 1

# Point d'entrée
ENTRYPOINT ["python", "src/main.py"]
CMD ["--server", "--port", "8000"]
```

### Docker Compose pour Production

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  cortexdfir-forge:
    build: 
      context: .
      dockerfile: Dockerfile
    image: cortexdfir-forge:latest
    container_name: cortexdfir-forge-prod
    restart: unless-stopped
    environment:
      - ENV=production
      - LOG_LEVEL=INFO
      - CORTEX_API_KEY_FILE=/run/secrets/cortex_api_key
      - CORTEX_API_KEY_ID_FILE=/run/secrets/cortex_api_key_id
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "127.0.0.1:8000:8000"
    networks:
      - cortex-network
    secrets:
      - cortex_api_key
      - cortex_api_key_id
    depends_on:
      - redis
      - prometheus
    deploy:
      resources:
        limits:
          memory: 16G
          cpus: '4.0'
        reservations:
          memory: 8G
          cpus: '2.0'

  nginx:
    image: nginx:1.25-alpine
    container_name: cortexdfir-nginx
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./logs/nginx:/var/log/nginx
    networks:
      - cortex-network
    depends_on:
      - cortexdfir-forge

  redis:
    image: redis:7-alpine
    container_name: cortexdfir-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - cortex-network
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'

  prometheus:
    image: prom/prometheus:latest
    container_name: cortexdfir-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "127.0.0.1:9090:9090"
    networks:
      - cortex-network

  grafana:
    image: grafana/grafana:latest
    container_name: cortexdfir-grafana
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    ports:
      - "127.0.0.1:3000:3000"
    networks:
      - cortex-network
    depends_on:
      - prometheus

networks:
  cortex-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  redis-data:
  prometheus-data:
  grafana-data:

secrets:
  cortex_api_key:
    external: true
  cortex_api_key_id:
    external: true
```

## 🔒 Configuration de Sécurité

### Configuration Nginx SSL

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';
    
    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log warn;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    upstream cortexdfir {
        server cortexdfir-forge:8000;
        keepalive 32;
    }
    
    server {
        listen 80;
        server_name _;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name cortexdfir.your-domain.com;
        
        ssl_certificate /etc/nginx/ssl/cortexdfir.crt;
        ssl_certificate_key /etc/nginx/ssl/cortexdfir.key;
        
        # Client certificate authentication (optionnel)
        # ssl_client_certificate /etc/nginx/ssl/ca.crt;
        # ssl_verify_client on;
        
        client_max_body_size 100M;
        
        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://cortexdfir;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 300s;
        }
        
        # Authentication endpoints
        location /auth/ {
            limit_req zone=login burst=5 nodelay;
            proxy_pass http://cortexdfir;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            proxy_pass http://cortexdfir;
            access_log off;
        }
    }
}
```

### Configuration des Secrets

```bash
# create-secrets.sh
#!/bin/bash

# Création des secrets Docker
echo "Création des secrets pour la production..."

# API Keys Cortex XDR
read -s -p "Cortex API Key: " CORTEX_API_KEY
echo
read -s -p "Cortex API Key ID: " CORTEX_API_KEY_ID
echo

# Création des secrets
echo "$CORTEX_API_KEY" | docker secret create cortex_api_key -
echo "$CORTEX_API_KEY_ID" | docker secret create cortex_api_key_id -

# Passwords pour les services
openssl rand -base64 32 | docker secret create redis_password -
openssl rand -base64 32 | docker secret create grafana_password -

echo "Secrets créés avec succès!"
```

## 📊 Monitoring et Observabilité

### Configuration Prometheus

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: 'cortexdfir-forge'
    static_configs:
      - targets: ['cortexdfir-forge:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Alertes Prometheus

```yaml
# monitoring/alert_rules.yml
groups:
- name: cortexdfir-forge
  rules:
  - alert: CortexDFIRServiceDown
    expr: up{job="cortexdfir-forge"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "CortexDFIR-Forge service is down"
      description: "CortexDFIR-Forge service has been down for more than 1 minute"
      
  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.85
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage detected"
      description: "Memory usage is above 85% for more than 5 minutes"
      
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage detected"
      description: "CPU usage is above 80% for more than 5 minutes"
      
  - alert: CortexAPIError
    expr: increase(cortex_api_errors_total[5m]) > 10
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "High number of Cortex XDR API errors"
      description: "More than 10 API errors in the last 5 minutes"
```

### Health Check Script

```python
# src/utils/health_check.py
#!/usr/bin/env python3
"""
Script de vérification de santé pour CortexDFIR-Forge
"""

import sys
import time
import requests
import json
from pathlib import Path

def check_api_health():
    """Vérifie la santé de l'API"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        return response.status_code == 200
    except:
        return False

def check_cortex_connectivity():
    """Vérifie la connectivité avec Cortex XDR"""
    try:
        # Import local modules
        sys.path.append('/app/src')
        from core.cortex_client import CortexClient
        from utils.config_manager import ConfigManager
        
        config_manager = ConfigManager()
        client = CortexClient(config_manager)
        
        # Test simple de connectivité
        headers = client._get_auth_headers()
        return 'Authorization' in headers
    except:
        return False

def check_disk_space():
    """Vérifie l'espace disque disponible"""
    try:
        import shutil
        total, used, free = shutil.disk_usage('/app')
        free_percent = (free / total) * 100
        return free_percent > 10  # Au moins 10% libre
    except:
        return False

def check_memory_usage():
    """Vérifie l'utilisation mémoire"""
    try:
        import psutil
        memory = psutil.virtual_memory()
        return memory.percent < 90  # Moins de 90% utilisé
    except:
        return False

def main():
    """Fonction principale de vérification"""
    checks = {
        'api': check_api_health(),
        'cortex': check_cortex_connectivity(),
        'disk': check_disk_space(),
        'memory': check_memory_usage()
    }
    
    # Log des résultats
    health_status = {
        'timestamp': time.time(),
        'status': 'healthy' if all(checks.values()) else 'unhealthy',
        'checks': checks
    }
    
    print(json.dumps(health_status))
    
    # Exit code pour Docker health check
    sys.exit(0 if all(checks.values()) else 1)

if __name__ == '__main__':
    main()
```

## 💾 Sauvegarde et Récupération

### Script de Sauvegarde

```bash
#!/bin/bash
# backup.sh - Script de sauvegarde pour CortexDFIR-Forge

set -euo pipefail

# Configuration
BACKUP_DIR="/backup/cortexdfir-forge"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="cortexdfir_backup_${TIMESTAMP}"

# Création du répertoire de sauvegarde
mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"

echo "Début de la sauvegarde: $(date)"

# 1. Sauvegarde de la configuration
echo "Sauvegarde de la configuration..."
cp -r /app/config "${BACKUP_DIR}/${BACKUP_NAME}/"

# 2. Sauvegarde des règles YARA personnalisées
echo "Sauvegarde des règles YARA..."
cp -r /app/rules "${BACKUP_DIR}/${BACKUP_NAME}/"

# 3. Sauvegarde des données d'analyse
echo "Sauvegarde des données..."
if [ -d "/app/data" ]; then
    cp -r /app/data "${BACKUP_DIR}/${BACKUP_NAME}/"
fi

# 4. Sauvegarde des logs récents (7 derniers jours)
echo "Sauvegarde des logs récents..."
find /app/logs -name "*.log" -mtime -7 -exec cp {} "${BACKUP_DIR}/${BACKUP_NAME}/" \;

# 5. Export des métriques Redis
echo "Sauvegarde des données Redis..."
docker exec cortexdfir-redis redis-cli BGSAVE
sleep 10
docker cp cortexdfir-redis:/data/dump.rdb "${BACKUP_DIR}/${BACKUP_NAME}/redis_dump.rdb"

# 6. Compression de la sauvegarde
echo "Compression de la sauvegarde..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
rm -rf "${BACKUP_NAME}"

# 7. Nettoyage des anciennes sauvegardes
echo "Nettoyage des anciennes sauvegardes..."
find "${BACKUP_DIR}" -name "cortexdfir_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete

# 8. Vérification de l'intégrité
echo "Vérification de l'intégrité..."
if tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" > /dev/null; then
    echo "✅ Sauvegarde réussie: ${BACKUP_NAME}.tar.gz"
else
    echo "❌ Erreur lors de la vérification de la sauvegarde"
    exit 1
fi

# 9. Synchronisation vers stockage distant (optionnel)
if [ "${REMOTE_BACKUP:-false}" = "true" ]; then
    echo "Synchronisation vers le stockage distant..."
    rsync -avz "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" "${REMOTE_BACKUP_HOST}:${REMOTE_BACKUP_PATH}"
fi

echo "Sauvegarde terminée: $(date)"
```

### Script de Restauration

```bash
#!/bin/bash
# restore.sh - Script de restauration pour CortexDFIR-Forge

set -euo pipefail

BACKUP_FILE="$1"
RESTORE_DIR="/app"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Fichier de sauvegarde non trouvé: $BACKUP_FILE"
    exit 1
fi

echo "Début de la restauration depuis: $BACKUP_FILE"

# 1. Arrêt des services
echo "Arrêt des services..."
docker-compose -f docker-compose.prod.yml down

# 2. Sauvegarde de l'état actuel
echo "Sauvegarde de l'état actuel..."
CURRENT_BACKUP="/tmp/cortexdfir_current_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$CURRENT_BACKUP"
cp -r "$RESTORE_DIR/config" "$CURRENT_BACKUP/" 2>/dev/null || true
cp -r "$RESTORE_DIR/data" "$CURRENT_BACKUP/" 2>/dev/null || true

# 3. Extraction de la sauvegarde
echo "Extraction de la sauvegarde..."
TEMP_DIR="/tmp/cortexdfir_restore"
mkdir -p "$TEMP_DIR"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# 4. Restauration des fichiers
echo "Restauration des fichiers..."
BACKUP_CONTENT=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "cortexdfir_backup_*" | head -1)

if [ -n "$BACKUP_CONTENT" ]; then
    cp -r "$BACKUP_CONTENT/config" "$RESTORE_DIR/" 2>/dev/null || true
    cp -r "$BACKUP_CONTENT/rules" "$RESTORE_DIR/" 2>/dev/null || true
    cp -r "$BACKUP_CONTENT/data" "$RESTORE_DIR/" 2>/dev/null || true
else
    echo "❌ Structure de sauvegarde invalide"
    exit 1
fi

# 5. Restauration Redis
echo "Restauration des données Redis..."
if [ -f "$BACKUP_CONTENT/redis_dump.rdb" ]; then
    docker-compose -f docker-compose.prod.yml up -d redis
    sleep 10
    docker cp "$BACKUP_CONTENT/redis_dump.rdb" cortexdfir-redis:/data/dump.rdb
    docker restart cortexdfir-redis
fi

# 6. Redémarrage des services
echo "Redémarrage des services..."
docker-compose -f docker-compose.prod.yml up -d

# 7. Vérification de la santé
echo "Vérification de la santé des services..."
sleep 30
if docker exec cortexdfir-forge-prod python src/utils/health_check.py; then
    echo "✅ Restauration réussie"
    rm -rf "$TEMP_DIR"
else
    echo "❌ Problème détecté après restauration"
    echo "Sauvegarde de l'état actuel disponible dans: $CURRENT_BACKUP"
    exit 1
fi

echo "Restauration terminée: $(date)"
```

## 🔄 Maintenance et Mises à Jour

### Script de Mise à Jour

```bash
#!/bin/bash
# update.sh - Script de mise à jour pour CortexDFIR-Forge

set -euo pipefail

# Configuration
REPO_URL="https://github.com/servais1983/CortexDFIR-Forge.git"
BRANCH="master"
BACKUP_BEFORE_UPDATE=true

echo "🚀 Début de la mise à jour CortexDFIR-Forge"

# 1. Sauvegarde automatique avant mise à jour
if [ "$BACKUP_BEFORE_UPDATE" = true ]; then
    echo "📦 Sauvegarde automatique avant mise à jour..."
    ./backup.sh
fi

# 2. Récupération des dernières modifications
echo "📥 Récupération des dernières modifications..."
git fetch origin
git checkout $BRANCH
git pull origin $BRANCH

# 3. Vérification des changements de dépendances
echo "🔍 Vérification des dépendances..."
if ! cmp -s requirements.txt requirements-updated.txt; then
    echo "⚠️  Nouvelles dépendances détectées"
    pip install -r requirements-updated.txt
fi

# 4. Tests de pré-déploiement
echo "🧪 Exécution des tests..."
python -m pytest tests/ -v --tb=short

# 5. Reconstruction des images Docker
echo "🐳 Reconstruction des images Docker..."
docker-compose -f docker-compose.prod.yml build --no-cache

# 6. Déploiement en rolling update
echo "🔄 Déploiement en rolling update..."
docker-compose -f docker-compose.prod.yml up -d --no-deps cortexdfir-forge

# 7. Vérification de la santé post-déploiement
echo "❤️  Vérification de la santé..."
sleep 30
for i in {1..5}; do
    if docker exec cortexdfir-forge-prod python src/utils/health_check.py; then
        echo "✅ Service sain après mise à jour"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ Service non sain après mise à jour - rollback nécessaire"
        exit 1
    fi
    sleep 10
done

# 8. Mise à jour des autres services
echo "🔄 Mise à jour des services auxiliaires..."
docker-compose -f docker-compose.prod.yml up -d

echo "✅ Mise à jour terminée avec succès!"
```

### Maintenance Préventive

```bash
#!/bin/bash
# maintenance.sh - Script de maintenance préventive

# 1. Nettoyage des logs anciens
find /app/logs -name "*.log" -mtime +90 -delete

# 2. Nettoyage des fichiers temporaires
find /tmp -name "cortex_*" -mtime +7 -delete

# 3. Optimisation des bases de données
docker exec cortexdfir-redis redis-cli BGREWRITEAOF

# 4. Vérification de l'espace disque
df -h | awk '$5 > 80 {print "ATTENTION: Disque " $1 " utilisé à " $5}'

# 5. Mise à jour des règles YARA
cd /app/rules
git pull origin master

# 6. Redémarrage hebdomadaire (si nécessaire)
if [ "$(date +%u)" = "7" ] && [ "$(date +%H)" = "02" ]; then
    docker-compose -f docker-compose.prod.yml restart
fi
```

Ce guide de déploiement production fournit une base solide pour un déploiement sécurisé et maintenable de CortexDFIR-Forge. Adaptez les configurations selon vos besoins spécifiques et votre infrastructure.
