#!/bin/bash
# Script de configuration automatique pour CortexDFIR-Forge
# Ce script facilite la configuration initiale du projet

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Fonction pour afficher le header
print_header() {
    echo -e "${BLUE}${BOLD}"
    echo "============================================================"
    echo "         CortexDFIR-Forge - Configuration Automatique       "
    echo "============================================================"
    echo -e "${NC}"
}

# Fonction pour afficher les messages
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Vérifier le système d'exploitation
check_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        print_error "Système d'exploitation non supporté: $OSTYPE"
        exit 1
    fi
    print_success "Système détecté: $OS"
}

# Vérifier Python
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python n'est pas installé. Veuillez installer Python 3.8+"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Python trouvé: $PYTHON_VERSION"
    
    # Vérifier la version minimale
    MIN_VERSION="3.8"
    if [ "$(printf '%s\n' "$MIN_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$MIN_VERSION" ]; then
        print_error "Python $MIN_VERSION ou supérieur est requis"
        exit 1
    fi
}

# Créer l'environnement virtuel
create_venv() {
    if [ ! -d ".venv" ]; then
        print_info "Création de l'environnement virtuel..."
        $PYTHON_CMD -m venv .venv
        print_success "Environnement virtuel créé"
    else
        print_info "Environnement virtuel déjà existant"
    fi
}

# Activer l'environnement virtuel
activate_venv() {
    if [[ "$OS" == "windows" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    print_success "Environnement virtuel activé"
}

# Installer les dépendances
install_dependencies() {
    print_info "Installation des dépendances Python..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Installer yara-python selon l'OS
    if [[ "$OS" == "windows" ]]; then
        print_info "Installation de yara-python pour Windows..."
        pip install yara-python
    else
        print_info "Installation de yara-python..."
        pip install yara-python
    fi
    
    print_success "Dépendances installées"
}

# Configurer les variables d'environnement
configure_env() {
    if [ -f ".env" ]; then
        print_warning "Fichier .env déjà existant"
        read -p "Voulez-vous le reconfigurer ? (o/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Oo]$ ]]; then
            return
        fi
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        print_info "Sauvegarde créée: .env.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Copier le template
    cp .env.example .env
    
    print_info "Configuration de Cortex XDR..."
    echo
    
    # Sélection de la région
    echo "Sélectionnez votre région Cortex XDR:"
    echo "1) Europe (EU) - Recommandé"
    echo "2) États-Unis (US)"
    echo "3) Asie-Pacifique (APAC)"
    read -p "Votre choix (1-3) [1]: " region_choice
    
    case ${region_choice:-1} in
        1)
            CORTEX_URL="https://api-eu.xdr.paloaltonetworks.com"
            REGION="EU"
            ;;
        2)
            CORTEX_URL="https://api-us.xdr.paloaltonetworks.com"
            REGION="US"
            ;;
        3)
            CORTEX_URL="https://api-apac.xdr.paloaltonetworks.com"
            REGION="APAC"
            ;;
        *)
            print_error "Choix invalide"
            exit 1
            ;;
    esac
    
    print_success "Région sélectionnée: $REGION"
    
    # Demander les clés API
    echo
    print_info "Entrez vos clés API Cortex XDR (disponibles dans la console Cortex XDR)"
    echo
    read -p "API Key: " api_key
    read -p "API Key ID: " api_key_id
    read -p "Tenant ID: " tenant_id
    
    # Mettre à jour le fichier .env
    if [[ "$OS" == "macos" ]]; then
        # macOS utilise sed différemment
        sed -i '' "s|CORTEX_BASE_URL=.*|CORTEX_BASE_URL=$CORTEX_URL|" .env
        sed -i '' "s|CORTEX_API_KEY=.*|CORTEX_API_KEY=$api_key|" .env
        sed -i '' "s|CORTEX_API_KEY_ID=.*|CORTEX_API_KEY_ID=$api_key_id|" .env
        sed -i '' "s|CORTEX_TENANT_ID=.*|CORTEX_TENANT_ID=$tenant_id|" .env
    else
        sed -i "s|CORTEX_BASE_URL=.*|CORTEX_BASE_URL=$CORTEX_URL|" .env
        sed -i "s|CORTEX_API_KEY=.*|CORTEX_API_KEY=$api_key|" .env
        sed -i "s|CORTEX_API_KEY_ID=.*|CORTEX_API_KEY_ID=$api_key_id|" .env
        sed -i "s|CORTEX_TENANT_ID=.*|CORTEX_TENANT_ID=$tenant_id|" .env
    fi
    
    print_success "Configuration sauvegardée dans .env"
}

