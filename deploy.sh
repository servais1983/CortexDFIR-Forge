#!/bin/bash
# deploy.sh - Script de déploiement automatisé pour CortexDFIR-Forge
# Usage: ./deploy.sh [environment] [version]
# Exemple: ./deploy.sh production v2.0.0

set -euo pipefail

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="cortexdfir-forge"
DOCKER_IMAGE="${PROJECT_NAME}:production"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables d'environnement
ENVIRONMENT="${1:-production}"
VERSION="${2:-latest}"
DRY_RUN="${DRY_RUN:-false}"
SKIP_TESTS="${SKIP_TESTS:-false}"
FORCE_REBUILD="${FORCE_REBUILD:-false}"

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
}

check_prerequisites() {
    log "Vérification des prérequis..."
    
    # Vérifier Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé"
        exit 1
    fi
    
    # Vérifier Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé"
        exit 1
    fi
    
    # Vérifier les permissions Docker
    if ! docker info &> /dev/null; then
        log_error "Impossible d'accéder à Docker. Vérifiez les permissions."
        exit 1
    fi
    
    # Vérifier l'espace disque (minimum 10GB)
    available_space=$(df / | awk 'NR==2 {print $4}')
    min_space=$((10 * 1024 * 1024)) # 10GB en KB
    
    if [ "$available_space" -lt "$min_space" ]; then
        log_warning "Espace disque faible (< 10GB disponible)"
    fi
    
    log_success "Prérequis vérifiés"
}

create_directories() {
    log "Création des répertoires de données..."
    
    local dirs=(
        "/opt/cortexdfir-forge/data"
        "/opt/cortexdfir-forge/reports" 
        "/opt/cortexdfir-forge/redis"
        "/opt/cortexdfir-forge/prometheus"
        "/opt/cortexdfir-forge/grafana"
        "/var/log/cortexdfir-forge"
    )
    
    for dir in "${dirs[@]}"; do
        if [ "$DRY_RUN" = "false" ]; then
            sudo mkdir -p "$dir"
            sudo chown -R 1000:1000 "$dir"
        else
            log "DRY RUN: mkdir -p $dir"
        fi
    done
    
    log_success "Répertoires créés"
}

setup_secrets() {
    log "Configuration des secrets Docker..."
    
    # Vérifier si les secrets existent déjà
    local secrets=(
        "cortex_api_key"
        "cortex_api_key_id"
        "redis_password"
        "grafana_password"
        "grafana_secret_key"
    )
    
    for secret in "${secrets[@]}"; do
        if ! docker secret inspect "$secret" &> /dev/null; then
            if [ "$DRY_RUN" = "false" ]; then
                case "$secret" in
                    "cortex_api_key")
                        read -s -p "Cortex API Key: " api_key
                        echo
                        echo "$api_key" | docker secret create "$secret" -
                        ;;
                    "cortex_api_key_id")
                        read -s -p "Cortex API Key ID: " api_key_id
                        echo
                        echo "$api_key_id" | docker secret create "$secret" -
                        ;;
                    *"password"*|*"key"*)
                        openssl rand -base64 32 | docker secret create "$secret" -
                        ;;
                esac
            else
                log "DRY RUN: Créer secret $secret"
            fi
        else
            log "Secret $secret existe déjà"
        fi
    done
    
    log_success "Secrets configurés"
}

run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "Tests ignorés (SKIP_TESTS=true)"
        return 0
    fi
    
    log "Exécution des tests..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Tests unitaires
        if command -v python &> /dev/null; then
            python -m pytest tests/ -v --tb=short || log_warning "Tests unitaires échoués"
        fi
        
        # Tests de sécurité
        if command -v safety &> /dev/null; then
            safety check --file requirements-updated.txt || log_warning "Safety check échoué"
        fi
        
        if command -v bandit &> /dev/null; then
            bandit -r src/ -f json -o bandit-report.json || log_warning "Bandit scan échoué"
        fi
        
        log_success "Tests terminés"
    else
        log "DRY RUN: Exécution des tests"
    fi
}

build_image() {
    log "Construction de l'image Docker..."
    
    local build_args=""
    if [ "$FORCE_REBUILD" = "true" ]; then
        build_args="--no-cache"
    fi
    
    if [ "$DRY_RUN" = "false" ]; then
        docker build $build_args -t "$DOCKER_IMAGE" -t "${PROJECT_NAME}:${VERSION}" .
        log_success "Image construite: $DOCKER_IMAGE"
    else
        log "DRY RUN: docker build $build_args -t $DOCKER_IMAGE ."
    fi
}

deploy_services() {
    log "Déploiement des services..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Arrêt des services existants
        docker-compose -f docker-compose.prod.yml down --remove-orphans || true
        
        # Déploiement des nouveaux services
        docker-compose -f docker-compose.prod.yml up -d
        
        log_success "Services déployés"
    else
        log "DRY RUN: docker-compose -f docker-compose.prod.yml up -d"
    fi
}

