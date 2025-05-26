#!/bin/bash

# Script d'audit de sécurité des dépendances pour CortexDFIR-Forge
# Ce script vérifie les vulnérabilités dans les dépendances Python

echo "=== Audit de sécurité des dépendances CortexDFIR-Forge ==="
echo "Date d'exécution: $(date)"
echo

# Vérification de l'environnement virtuel
if [ ! -d "venv" ]; then
    echo "Erreur: Environnement virtuel non trouvé."
    echo "Veuillez exécuter installer.bat ou créer un environnement virtuel avant l'audit."
    exit 1
fi

# Activation de l'environnement virtuel
echo "Activation de l'environnement virtuel..."
source venv/bin/activate || { echo "Erreur lors de l'activation de l'environnement virtuel."; exit 1; }

# Mise à jour de pip
echo "Mise à jour de pip..."
pip install --upgrade pip || { echo "Erreur lors de la mise à jour de pip."; exit 1; }

# Vérification des dépendances installées
echo "Vérification des dépendances installées..."
pip freeze > installed_dependencies.txt
echo "Liste des dépendances installées sauvegardée dans installed_dependencies.txt"

# Audit avec pip-audit
echo
echo "=== Audit avec pip-audit ==="
pip-audit || echo "Avertissement: pip-audit a détecté des problèmes potentiels."

# Audit avec safety
echo
echo "=== Audit avec safety ==="
safety check || echo "Avertissement: safety a détecté des problèmes potentiels."

# Génération du rapport d'audit
echo
echo "Génération du rapport d'audit complet..."
mkdir -p security_reports
REPORT_FILE="security_reports/dependency_audit_$(date +%Y%m%d_%H%M%S).txt"

{
    echo "=== Rapport d'audit de sécurité des dépendances CortexDFIR-Forge ==="
    echo "Date: $(date)"
    echo
    echo "=== Dépendances installées ==="
    cat installed_dependencies.txt
    echo
    echo "=== Résultats pip-audit ==="
    pip-audit 2>&1
    echo
    echo "=== Résultats safety ==="
    safety check 2>&1
} > "$REPORT_FILE"

echo "Rapport d'audit complet généré: $REPORT_FILE"

# Nettoyage
rm installed_dependencies.txt

echo
echo "Audit de sécurité terminé."
echo "Vérifiez le rapport pour les vulnérabilités potentielles et mettez à jour les dépendances si nécessaire."
echo

# Désactivation de l'environnement virtuel
deactivate
