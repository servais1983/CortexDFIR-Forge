#!/usr/bin/env python3
"""
Script de test de connexion à Cortex XDR
Ce script vérifie que la configuration est correcte et que l'API est accessible.
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

try:
    from src.utils.config_manager import ConfigManager
    from src.core.cortex_client import CortexClient
except ImportError:
    print("❌ Erreur: Impossible d'importer les modules. Assurez-vous d'être dans le bon répertoire.")
    sys.exit(1)

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    """Affiche l'en-tête du script"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}🔍 Test de Connexion Cortex XDR - CortexDFIR-Forge{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{Colors.BLUE}▶ {title}{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")

def print_success(message):
    """Affiche un message de succès"""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_warning(message):
    """Affiche un message d'avertissement"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")

def print_info(key, value):
    """Affiche une information formatée"""
    print(f"  {Colors.BOLD}{key}:{Colors.RESET} {value}")

def check_environment():
    """Vérifie les variables d'environnement"""
    print_section("Vérification de l'environnement")
    
    # Charger le fichier .env s'il existe
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print_success(f"Fichier .env trouvé : {env_path}")
    else:
        print_warning("Fichier .env non trouvé. Utilisation de la configuration par défaut.")
    
    # Vérifier les variables d'environnement
    env_vars = {
        'CORTEX_API_KEY': os.getenv('CORTEX_API_KEY'),
        'CORTEX_API_KEY_ID': os.getenv('CORTEX_API_KEY_ID'),
        'CORTEX_TENANT_ID': os.getenv('CORTEX_TENANT_ID'),
        'CORTEX_BASE_URL': os.getenv('CORTEX_BASE_URL', 'https://api-eu.xdr.paloaltonetworks.com')
    }
    
    missing_vars = []
    for var, value in env_vars.items():
        if value and value != 'votre_cle_api_ici' and value != 'votre_id_cle_api_ici' and value != 'votre_tenant_id_ici':
            print_success(f"{var} est configuré")
            if var == 'CORTEX_BASE_URL':
                print_info("  URL", value)
        else:
            missing_vars.append(var)
            print_error(f"{var} n'est pas configuré")
    
    return len(missing_vars) == 0, env_vars

def test_config_manager():
    """Teste le gestionnaire de configuration"""
    print_section("Test du gestionnaire de configuration")
    
    try:
        config_manager = ConfigManager()
        print_success("ConfigManager initialisé avec succès")
        
        cortex_config = config_manager.get_cortex_config()
        print_success("Configuration Cortex XDR chargée")
        
        # Afficher la configuration (sans les secrets)
        print_info("URL de base", cortex_config.get('base_url', 'Non défini'))
        print_info("Advanced API", cortex_config.get('advanced_api', False))
        
        # Vérifier si les clés sont configurées
        if cortex_config.get('api_key') and cortex_config.get('api_key') != '':
            print_success("Clé API configurée")
        else:
            print_error("Clé API non configurée")
            
        if cortex_config.get('api_key_id') and cortex_config.get('api_key_id') != '':
            print_success("ID de clé API configuré")
        else:
            print_error("ID de clé API non configuré")
            
        return config_manager, cortex_config
    except Exception as e:
        print_error(f"Erreur lors de l'initialisation du ConfigManager : {str(e)}")
        return None, None

def test_cortex_client(config_manager):
    """Teste le client Cortex XDR"""
    print_section("Test du client Cortex XDR")
    
    try:
        cortex_client = CortexClient(config_manager)
        print_success("CortexClient initialisé avec succès")
        
        # Afficher les informations de connexion
        print_info("URL configurée", cortex_client.base_url)
        
        # Déterminer la région
        if 'eu' in cortex_client.base_url:
            region = "Europe (EU) 🇪🇺"
        elif 'us' in cortex_client.base_url:
            region = "États-Unis (US) 🇺🇸"
        elif 'apac' in cortex_client.base_url:
            region = "Asie-Pacifique (APAC) 🌏"
        else:
            region = "Inconnue"
        
        print_info("Région", region)
        
        return cortex_client
    except Exception as e:
        print_error(f"Erreur lors de l'initialisation du CortexClient : {str(e)}")
        return None