wait_for_health() {
    log "Attente de la santé des services..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if [ "$DRY_RUN" = "false" ]; then
            if docker exec cortexdfir-forge-prod python src/utils/health_check.py 2>/dev/null; then
                log_success "Services en bonne santé"
                return 0
            fi
        else
            log "DRY RUN: Vérification de santé (tentative $attempt/$max_attempts)"
            if [ $attempt -eq 3 ]; then
                log_success "DRY RUN: Services simulés comme sains"
                return 0
            fi
        fi
        
        log "Tentative $attempt/$max_attempts - En attente..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Services non sains après $max_attempts tentatives"
    return 1
}

run_smoke_tests() {
    log "Exécution des tests de fumée..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Test API de base
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API accessible"
        else
            log_warning "API non accessible"
        fi
        
        # Test Prometheus metrics
        if curl -f http://localhost:9090/-/ready > /dev/null 2>&1; then
            log_success "Prometheus accessible"
        else
            log_warning "Prometheus non accessible"
        fi
        
        # Test Grafana
        if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
            log_success "Grafana accessible"
        else
            log_warning "Grafana non accessible"
        fi
    else
        log "DRY RUN: Tests de fumée"
    fi
}

cleanup() {
    log "Nettoyage..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Nettoyage des images Docker non utilisées
        docker image prune -f || true
        
        # Nettoyage des volumes non utilisés
        docker volume prune -f || true
        
        log_success "Nettoyage terminé"
    else
        log "DRY RUN: Nettoyage"
    fi
}

rollback() {
    log_error "Rollback en cours..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Arrêter les services actuels
        docker-compose -f docker-compose.prod.yml down || true
        
        # Restaurer la dernière version fonctionnelle
        if docker image inspect "${PROJECT_NAME}:previous" &> /dev/null; then
            docker tag "${PROJECT_NAME}:previous" "$DOCKER_IMAGE"
            docker-compose -f docker-compose.prod.yml up -d
            log_success "Rollback effectué vers la version précédente"
        else
            log_error "Aucune version précédente disponible pour le rollback"
        fi
    else
        log "DRY RUN: Rollback vers version précédente"
    fi
}

create_backup() {
    log "Création d'une sauvegarde pré-déploiement..."
    
    if [ "$DRY_RUN" = "false" ]; then
        # Sauvegarder l'image actuelle
        if docker image inspect "$DOCKER_IMAGE" &> /dev/null; then
            docker tag "$DOCKER_IMAGE" "${PROJECT_NAME}:previous"
            log_success "Image sauvegardée comme ${PROJECT_NAME}:previous"
        fi
        
        # Exécuter le script de sauvegarde si disponible
        if [ -f "./scripts/backup.sh" ]; then
            ./scripts/backup.sh
        fi
    else
        log "DRY RUN: Création de sauvegarde"
    fi
}

show_usage() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [VERSION] [OPTIONS]

Arguments:
    ENVIRONMENT    Environnement de déploiement (défaut: production)
    VERSION        Version à déployer (défaut: latest)

Variables d'environnement:
    DRY_RUN        Mode simulation (true/false, défaut: false)
    SKIP_TESTS     Ignorer les tests (true/false, défaut: false)
    FORCE_REBUILD  Forcer la reconstruction (true/false, défaut: false)

Exemples:
    $0                              # Déploie en production avec la version latest
    $0 staging v1.0.0               # Déploie la version v1.0.0 en staging
    DRY_RUN=true $0 production      # Mode simulation
    SKIP_TESTS=true $0 production   # Déploie sans exécuter les tests

EOF
}

# ==============================================================================
# FONCTION PRINCIPALE
# ==============================================================================

main() {
    # Gestion des arguments
    case "${1:-}" in
        -h|--help)
            show_usage
            exit 0
            ;;
    esac
    
    log "🚀 Début du déploiement CortexDFIR-Forge"
    log "Environnement: $ENVIRONMENT"
    log "Version: $VERSION"
    log "Mode DRY RUN: $DRY_RUN"
    
    # Définir le gestionnaire d'erreur
    trap 'log_error "Erreur détectée. Arrêt du déploiement."; rollback; exit 1' ERR
    
    # Étapes du déploiement
    check_prerequisites
    create_directories
    
    if [ "$ENVIRONMENT" = "production" ]; then
        setup_secrets
        create_backup
    fi
    
    run_tests
    build_image
    deploy_services
    wait_for_health
    run_smoke_tests
    cleanup
    
    log_success "🎉 Déploiement terminé avec succès!"
    log "Services disponibles:"
    log "  - Application: http://localhost:8000"
    log "  - Prometheus: http://localhost:9090"
    log "  - Grafana: http://localhost:3000"
    
    # Affichage du statut des services
    if [ "$DRY_RUN" = "false" ]; then
        echo ""
        docker-compose -f docker-compose.prod.yml ps
    fi
}

# ==============================================================================
# POINT D'ENTRÉE
# ==============================================================================

# Vérifier si le script est exécuté directement
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
