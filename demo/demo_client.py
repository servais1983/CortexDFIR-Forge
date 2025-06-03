#!/usr/bin/env python3
"""
Démonstration du client Cortex XDR
Ce script montre les principales fonctionnalités du client Cortex XDR
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta

# Ajout du chemin parent pour l'importation des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from src.core.cortex_client import CortexClient
from src.utils.config_manager import ConfigManager

def setup_logging():
    """Configuration du logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_config():
    """Chargement de la configuration"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def demo_analyze_file(cortex_client, file_path):
    """Démonstration de l'analyse de fichier"""
    logger.info("=== Démonstration de l'analyse de fichier ===")
    try:
        result = cortex_client.analyze_file(file_path)
        logger.info(f"Résultat de l'analyse : {json.dumps(result, indent=2)}")
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse : {str(e)}")

def demo_get_incidents(cortex_client):
    """Démonstration de la récupération des incidents"""
    logger.info("\n=== Démonstration de la récupération des incidents ===")
    try:
        # Récupération des incidents des dernières 24h
        time_frame = "last_24_hours"
        incidents = cortex_client.get_incidents(time_frame=time_frame)
        logger.info(f"Incidents trouvés : {len(incidents)}")
        for incident in incidents[:3]:  # Affiche les 3 premiers incidents
            logger.info(f"Incident : {json.dumps(incident, indent=2)}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des incidents : {str(e)}")

def demo_xql_query(cortex_client):
    """Démonstration de l'exécution d'une requête XQL"""
    logger.info("\n=== Démonstration de l'exécution d'une requête XQL ===")
    try:
        # Exemple de requête XQL pour les processus récents
        query = """
        dataset=xdr_data
        | filter event_type = "process"
        | fields timestamp, event_type, process_name, process_command_line
        | limit 5
        """
        results = cortex_client.execute_xql_query(query)
        logger.info(f"Résultats de la requête XQL : {json.dumps(results, indent=2)}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la requête XQL : {str(e)}")

def demo_get_endpoints(cortex_client):
    """Démonstration de la récupération des endpoints"""
    logger.info("\n=== Démonstration de la récupération des endpoints ===")
    try:
        endpoints = cortex_client.get_endpoints()
        logger.info(f"Endpoints trouvés : {len(endpoints)}")
        for endpoint in endpoints[:3]:  # Affiche les 3 premiers endpoints
            logger.info(f"Endpoint : {json.dumps(endpoint, indent=2)}")
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des endpoints : {str(e)}")

def main():
    """Fonction principale"""
    try:
        # Chargement de la configuration
        config = load_config()
        
        # Initialisation du client Cortex
        config_manager = ConfigManager()
        cortex_client = CortexClient(config_manager)
        
        # Création du dossier samples s'il n'existe pas
        samples_dir = os.path.join(os.path.dirname(__file__), 'samples')
        os.makedirs(samples_dir, exist_ok=True)
        
        # Création d'un fichier de test
        test_file = os.path.join(samples_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write("Ceci est un fichier de test pour la démonstration Cortex XDR")
        
        # Exécution des démonstrations
        demo_analyze_file(cortex_client, test_file)
        demo_get_incidents(cortex_client)
        demo_xql_query(cortex_client)
        demo_get_endpoints(cortex_client)
        
    except Exception as e:
        logger.error(f"Erreur lors de la démonstration : {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logger = setup_logging()
    main() 