import os
import logging
import yaml
from typing import Dict, Any, Optional
from utils.secrets_manager import SecretsManager

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
        self.env_file = os.path.join(self.config_dir, ".env")
        self.config = {}
        
        # Initialisation du gestionnaire de secrets
        self.secrets_manager = SecretsManager(self.env_file)
        
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
                    self.config = yaml.safe_load(f) or {}
                    
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
                    "use_env_secrets": True,
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
                    "use_env_secrets": True,
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
            # Assurez-vous que les secrets ne sont pas stockés dans le fichier de configuration
            if "cortex" in self.config:
                cortex_config = self.config["cortex"].copy()
                # Suppression des secrets potentiels du dictionnaire de configuration
                for key in ["api_key", "api_key_id", "tenant_id"]:
                    if key in cortex_config:
                        del cortex_config[key]
                # Assurez-vous que use_env_secrets est défini à True
                cortex_config["use_env_secrets"] = True
                self.config["cortex"] = cortex_config
            
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
        cortex_config = self.config.get("cortex", {}).copy()
        
        # Si use_env_secrets est activé, récupérer les secrets depuis les variables d'environnement
        if cortex_config.get("use_env_secrets", False):
            credentials = self.secrets_manager.get_cortex_credentials()
            cortex_config.update(credentials)
        
        return cortex_config
    
    def set_cortex_config(self, api_key: Optional[str] = None, api_key_id: Optional[str] = None, 
                         tenant_id: Optional[str] = None, base_url: Optional[str] = None) -> bool:
        """
        Définit la configuration Cortex XDR
        
        Args:
            api_key: Clé API Cortex XDR (optionnel)
            api_key_id: ID de la clé API Cortex XDR (optionnel)
            tenant_id: ID du tenant Cortex XDR (optionnel)
            base_url: URL de base de l'API Cortex XDR (optionnel)
        
        Returns:
            True si la configuration a été mise à jour, False sinon
        """
        try:
            if "cortex" not in self.config:
                self.config["cortex"] = {}
            
            # Mise à jour de l'URL de base dans le fichier de configuration
            if base_url:
                self.config["cortex"]["base_url"] = base_url
            
            # Stockage des secrets dans le fichier .env si fournis
            secrets_updated = False
            if api_key or api_key_id or tenant_id:
                # Lecture du fichier .env existant
                env_content = ""
                if os.path.exists(self.env_file):
                    with open(self.env_file, "r") as f:
                        env_content = f.read()
                
                # Mise à jour des variables d'environnement
                env_lines = env_content.split("\n")
                updated_lines = []
                
                # Variables à mettre à jour
                env_vars = {
                    "CORTEX_API_KEY": api_key,
                    "CORTEX_API_KEY_ID": api_key_id,
                    "CORTEX_TENANT_ID": tenant_id,
                    "CORTEX_BASE_URL": base_url
                }
                
                # Filtrer les variables non fournies
                env_vars = {k: v for k, v in env_vars.items() if v is not None}
                
                # Mise à jour des lignes existantes
                for line in env_lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        updated_lines.append(line)
                        continue
                    
                    var_name = line.split("=")[0] if "=" in line else ""
                    if var_name in env_vars:
                        updated_lines.append(f"{var_name}={env_vars[var_name]}")
                        del env_vars[var_name]
                    else:
                        updated_lines.append(line)
                
                # Ajout des nouvelles variables
                for var_name, value in env_vars.items():
                    updated_lines.append(f"{var_name}={value}")
                
                # Écriture du fichier .env mis à jour
                with open(self.env_file, "w") as f:
                    f.write("\n".join(updated_lines))
                
                secrets_updated = True
            
            # Sauvegarde de la configuration
            config_updated = self.save_config()
            
            return config_updated or secrets_updated
            
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