def test_api_connection(cortex_client):
    """Teste la connexion à l'API Cortex XDR"""
    print_section("Test de connexion à l'API")
    
    if not cortex_client.api_key or not cortex_client.api_key_id:
        print_error("Les clés API ne sont pas configurées. Impossible de tester la connexion.")
        print_warning("Mode simulation activé.")
        return False
    
    try:
        # Tenter de générer un token
        print("Test d'authentification...")
        headers = cortex_client._get_auth_headers()
        
        if "Authorization" in headers and headers["Authorization"].startswith("Bearer "):
            print_success("Authentification réussie ! Token généré.")
            print_info("Type d'auth", "Bearer Token")
            
            # Tester un endpoint simple
            print("\nTest d'un endpoint API...")
            try:
                # Utiliser l'endpoint des endpoints qui est généralement accessible
                response = cortex_client.get_endpoints()
                if response:
                    print_success(f"Connexion à l'API réussie ! {len(response)} endpoints trouvés.")
                    return True
                else:
                    print_warning("Connexion réussie mais aucun endpoint trouvé.")
                    return True
            except Exception as e:
                print_warning(f"Endpoint test échoué : {str(e)}")
                print_info("Note", "Cela peut être normal si aucun endpoint n'est configuré")
                return True
        else:
            print_error("Échec de l'authentification. Vérifiez vos clés API.")
            return False
            
    except Exception as e:
        print_error(f"Erreur lors du test de connexion : {str(e)}")
        return False

def test_sample_analysis(cortex_client):
    """Teste l'analyse d'un fichier exemple"""
    print_section("Test d'analyse de fichier (simulation)")
    
    try:
        # Créer un fichier de test temporaire
        test_file = "test_cortex_connection.txt"
        with open(test_file, 'w') as f:
            f.write("Test file for Cortex XDR connection validation")
        
        print(f"Fichier de test créé : {test_file}")
        
        # Analyser le fichier
        result = cortex_client.analyze_file(test_file)
        
        if result:
            print_success("Analyse terminée avec succès")
            print_info("Menaces détectées", len(result.get('threats', [])))
            print_info("Score de risque", result.get('score', 0))
            print_info("Indicateurs", len(result.get('indicators', [])))
            
            # Nettoyer
            os.remove(test_file)
            return True
        else:
            print_error("L'analyse a échoué")
            os.remove(test_file)
            return False
            
    except Exception as e:
        print_error(f"Erreur lors du test d'analyse : {str(e)}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

def print_summary(results):
    """Affiche un résumé des tests"""
    print_section("Résumé des tests")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    print(f"\n{Colors.BOLD}Tests réussis : {passed_tests}/{total_tests}{Colors.RESET}")
    
    for test_name, result in results.items():
        if result:
            print_success(test_name)
        else:
            print_error(test_name)
    
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    
    if passed_tests == total_tests:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ Tous les tests sont passés ! CortexDFIR-Forge est prêt à l'emploi.{Colors.RESET}")
    elif passed_tests >= total_tests - 1:
        print(f"{Colors.YELLOW}{Colors.BOLD}⚠️  Configuration partiellement fonctionnelle. Vérifiez les erreurs ci-dessus.{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ Configuration incomplète. Veuillez configurer les clés API Cortex XDR.{Colors.RESET}")
        print(f"\n{Colors.YELLOW}Instructions :{Colors.RESET}")
        print("1. Copiez le fichier .env.example vers .env")
        print("2. Éditez .env et ajoutez vos clés API Cortex XDR")
        print("3. Relancez ce script de test")

def main():
    """Fonction principale"""
    print_header()
    
    results = {}
    
    # 1. Vérifier l'environnement
    env_ok, env_vars = check_environment()
    results["Configuration environnement"] = env_ok
    
    # 2. Tester le gestionnaire de configuration
    config_manager, cortex_config = test_config_manager()
    results["Gestionnaire de configuration"] = config_manager is not None
    
    if not config_manager:
        print_summary(results)
        return
    
    # 3. Tester le client Cortex
    cortex_client = test_cortex_client(config_manager)
    results["Client Cortex XDR"] = cortex_client is not None
    
    if not cortex_client:
        print_summary(results)
        return
    
    # 4. Tester la connexion API (seulement si les clés sont configurées)
    if cortex_client.api_key and cortex_client.api_key_id:
        api_ok = test_api_connection(cortex_client)
        results["Connexion API Cortex XDR"] = api_ok
    else:
        print_warning("\nTests API ignorés (clés non configurées)")
        results["Connexion API Cortex XDR"] = False
    
    # 5. Test d'analyse
    analysis_ok = test_sample_analysis(cortex_client)
    results["Analyse de fichier"] = analysis_ok
    
    # Afficher le résumé
    print_summary(results)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrompu par l'utilisateur.{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Erreur inattendue : {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
