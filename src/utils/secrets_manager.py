import os
import logging
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Gestionnaire de secrets sécurisé pour CortexDFIR-Forge
    
    Cette classe fournit des méthodes pour charger des secrets depuis des variables
    d'environnement et pour chiffrer/déchiffrer des données sensibles.
    """
    
    def __init__(self, env_path: Optional[str] = None):
        """
        Initialisation du gestionnaire de secrets
        
        Args:
            env_path: Chemin optionnel vers le fichier .env
        """
        # Chargement des variables d'environnement
        if env_path and os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            # Recherche du fichier .env dans les emplacements standards
            default_paths = [
                os.path.join(os.getcwd(), '.env'),
                os.path.join(os.getcwd(), 'config', '.env')
            ]
            for path in default_paths:
                if os.path.exists(path):
                    load_dotenv(path)
                    break
        
        # Initialisation du chiffreur si une clé est disponible
        self.encryption_key = os.environ.get('ENCRYPTION_KEY')
        self.cipher_suite = None
        
        if self.encryption_key:
            try:
                # Dérivation d'une clé de chiffrement à partir de la clé fournie
                salt = b'CortexDFIR-Forge'  # Salt fixe pour la dérivation de clé
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                )
                key = base64.urlsafe_b64encode(kdf.derive(self.encryption_key.encode()))
                self.cipher_suite = Fernet(key)
                logger.info("Chiffrement initialisé avec succès")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du chiffrement: {str(e)}", exc_info=True)
                self.cipher_suite = None
    
    def get_secret(self, secret_name: str, default: Any = None) -> Any:
        """
        Récupère un secret depuis les variables d'environnement
        
        Args:
            secret_name: Nom du secret à récupérer
            default: Valeur par défaut si le secret n'est pas trouvé
        
        Returns:
            La valeur du secret ou la valeur par défaut
        """
        return os.environ.get(secret_name, default)
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """
        Chiffre des données sensibles
        
        Args:
            data: Données à chiffrer
        
        Returns:
            Données chiffrées en base64 ou None en cas d'erreur
        """
        if not self.cipher_suite:
            logger.warning("Tentative de chiffrement sans clé de chiffrement configurée")
            return None
        
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Erreur lors du chiffrement: {str(e)}", exc_info=True)
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """
        Déchiffre des données sensibles
        
        Args:
            encrypted_data: Données chiffrées en base64
        
        Returns:
            Données déchiffrées ou None en cas d'erreur
        """
        if not self.cipher_suite:
            logger.warning("Tentative de déchiffrement sans clé de chiffrement configurée")
            return None
        
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data)
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Erreur lors du déchiffrement: {str(e)}", exc_info=True)
            return None
    
    def get_cortex_credentials(self) -> Dict[str, str]:
        """
        Récupère les informations d'identification Cortex XDR
        
        Returns:
            Dictionnaire contenant les informations d'identification
        """
        return {
            "api_key": self.get_secret("CORTEX_API_KEY", ""),
            "api_key_id": self.get_secret("CORTEX_API_KEY_ID", ""),
            "tenant_id": self.get_secret("CORTEX_TENANT_ID", ""),
            "base_url": self.get_secret("CORTEX_BASE_URL", "https://api.xdr.paloaltonetworks.com")
        }
    
    def store_token(self, token: str, expiry: str) -> Dict[str, str]:
        """
        Stocke un token d'authentification de manière sécurisée
        
        Args:
            token: Token à stocker
            expiry: Date d'expiration au format ISO
        
        Returns:
            Dictionnaire contenant le token chiffré et sa date d'expiration
        """
        encrypted_token = self.encrypt_data(token) if self.cipher_suite else token
        
        return {
            "token": encrypted_token,
            "expiry": expiry,
            "encrypted": self.cipher_suite is not None
        }
    
    def retrieve_token(self, token_data: Dict[str, str]) -> Optional[str]:
        """
        Récupère un token d'authentification stocké
        
        Args:
            token_data: Dictionnaire contenant le token et ses métadonnées
        
        Returns:
            Token déchiffré ou None en cas d'erreur
        """
        if not token_data or "token" not in token_data:
            return None
        
        # Vérification si le token est chiffré
        is_encrypted = token_data.get("encrypted", False)
        
        if is_encrypted and self.cipher_suite:
            return self.decrypt_data(token_data["token"])
        else:
            return token_data["token"]
