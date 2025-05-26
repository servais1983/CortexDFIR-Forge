import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration du format de journalisation
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Niveaux de journalisation personnalisés
SECURITY_LEVEL = 25  # Entre INFO (20) et WARNING (30)
AUDIT_LEVEL = 15     # Entre DEBUG (10) et INFO (20)

class SecureLogger:
    """
    Gestionnaire de journalisation sécurisé pour CortexDFIR-Forge
    
    Cette classe fournit des méthodes pour journaliser les événements de manière sécurisée,
    en filtrant les informations sensibles et en offrant des niveaux de journalisation
    spécifiques pour les événements de sécurité.
    """
    
    def __init__(self, name: str, log_dir: str = None, log_level: int = logging.INFO):
        """
        Initialisation du gestionnaire de journalisation
        
        Args:
            name: Nom du logger
            log_dir: Répertoire des fichiers de log (optionnel)
            log_level: Niveau de journalisation (optionnel)
        """
        # Ajout des niveaux de journalisation personnalisés
        logging.addLevelName(SECURITY_LEVEL, "SECURITY")
        logging.addLevelName(AUDIT_LEVEL, "AUDIT")
        
        # Création du logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        
        # Définition du répertoire de logs
        if log_dir:
            self.log_dir = log_dir
        else:
            self.log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
        
        # Création du répertoire de logs s'il n'existe pas
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Création des gestionnaires de journalisation
        self._setup_handlers()
        
        # Liste des mots-clés sensibles à filtrer
        self.sensitive_keywords = [
            "api_key", "apikey", "api-key", "password", "secret", "token", "auth", 
            "credential", "private", "key", "cert", "certificate"
        ]
    
    def _setup_handlers(self):
        """Configure les gestionnaires de journalisation"""
        # Vérification si des handlers sont déjà configurés
        if self.logger.handlers:
            return
        
        # Handler pour la console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # Handler pour le fichier de log général
        log_file = os.path.join(self.log_dir, "cortexdfir.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        
        # Handler pour les événements de sécurité
        security_log_file = os.path.join(self.log_dir, "security.log")
        security_handler = logging.FileHandler(security_log_file)
        security_handler.setLevel(SECURITY_LEVEL)
        security_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        security_handler.setFormatter(security_formatter)
        
        # Handler pour les événements d'audit
        audit_log_file = os.path.join(self.log_dir, "audit.log")
        audit_handler = logging.FileHandler(audit_log_file)
        audit_handler.setLevel(AUDIT_LEVEL)
        audit_formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT)
        audit_handler.setFormatter(audit_formatter)
        
        # Ajout des handlers au logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(security_handler)
        self.logger.addHandler(audit_handler)
    
    def _filter_sensitive_data(self, message: str) -> str:
        """
        Filtre les informations sensibles dans un message
        
        Args:
            message: Message à filtrer
        
        Returns:
            Message filtré
        """
        filtered_message = message
        
        # Filtrage des mots-clés sensibles
        for keyword in self.sensitive_keywords:
            # Recherche de motifs comme "api_key=1234" ou "api_key: 1234" ou "api_key":"1234"
            patterns = [
                f"{keyword}=([^&\s]+)",
                f"{keyword}:\s*([^,\s]+)",
                f'"{keyword}":\s*"([^"]+)"',
                f"'{keyword}':\s*'([^']+)'",
            ]
            
            for pattern in patterns:
                import re
                filtered_message = re.sub(
                    pattern, 
                    f"{keyword}=***REDACTED***", 
                    filtered_message, 
                    flags=re.IGNORECASE
                )
        
        return filtered_message
    
    def debug(self, message: str, *args, **kwargs):
        """Journalise un message de niveau DEBUG"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.debug(filtered_message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Journalise un message de niveau INFO"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.info(filtered_message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Journalise un message de niveau WARNING"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.warning(filtered_message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Journalise un message de niveau ERROR"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.error(filtered_message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Journalise un message de niveau CRITICAL"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.critical(filtered_message, *args, **kwargs)
    
    def security(self, message: str, *args, **kwargs):
        """Journalise un message de niveau SECURITY"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.log(SECURITY_LEVEL, filtered_message, *args, **kwargs)
    
    def audit(self, message: str, *args, **kwargs):
        """Journalise un message de niveau AUDIT"""
        filtered_message = self._filter_sensitive_data(message)
        self.logger.log(AUDIT_LEVEL, filtered_message, *args, **kwargs)
    
    def log_exception(self, message: str, exc_info: bool = True, stack_info: bool = False):
        """
        Journalise une exception avec des informations détaillées
        
        Args:
            message: Message décrivant l'exception
            exc_info: Inclure les informations d'exception
            stack_info: Inclure les informations de pile
        """
        filtered_message = self._filter_sensitive_data(message)
        self.logger.error(filtered_message, exc_info=exc_info, stack_info=stack_info)
    
    def log_security_event(self, event_type: str, details: Dict[str, Any], success: bool = True):
        """
        Journalise un événement de sécurité
        
        Args:
            event_type: Type d'événement (authentication, authorization, etc.)
            details: Détails de l'événement
            success: Indique si l'événement a réussi
        """
        # Filtrage des informations sensibles dans les détails
        filtered_details = {}
        for key, value in details.items():
            if isinstance(value, str):
                for keyword in self.sensitive_keywords:
                    if keyword.lower() in key.lower():
                        filtered_details[key] = "***REDACTED***"
                        break
                else:
                    filtered_details[key] = value
            else:
                filtered_details[key] = value
        
        # Création du message d'événement
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "success": success,
            "details": filtered_details
        }
        
        # Journalisation de l'événement
        message = f"Événement de sécurité: {event_type} - {'Succès' if success else 'Échec'}"
        self.security(f"{message} - {json.dumps(event_data)}")
    
    def log_audit_event(self, action: str, resource: str, user: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Journalise un événement d'audit
        
        Args:
            action: Action effectuée (create, read, update, delete)
            resource: Ressource concernée
            user: Utilisateur ayant effectué l'action (optionnel)
            details: Détails supplémentaires (optionnel)
        """
        # Filtrage des informations sensibles dans les détails
        filtered_details = {}
        if details:
            for key, value in details.items():
                if isinstance(value, str):
                    for keyword in self.sensitive_keywords:
                        if keyword.lower() in key.lower():
                            filtered_details[key] = "***REDACTED***"
                            break
                    else:
                        filtered_details[key] = value
                else:
                    filtered_details[key] = value
        
        # Création du message d'audit
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "resource": resource,
            "user": user,
            "details": filtered_details
        }
        
        # Journalisation de l'événement d'audit
        message = f"Audit: {action} sur {resource}"
        if user:
            message += f" par {user}"
        self.audit(f"{message} - {json.dumps(audit_data)}")
