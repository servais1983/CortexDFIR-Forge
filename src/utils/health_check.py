#!/usr/bin/env python3
"""
Health Check Script pour CortexDFIR-Forge
Vérifie l'état de santé du système et la configuration
"""

import os
import sys
import json
import psutil
import requests
from datetime import datetime
from pathlib import Path

# Ajouter le chemin src au PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..'))

try:
    from src.utils.config_manager import ConfigManager
    from src.core.cortex_client import CortexClient
except ImportError:
    print("❌ Erreur: Impossible d'importer les modules.")
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
    """Affiche l'en-tête"""
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}🏥 Health Check - CortexDFIR-Forge{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🖥️  Système: {sys.platform}")
    print(f"🐍 Python: {sys.version.split()[0]}\n")

def check_system_resources():
    """Vérifie les ressources système"""
    print(f"\n{Colors.BLUE}▶ Ressources Système{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    # CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_status = "✅" if cpu_percent < 80 else "⚠️" if cpu_percent < 90 else "❌"
    print(f"{cpu_status} CPU: {cpu_percent}%")
    
    # Mémoire
    memory = psutil.virtual_memory()
    mem_percent = memory.percent
    mem_status = "✅" if mem_percent < 80 else "⚠️" if mem_percent < 90 else "❌"
    print(f"{mem_status} Mémoire: {mem_percent}% ({memory.used / 1024**3:.1f} GB / {memory.total / 1024**3:.1f} GB)")
    
    # Disque
    disk = psutil.disk_usage('/')
    disk_percent = disk.percent
    disk_status = "✅" if disk_percent < 80 else "⚠️" if disk_percent < 90 else "❌"
    print(f"{disk_status} Disque: {disk_percent}% ({disk.used / 1024**3:.1f} GB / {disk.total / 1024**3:.1f} GB)")
    
    return cpu_percent < 90 and mem_percent < 90 and disk_percent < 90

def check_directories():
    """Vérifie l'existence des répertoires nécessaires"""
    print(f"\n{Colors.BLUE}▶ Répertoires Requis{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    required_dirs = [
        "data",
        "reports",
        "logs",
        "temp",
        "rules",
        "config"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}/")
        else:
            print(f"❌ {dir_name}/ (manquant)")
            all_exist = False
    
    return all_exist

def check_configuration():
    """Vérifie la configuration"""
    print(f"\n{Colors.BLUE}▶ Configuration{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    # Vérifier .env
    env_exists = os.path.exists('.env')
    if env_exists:
        print("✅ Fichier .env présent")
    else:
        print("❌ Fichier .env manquant")
    
    # Vérifier config.yaml
    config_exists = os.path.exists('config/config.yaml')
    if config_exists:
        print("✅ Fichier config.yaml présent")
    else:
        print("❌ Fichier config.yaml manquant")
    
    # Charger et vérifier la configuration
    if config_exists:
        try:
            config_manager = ConfigManager()
            cortex_config = config_manager.get_cortex_config()
            
            # Vérifier l'URL et déterminer la région
            base_url = cortex_config.get('base_url', '')
            if 'eu' in base_url:
                region = "Europe (EU) 🇪🇺"
            elif 'us' in base_url:
                region = "États-Unis (US) 🇺🇸"
            elif 'apac' in base_url:
                region = "Asie-Pacifique (APAC) 🌏"
            else:
                region = "Non configurée"
            
            print(f"✅ Région Cortex XDR: {region}")
            
            # Vérifier les clés API
            has_api_key = bool(cortex_config.get('api_key'))
            has_api_key_id = bool(cortex_config.get('api_key_id'))
            
            if has_api_key and has_api_key_id:
                print("✅ Clés API configurées")
            else:
                print("⚠️  Clés API non configurées (mode simulation)")
            
            return True
        except Exception as e:
            print(f"❌ Erreur de configuration: {str(e)}")
            return False
    
    return env_exists and config_exists

def check_dependencies():
    """Vérifie les dépendances Python"""
    print(f"\n{Colors.BLUE}▶ Dépendances Python{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    required_packages = [
        "requests",
        "PyQt5",
        "psutil",
        "cryptography",
        "jinja2",
        "pyyaml"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (manquant)")
            missing_packages.append(package)
    
    # Vérifier yara-python séparément
    try:
        import yara
        print("✅ yara-python")
    except ImportError:
        print("⚠️  yara-python (optionnel, recommandé)")
    
    return len(missing_packages) == 0

def check_yara_rules():
    """Vérifie la présence des règles YARA"""
    print(f"\n{Colors.BLUE}▶ Règles YARA{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    rules_dirs = [
        "rules/yara-rules",
        "rules/custom",
        "rules/malware",
        "rules/ransomware"
    ]
    
    total_rules = 0
    for rules_dir in rules_dirs:
        if os.path.exists(rules_dir):
            yar_files = list(Path(rules_dir).rglob("*.yar")) + list(Path(rules_dir).rglob("*.yara"))
            count = len(yar_files)
            total_rules += count
            if count > 0:
                print(f"✅ {rules_dir}: {count} règles")
            else:
                print(f"⚠️  {rules_dir}: aucune règle")
        else:
            print(f"⚠️  {rules_dir}: répertoire manquant")
    
    print(f"\n📊 Total: {total_rules} règles YARA")
    return total_rules > 0

def check_cortex_connection():
    """Teste la connexion à Cortex XDR"""
    print(f"\n{Colors.BLUE}▶ Connexion Cortex XDR{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    try:
        config_manager = ConfigManager()
        cortex_client = CortexClient(config_manager)
        
        # Afficher l'URL configurée
        print(f"📍 URL: {cortex_client.base_url}")
        
        # Si les clés API sont configurées, tester la connexion
        if cortex_client.api_key and cortex_client.api_key_id:
            try:
                headers = cortex_client._get_auth_headers()
                if "Authorization" in headers:
                    print("✅ Authentification réussie")
                    
                    # Tester un endpoint simple
                    endpoints = cortex_client.get_endpoints()
                    if endpoints is not None:
                        print(f"✅ API accessible ({len(endpoints)} endpoints)")
                        return True
                    else:
                        print("⚠️  API accessible mais aucune donnée")
                        return True
                else:
                    print("❌ Échec de l'authentification")
                    return False
            except Exception as e:
                print(f"❌ Erreur de connexion: {str(e)}")
                return False
        else:
            print("⚠️  Mode simulation (pas de clés API)")
            return True
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def check_disk_space():
    """Vérifie l'espace disque pour les analyses"""
    print(f"\n{Colors.BLUE}▶ Espace Disque pour Analyses{Colors.RESET}")
    print(f"{Colors.BLUE}{'─' * 40}{Colors.RESET}")
    
    # Vérifier l'espace dans le répertoire data
    data_path = os.path.abspath("data")
    if not os.path.exists(data_path):
        os.makedirs(data_path, exist_ok=True)
    
    disk = psutil.disk_usage(data_path)
    free_gb = disk.free / 1024**3
    
    if free_gb > 100:
        print(f"✅ Espace libre: {free_gb:.1f} GB (excellent)")
        status = "excellent"
    elif free_gb > 50:
        print(f"✅ Espace libre: {free_gb:.1f} GB (bon)")
        status = "good"
    elif free_gb > 20:
        print(f"⚠️  Espace libre: {free_gb:.1f} GB (limité)")
        status = "limited"
    else:
        print(f"❌ Espace libre: {free_gb:.1f} GB (insuffisant)")
        status = "insufficient"
    
    # Recommandations selon l'espace
    if status == "limited":
        print("   💡 Recommandation: Libérez de l'espace pour les analyses VMDK")
    elif status == "insufficient":
        print("   💡 Recommandation: Au moins 20 GB requis pour fonctionner correctement")
    
    return free_gb > 20

def generate_health_report():
    """Génère un rapport de santé"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "configuration": {
            "env_file": os.path.exists('.env'),
            "config_file": os.path.exists('config/config.yaml')
        },
        "status": "healthy"
    }
    
    # Sauvegarder le rapport
    report_path = f"logs/health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report_path

def main():
    """Fonction principale"""
    print_header()
    
    # Exécuter tous les checks
    checks = {
        "Ressources système": check_system_resources(),
        "Répertoires": check_directories(),
        "Configuration": check_configuration(),
        "Dépendances": check_dependencies(),
        "Règles YARA": check_yara_rules(),
        "Connexion Cortex": check_cortex_connection(),
        "Espace disque": check_disk_space()
    }
    
    # Résumé
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 Résumé du Health Check{Colors.RESET}")
    print(f"{Colors.BOLD}{'=' * 60}{Colors.RESET}\n")
    
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)
    
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    print(f"\n{Colors.BOLD}Score: {passed}/{total}{Colors.RESET}")
    
    # État global
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ Système en parfaite santé !{Colors.RESET}")
        status = "HEALTHY"
    elif passed >= total - 2:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  Système fonctionnel avec des avertissements{Colors.RESET}")
        status = "WARNING"
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Système nécessite une intervention{Colors.RESET}")
        status = "CRITICAL"
    
    # Générer le rapport
    try:
        report_path = generate_health_report()
        print(f"\n📄 Rapport sauvegardé: {report_path}")
    except:
        pass
    
    # Code de sortie selon l'état
    if status == "HEALTHY":
        sys.exit(0)
    elif status == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Health check interrompu.{Colors.RESET}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Erreur inattendue : {str(e)}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
