import os
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class InputValidator:
    """
    Validateur d'entrées pour CortexDFIR-Forge
    
    Cette classe fournit des méthodes pour valider les entrées utilisateur,
    notamment les chemins de fichiers et les types de fichiers.
    """
    
    # Extensions de fichiers autorisées par catégorie
    ALLOWED_EXTENSIONS = {
        "disk_image": [".vmdk", ".vhd", ".vhdx", ".img", ".dd", ".raw", ".bin"],
        "log": [".log", ".evt", ".evtx", ".etl"],
        "document": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".rtf"],
        "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
        "executable": [".exe", ".dll", ".sys", ".bat", ".ps1", ".vbs", ".js"],
        "memory_dump": [".dmp", ".mem", ".raw"],
        "data": [".csv", ".json", ".xml", ".yaml", ".yml"]
    }
    
    # Taille maximale de fichier par défaut (100 MB)
    DEFAULT_MAX_FILE_SIZE = 100 * 1024 * 1024
    
    # Motifs de chemins potentiellement dangereux
    DANGEROUS_PATH_PATTERNS = [
        r"\.\.\/",  # Traversée de répertoire (../)
        r"\.\.\\",  # Traversée de répertoire (..\)
        r"\/etc\/",  # Accès à /etc/
        r"\/bin\/",  # Accès à /bin/
        r"C:\\Windows\\",  # Accès à C:\Windows\
        r"C:\\Program Files",  # Accès à C:\Program Files
        r"\/dev\/",  # Accès à /dev/
        r"\/proc\/",  # Accès à /proc/
        r"\/sys\/",  # Accès à /sys/
    ]
    
    def __init__(self, config_manager=None):
        """
        Initialisation du validateur d'entrées
        
        Args:
            config_manager: Gestionnaire de configuration optionnel
        """
        self.config_manager = config_manager
        self.max_file_size = self.DEFAULT_MAX_FILE_SIZE
        
        # Chargement de la configuration si disponible
        if self.config_manager:
            analysis_config = self.config_manager.get_analysis_config()
            self.max_file_size = analysis_config.get("max_file_size", self.DEFAULT_MAX_FILE_SIZE)
    
    def validate_file_path(self, file_path: str) -> Tuple[bool, str]:
        """
        Valide un chemin de fichier
        
        Args:
            file_path: Chemin du fichier à valider
        
        Returns:
            Tuple (est_valide, message_erreur)
        """
        # Vérification de l'existence du fichier
        if not os.path.exists(file_path):
            return False, f"Le fichier {file_path} n'existe pas"
        
        # Vérification que le chemin pointe vers un fichier et non un répertoire
        if not os.path.isfile(file_path):
            return False, f"{file_path} n'est pas un fichier"
        
        # Vérification des motifs de chemins dangereux
        for pattern in self.DANGEROUS_PATH_PATTERNS:
            if re.search(pattern, file_path):
                return False, f"Chemin de fichier potentiellement dangereux: {file_path}"
        
        # Vérification de la taille du fichier
        file_size = os.path.getsize(file_path)
        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            return False, f"Taille du fichier ({file_size / (1024 * 1024):.2f} MB) dépasse la limite maximale ({max_size_mb:.2f} MB)"
        
        # Vérification des permissions de lecture
        if not os.access(file_path, os.R_OK):
            return False, f"Permissions insuffisantes pour lire le fichier {file_path}"
        
        return True, ""
    
    def validate_file_type(self, file_path: str, allowed_categories: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Valide le type d'un fichier en fonction de son extension
        
        Args:
            file_path: Chemin du fichier à valider
            allowed_categories: Liste des catégories d'extensions autorisées
        
        Returns:
            Tuple (est_valide, message_erreur)
        """
        # Si aucune catégorie n'est spécifiée, toutes sont autorisées
        if not allowed_categories:
            allowed_categories = list(self.ALLOWED_EXTENSIONS.keys())
        
        # Récupération de l'extension du fichier
        _, extension = os.path.splitext(file_path.lower())
        
        # Vérification que l'extension est autorisée
        allowed_extensions = []
        for category in allowed_categories:
            if category in self.ALLOWED_EXTENSIONS:
                allowed_extensions.extend(self.ALLOWED_EXTENSIONS[category])
        
        if not extension:
            return False, "Le fichier n'a pas d'extension"
        
        if extension not in allowed_extensions:
            return False, f"Extension de fichier non autorisée: {extension}. Extensions autorisées: {', '.join(allowed_extensions)}"
        
        return True, ""
    
    def validate_file(self, file_path: str, allowed_categories: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Valide un fichier (chemin et type)
        
        Args:
            file_path: Chemin du fichier à valider
            allowed_categories: Liste des catégories d'extensions autorisées
        
        Returns:
            Tuple (est_valide, message_erreur)
        """
        # Validation du chemin
        path_valid, path_error = self.validate_file_path(file_path)
        if not path_valid:
            return False, path_error
        
        # Validation du type
        type_valid, type_error = self.validate_file_type(file_path, allowed_categories)
        if not type_valid:
            return False, type_error
        
        return True, ""
    
    def validate_files(self, file_paths: List[str], allowed_categories: Optional[List[str]] = None) -> Dict[str, Tuple[bool, str]]:
        """
        Valide une liste de fichiers
        
        Args:
            file_paths: Liste des chemins de fichiers à valider
            allowed_categories: Liste des catégories d'extensions autorisées
        
        Returns:
            Dictionnaire des résultats de validation par fichier
        """
        results = {}
        
        for file_path in file_paths:
            results[file_path] = self.validate_file(file_path, allowed_categories)
        
        return results
    
    def get_valid_files(self, file_paths: List[str], allowed_categories: Optional[List[str]] = None) -> List[str]:
        """
        Filtre une liste de fichiers pour ne garder que les fichiers valides
        
        Args:
            file_paths: Liste des chemins de fichiers à filtrer
            allowed_categories: Liste des catégories d'extensions autorisées
        
        Returns:
            Liste des chemins de fichiers valides
        """
        valid_files = []
        
        for file_path in file_paths:
            is_valid, _ = self.validate_file(file_path, allowed_categories)
            if is_valid:
                valid_files.append(file_path)
        
        return valid_files
    
    def sanitize_file_path(self, file_path: str) -> str:
        """
        Nettoie un chemin de fichier pour le rendre plus sûr
        
        Args:
            file_path: Chemin du fichier à nettoyer
        
        Returns:
            Chemin de fichier nettoyé
        """
        # Conversion en chemin absolu
        abs_path = os.path.abspath(file_path)
        
        # Normalisation du chemin (résolution des .. et .)
        norm_path = os.path.normpath(abs_path)
        
        return norm_path
