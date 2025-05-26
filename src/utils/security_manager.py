import os
import logging
import hashlib
import json
from typing import Dict, Any, Optional

class SecurityManager:
    """
    Gestionnaire de sécurité pour CortexDFIR-Forge
    
    Cette classe gère les aspects de sécurité de l'application, notamment :
    - La validation des règles YARA
    - La vérification de l'intégrité des fichiers
    - Le chiffrement des données sensibles
    - La gestion des autorisations
    """
    
    def __init__(self, config_dir: str = None):
        """
        Initialisation du gestionnaire de sécurité
        
        Args:
            config_dir: Répertoire de configuration (optionnel)
        """
        self.logger = logging.getLogger(__name__)
        
        # Répertoire de configuration
        if config_dir is None:
            self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config")
        else:
            self.config_dir = config_dir
            
        # Création du répertoire de configuration s'il n'existe pas
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Fichier d'intégrité
        self.integrity_file = os.path.join(self.config_dir, "integrity.json")
        
        # Chargement des données d'intégrité
        self.integrity_data = self._load_integrity_data()
    
    def _load_integrity_data(self) -> Dict[str, Any]:
        """
        Chargement des données d'intégrité
        
        Returns:
            Dictionnaire des données d'intégrité
        """
        if os.path.exists(self.integrity_file):
            try:
                with open(self.integrity_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erreur lors du chargement des données d'intégrité: {str(e)}")
                return {"files": {}, "rules": {}}
        else:
            return {"files": {}, "rules": {}}
    
    def _save_integrity_data(self):
        """Sauvegarde des données d'intégrité"""
        try:
            with open(self.integrity_file, 'w') as f:
                json.dump(self.integrity_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des données d'intégrité: {str(e)}")
    
    def calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calcul du hash d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Hash SHA-256 du fichier, ou None en cas d'erreur
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Fichier non trouvé: {file_path}")
            return None
        
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul du hash pour {file_path}: {str(e)}")
            return None
    
    def verify_file_integrity(self, file_path: str) -> bool:
        """
        Vérification de l'intégrité d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            True si l'intégrité est vérifiée, False sinon
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Fichier non trouvé: {file_path}")
            return False
        
        # Calcul du hash actuel
        current_hash = self.calculate_file_hash(file_path)
        if current_hash is None:
            return False
        
        # Récupération du hash enregistré
        stored_hash = self.integrity_data["files"].get(file_path)
        
        # Si aucun hash n'est enregistré, on l'enregistre
        if stored_hash is None:
            self.integrity_data["files"][file_path] = current_hash
            self._save_integrity_data()
            return True
        
        # Vérification de l'intégrité
        return current_hash == stored_hash
    
    def update_file_integrity(self, file_path: str) -> bool:
        """
        Mise à jour de l'intégrité d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            True si la mise à jour a réussi, False sinon
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Fichier non trouvé: {file_path}")
            return False
        
        # Calcul du hash
        file_hash = self.calculate_file_hash(file_path)
        if file_hash is None:
            return False
        
        # Mise à jour des données d'intégrité
        self.integrity_data["files"][file_path] = file_hash
        self._save_integrity_data()
        
        return True
    
    def validate_yara_rule(self, rule_path: str) -> Dict[str, Any]:
        """
        Validation d'une règle YARA
        
        Args:
            rule_path: Chemin de la règle YARA
            
        Returns:
            Dictionnaire contenant le résultat de la validation
        """
        import yara
        
        if not os.path.exists(rule_path):
            return {
                "valid": False,
                "error": f"Fichier non trouvé: {rule_path}",
                "metadata": {}
            }
        
        try:
            # Compilation de la règle
            rule = yara.compile(filepath=rule_path)
            
            # Extraction des métadonnées
            metadata = {}
            for rule_meta in rule.metadata:
                for key, value in rule_meta.items():
                    metadata[key] = value
            
            # Vérification des métadonnées requises
            required_metadata = ["description", "author"]
            missing_metadata = [field for field in required_metadata if field not in metadata]
            
            if missing_metadata:
                return {
                    "valid": False,
                    "error": f"Métadonnées manquantes: {', '.join(missing_metadata)}",
                    "metadata": metadata
                }
            
            # Mise à jour des données d'intégrité
            rule_hash = self.calculate_file_hash(rule_path)
            if rule_hash:
                self.integrity_data["rules"][rule_path] = {
                    "hash": rule_hash,
                    "metadata": metadata
                }
                self._save_integrity_data()
            
            return {
                "valid": True,
                "error": None,
                "metadata": metadata
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "metadata": {}
            }
    
    def validate_yara_rules_directory(self, rules_dir: str) -> Dict[str, Any]:
        """
        Validation d'un répertoire de règles YARA
        
        Args:
            rules_dir: Chemin du répertoire de règles
            
        Returns:
            Dictionnaire contenant les résultats de validation
        """
        if not os.path.exists(rules_dir) or not os.path.isdir(rules_dir):
            return {
                "valid": False,
                "error": f"Répertoire non trouvé: {rules_dir}",
                "rules": {}
            }
        
        results = {
            "valid": True,
            "error": None,
            "rules": {}
        }
        
        # Parcours récursif du répertoire
        for root, _, files in os.walk(rules_dir):
            for file in files:
                if file.endswith(('.yar', '.yara')):
                    rule_path = os.path.join(root, file)
                    validation_result = self.validate_yara_rule(rule_path)
                    
                    # Ajout du résultat
                    results["rules"][rule_path] = validation_result
                    
                    # Si une règle est invalide, l'ensemble est invalide
                    if not validation_result["valid"]:
                        results["valid"] = False
        
        return results
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Chiffrement de données sensibles
        
        Args:
            data: Données à chiffrer
            
        Returns:
            Données chiffrées
        """
        from cryptography.fernet import Fernet
        
        # Génération ou récupération de la clé
        key_file = os.path.join(self.config_dir, "encryption.key")
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
        
        # Chiffrement des données
        cipher = Fernet(key)
        encrypted_data = cipher.encrypt(data.encode())
        
        return encrypted_data.decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> Optional[str]:
        """
        Déchiffrement de données sensibles
        
        Args:
            encrypted_data: Données chiffrées
            
        Returns:
            Données déchiffrées, ou None en cas d'erreur
        """
        from cryptography.fernet import Fernet, InvalidToken
        
        # Récupération de la clé
        key_file = os.path.join(self.config_dir, "encryption.key")
        
        if not os.path.exists(key_file):
            self.logger.error("Clé de chiffrement non trouvée")
            return None
        
        try:
            with open(key_file, 'rb') as f:
                key = f.read()
            
            # Déchiffrement des données
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data.encode())
            
            return decrypted_data.decode()
        except InvalidToken:
            self.logger.error("Token invalide lors du déchiffrement")
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors du déchiffrement: {str(e)}")
            return None
    
    def secure_delete_file(self, file_path: str) -> bool:
        """
        Suppression sécurisée d'un fichier
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            True si la suppression a réussi, False sinon
        """
        if not os.path.exists(file_path):
            self.logger.error(f"Fichier non trouvé: {file_path}")
            return False
        
        try:
            # Récupération de la taille du fichier
            file_size = os.path.getsize(file_path)
            
            # Écrasement du fichier avec des données aléatoires
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
            
            # Suppression du fichier
            os.remove(file_path)
            
            # Suppression des données d'intégrité
            if file_path in self.integrity_data["files"]:
                del self.integrity_data["files"][file_path]
                self._save_integrity_data()
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression sécurisée de {file_path}: {str(e)}")
            return False
