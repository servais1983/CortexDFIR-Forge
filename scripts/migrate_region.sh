#!/bin/bash
# Script de migration de région pour CortexDFIR-Forge
# Facilite le changement de région Cortex XDR

set -e

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

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

# Vérifier les arguments
if [ -z "$1" ]; then
    echo -e "${BOLD}Usage: ./migrate_region.sh [EU|US|APAC]${NC}"
    echo
    echo "Régions disponibles:"
    echo "  EU   - Europe (api-eu.xdr.paloaltonetworks.com)"
    echo "  US   - États-Unis (api-us.xdr.paloaltonetworks.com)"
    echo "  APAC - Asie-Pacifique (api-apac.xdr.paloaltonetworks.com)"
    echo
    echo "Exemple: ./migrate_region.sh EU"
    exit 1
fi

REGION=$(echo "$1" | tr '[:lower:]' '[:upper:]')

# Définir l'URL selon la région
case $REGION in
    EU)
        URL="https://api-eu.xdr.paloaltonetworks.com"
        REGION_NAME="Europe"
        ;;
    US)
        URL="https://api-us.xdr.paloaltonetworks.com"
        REGION_NAME="États-Unis"
        ;;
    APAC)
        URL="https://api-apac.xdr.paloaltonetworks.com"
        REGION_NAME="Asie-Pacifique"
        ;;
    *)
        print_error "Région invalide: $1"
        echo "Utilisez EU, US ou APAC"
        exit 1
        ;;
esac

echo -e "${BLUE}${BOLD}"
echo "============================================================"
echo "     Migration vers la région $REGION_NAME ($REGION)        "
echo "============================================================"
echo -e "${NC}"

# Vérifier l'existence du fichier .env
if [ ! -f ".env" ]; then
    print_error "Fichier .env non trouvé"
    print_info "Créez d'abord le fichier avec: cp .env.example .env"
    exit 1
fi

# Afficher la configuration actuelle
print_info "Configuration actuelle:"
current_url=$(grep "CORTEX_BASE_URL=" .env | cut -d'=' -f2)
if [ -n "$current_url" ]; then
    echo "  URL actuelle: $current_url"
    
    # Déterminer la région actuelle
    if [[ "$current_url" == *"eu"* ]]; then
        current_region="EU"
    elif [[ "$current_url" == *"us"* ]]; then
        current_region="US"
    elif [[ "$current_url" == *"apac"* ]]; then
        current_region="APAC"
    else
        current_region="Inconnue"
    fi
    echo "  Région actuelle: $current_region"
else
    print_warning "URL actuelle non définie"
fi

echo

# Demander confirmation
if [ "$current_region" == "$REGION" ]; then
    print_warning "Vous êtes déjà sur la région $REGION"
    read -p "Voulez-vous continuer quand même ? (o/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Oo]$ ]]; then
        exit 0
    fi
fi

# Créer une sauvegarde
backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$backup_file"
print_success "Sauvegarde créée: $backup_file"

# Mettre à jour l'URL
print_info "Mise à jour de la configuration..."

# Détecter l'OS pour sed
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|CORTEX_BASE_URL=.*|CORTEX_BASE_URL=$URL|" .env
else
    # Linux/Windows
    sed -i "s|CORTEX_BASE_URL=.*|CORTEX_BASE_URL=$URL|" .env
fi

# Vérifier si la ligne existe, sinon l'ajouter
if ! grep -q "CORTEX_BASE_URL=" .env; then
    echo "CORTEX_BASE_URL=$URL" >> .env
fi

print_success "Configuration mise à jour"

# Mettre à jour config.yaml si il existe
if [ -f "config/config.yaml" ]; then
    print_info "Mise à jour de config.yaml..."
    
    # Créer une sauvegarde
    cp config/config.yaml "config/config.yaml.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Mettre à jour l'URL dans config.yaml
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|base_url:.*|base_url: $URL|" config/config.yaml
    else
        sed -i "s|base_url:.*|base_url: $URL|" config/config.yaml
    fi
    
    print_success "config.yaml mis à jour"
fi

echo
echo -e "${GREEN}${BOLD}============================================================${NC}"
echo -e "${GREEN}${BOLD}✅ Migration vers $REGION_NAME terminée avec succès!${NC}"
echo -e "${GREEN}${BOLD}============================================================${NC}"
echo

print_info "Nouvelle configuration:"
echo "  📍 Région: $REGION_NAME ($REGION)"
echo "  🌐 URL: $URL"
echo

print_warning "Actions requises:"
echo
echo "1. Générer de nouvelles clés API pour la région $REGION_NAME:"
echo "   - Connectez-vous à la console Cortex XDR de $REGION_NAME"
echo "   - Allez dans Settings > Configurations > API Keys"
echo "   - Créez de nouvelles clés avec les permissions appropriées"
echo
echo "2. Mettre à jour vos clés dans .env:"
echo "   CORTEX_API_KEY=nouvelle_cle_api"
echo "   CORTEX_API_KEY_ID=nouveau_id_cle_api"
echo "   CORTEX_TENANT_ID=nouveau_tenant_id"
echo
echo "3. Tester la connexion:"
echo "   python src/utils/test_cortex_connection.py"
echo

# Option pour éditer le fichier .env
read -p "Voulez-vous éditer .env maintenant ? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    # Déterminer l'éditeur
    if [ -n "$EDITOR" ]; then
        $EDITOR .env
    elif command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    elif command -v vi &> /dev/null; then
        vi .env
    else
        print_warning "Aucun éditeur trouvé. Éditez manuellement .env"
    fi
fi

# Option pour tester la connexion
echo
read -p "Voulez-vous tester la connexion maintenant ? (o/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Oo]$ ]]; then
    if command -v python3 &> /dev/null; then
        python3 src/utils/test_cortex_connection.py
    elif command -v python &> /dev/null; then
        python src/utils/test_cortex_connection.py
    else
        print_error "Python non trouvé. Installez Python pour tester la connexion."
    fi
fi

echo
print_info "Pour restaurer la configuration précédente:"
echo "  cp $backup_file .env"
echo
