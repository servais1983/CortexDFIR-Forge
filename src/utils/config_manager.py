import os
import logging
import yaml
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Gestionnaire de configuration pour CortexDFIR-Forge
    """
    
    def __init__(self):
        """
        Initialisation du gestionnaire de configuration
        """
        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
        self.config_file = os.path.join(self.config_dir, "config.yaml")
        self.config = {}
        
        # Création du répertoire de configuration s'il n'existe pas
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, exist_ok=True)
        
        # Chargement de la configuration
        self._load_config()
        
        logger.info("ConfigManager initialisé")
    
    def _load_config(self) -> None:
        """
        Charge la configuration depuis le fichier YAML
        """
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.config = yaml.safe_load(f)
                    
                logger.info(f"Configuration chargée depuis {self.config_file}")
            else:
                logger.warning(f"Fichier de configuration {self.config_file} non trouvé, utilisation des valeurs par défaut")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Erreur lors du chargement de la configuration: {str(e)}", exc_info=True)
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """
        Crée une configuration par défaut
        """
        try:
            self.config = {
                "cortex": {
                    "api_key": "",
                    "api_key_id": "",
                    "tenant_id": "",
                    "base_url": "https://api.xdr.paloaltonetworks.com"
                },
                "analysis": {
                    "default_types": ["malware", "ransomware", "phishing", "persistence"],
                    "max_file_size": 100 * 1024 * 1024  # 100 MB
                },
                "reporting": {
                    "company_name": "Votre Entreprise",
                    "logo_path": "",
                    "default_output_dir": os.path.join(os.path.expanduser("~"), "Documents", "CortexDFIR-Reports")
                }
            }
            
            # Création du répertoire de configuration s'il n'existe pas
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            
            # Écriture de la configuration par défaut
            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            logger.info(f"Configuration par défaut créée dans {self.config_file}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la configuration par défaut: {str(e)}", exc_info=True)
            # Configuration minimale en mémoire
            self.config = {
                "cortex": {
                    "api_key": "",
                    "api_key_id": "",
                    "tenant_id": "",
                    "base_url": "https://api.xdr.paloaltonetworks.com"
                }
            }
    
    def save_config(self) -> bool:
        """
        Sauvegarde la configuration dans le fichier YAML
        
        Returns:
            True si la sauvegarde a réussi, False sinon
        """
        try:
            with open(self.config_file, "w") as f:
                yaml.dump(self.config, f, default_flow_style=False)
            
            logger.info(f"Configuration sauvegardée dans {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {str(e)}", exc_info=True)
            return False
    
    def get_cortex_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration Cortex XDR
        
        Returns:
            Dictionnaire de configuration Cortex XDR
        """
        return self.config.get("cortex", {})
    
    def set_cortex_config(self, api_key: str, api_key_id: str, tenant_id: str, base_url: str = None) -> bool:
        """
        Définit la configuration Cortex XDR
        
        Args:
            api_key: Clé API Cortex XDR
            api_key_id: ID de la clé API Cortex XDR
            tenant_id: ID du tenant Cortex XDR
            base_url: URL de base de l'API Cortex XDR (optionnel)
        
        Returns:
            True si la configuration a été mise à jour, False sinon
        """
        try:
            if "cortex" not in self.config:
                self.config["cortex"] = {}
            
            self.config["cortex"]["api_key"] = api_key
            self.config["cortex"]["api_key_id"] = api_key_id
            self.config["cortex"]["tenant_id"] = tenant_id
            
            if base_url:
                self.config["cortex"]["base_url"] = base_url
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration Cortex XDR: {str(e)}", exc_info=True)
            return False
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration d'analyse
        
        Returns:
            Dictionnaire de configuration d'analyse
        """
        return self.config.get("analysis", {})
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration de reporting
        
        Returns:
            Dictionnaire de configuration de reporting
        """
        return self.config.get("reporting", {})
    
    def set_reporting_config(self, company_name: str, logo_path: str = None, default_output_dir: str = None) -> bool:
        """
        Définit la configuration de reporting
        
        Args:
            company_name: Nom de l'entreprise
            logo_path: Chemin vers le logo de l'entreprise (optionnel)
            default_output_dir: Répertoire de sortie par défaut pour les rapports (optionnel)
        
        Returns:
            True si la configuration a été mise à jour, False sinon
        """
        try:
            if "reporting" not in self.config:
                self.config["reporting"] = {}
            
            self.config["reporting"]["company_name"] = company_name
            
            if logo_path:
                self.config["reporting"]["logo_path"] = logo_path
            
            if default_output_dir:
                self.config["reporting"]["default_output_dir"] = default_output_dir
            
            return self.save_config()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration de reporting: {str(e)}", exc_info=True)
            return False