# Créer les répertoires nécessaires
create_directories() {
    print_info "Création des répertoires nécessaires..."
    
    directories=(
        "data"
        "reports"
        "logs"
        "temp"
        "rules/custom"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_success "Répertoire créé: $dir"
        fi
    done
}

# Télécharger les règles YARA
download_yara_rules() {
    print_info "Vérification des règles YARA..."
    
    if [ ! -d "rules/yara-rules" ]; then
        print_info "Téléchargement des règles YARA..."
        git clone https://github.com/Yara-Rules/rules.git rules/yara-rules
        print_success "Règles YARA téléchargées"
    else
        print_info "Règles YARA déjà présentes"
        read -p "Voulez-vous les mettre à jour ? (o/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            cd rules/yara-rules
            git pull
            cd ../..
            print_success "Règles YARA mises à jour"
        fi
    fi
}

# Tester la connexion
test_connection() {
    print_info "Test de connexion à Cortex XDR..."
    echo
    
    if $PYTHON_CMD src/utils/test_cortex_connection.py; then
        echo
        print_success "Test de connexion réussi!"
    else
        echo
        print_error "Test de connexion échoué. Vérifiez vos clés API."
        print_info "Vous pouvez relancer le test avec: python src/utils/test_cortex_connection.py"
    fi
}

# Configuration Docker (optionnel)
configure_docker() {
    if command -v docker &> /dev/null; then
        print_info "Docker détecté"
        read -p "Voulez-vous configurer Docker ? (o/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Oo]$ ]]; then
            print_info "Création des secrets Docker..."
            
            # Charger les variables depuis .env
            source .env
            
            # Créer les secrets
            echo "$CORTEX_API_KEY" | docker secret create cortex_api_key - 2>/dev/null || true
            echo "$CORTEX_API_KEY_ID" | docker secret create cortex_api_key_id - 2>/dev/null || true
            echo "$CORTEX_TENANT_ID" | docker secret create cortex_tenant_id - 2>/dev/null || true
            
            # Générer des mots de passe aléatoires
            REDIS_PASSWORD=$(openssl rand -base64 32)
            GRAFANA_PASSWORD=$(openssl rand -base64 32)
            
            echo "$REDIS_PASSWORD" | docker secret create redis_password - 2>/dev/null || true
            echo "$GRAFANA_PASSWORD" | docker secret create grafana_password - 2>/dev/null || true
            echo "grafana_secret_$(date +%s)" | docker secret create grafana_secret_key - 2>/dev/null || true
            
            print_success "Secrets Docker créés"
            print_info "Mot de passe Grafana admin: $GRAFANA_PASSWORD"
            print_warning "Conservez ce mot de passe en lieu sûr!"
        fi
    fi
}

# Fonction principale
main() {
    print_header
    
    # Vérifications préliminaires
    check_os
    check_python
    
    # Configuration
    create_venv
    activate_venv
    install_dependencies
    configure_env
    create_directories
    download_yara_rules
    
    # Tests
    echo
    test_connection
    
    # Docker (optionnel)
    configure_docker
    
    # Résumé final
    echo
    echo -e "${GREEN}${BOLD}============================================================${NC}"
    echo -e "${GREEN}${BOLD}✅ Configuration terminée avec succès!${NC}"
    echo -e "${GREEN}${BOLD}============================================================${NC}"
    echo
    print_info "Pour démarrer CortexDFIR-Forge:"
    echo
    echo "  Option 1 - Interface graphique:"
    echo "    source .venv/bin/activate  # Linux/Mac"
    echo "    .venv\\Scripts\\activate     # Windows"
    echo "    python src/main.py"
    echo
    echo "  Option 2 - Docker:"
    echo "    docker-compose -f docker-compose.prod.yml up -d"
    echo
    print_info "Documentation complète: https://github.com/servais1983/CortexDFIR-Forge"
    echo
}

# Exécuter le script
main
