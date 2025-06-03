import requests
import ssl
import logging
import urllib3
from typing import Dict, Any, Optional, Union, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SecureHTTPAdapter(HTTPAdapter):
    """
    Adaptateur HTTP sécurisé pour les requêtes
    
    Cette classe étend HTTPAdapter pour forcer l'utilisation de TLS 1.2+
    et des suites de chiffrement sécurisées.
    """
    
    def init_poolmanager(self, *args, **kwargs):
        """Initialise le gestionnaire de pool avec des paramètres SSL sécurisés"""
        context = ssl.create_default_context()
        # Force TLS 1.2 ou supérieur en utilisant la méthode recommandée
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.maximum_version = ssl.TLSVersion.TLSv1_3
        
        # Utilise uniquement des suites de chiffrement sécurisées
        context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20')
        
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

class SecureRequestManager:
    """
    Gestionnaire de requêtes HTTP sécurisées
    
    Cette classe fournit des méthodes pour effectuer des requêtes HTTP
    de manière sécurisée, avec vérification SSL, timeouts, et gestion des erreurs.
    """
    
    def __init__(self, logger=None):
        """
        Initialisation du gestionnaire de requêtes
        
        Args:
            logger: Logger à utiliser (optionnel)
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Configuration des timeouts par défaut (connexion, lecture)
        self.default_timeout = (5, 30)
        
        # Configuration de la stratégie de retry
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        # Création de la session sécurisée
        self.session = self._create_secure_session()
    
    def _create_secure_session(self) -> requests.Session:
        """
        Crée une session HTTP sécurisée
        
        Returns:
            Session HTTP sécurisée
        """
        session = requests.Session()
        
        # Montage de l'adaptateur sécurisé
        adapter = SecureHTTPAdapter(max_retries=self.retry_strategy)
        session.mount("https://", adapter)
        
        # Désactivation des avertissements de vérification SSL
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        return session
    
    def request(
        self, 
        method: str, 
        url: str, 
        headers: Optional[Dict[str, str]] = None, 
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        timeout: Optional[Union[float, Tuple[float, float]]] = None,
        verify: bool = True
    ) -> requests.Response:
        """
        Effectue une requête HTTP sécurisée
        
        Args:
            method: Méthode HTTP (GET, POST, etc.)
            url: URL de la requête
            headers: En-têtes HTTP (optionnel)
            params: Paramètres de requête (optionnel)
            data: Données de formulaire (optionnel)
            json: Données JSON (optionnel)
            files: Fichiers à envoyer (optionnel)
            timeout: Timeout personnalisé (optionnel)
            verify: Vérification SSL (optionnel, True par défaut)
        
        Returns:
            Réponse HTTP
        
        Raises:
            requests.exceptions.RequestException: Si la requête échoue
        """
        # Utilisation du timeout par défaut si non spécifié
        if timeout is None:
            timeout = self.default_timeout
        
        try:
            self.logger.debug(f"Requête {method} vers {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                files=files,
                timeout=timeout,
                verify=verify
            )
            
            # Vérification du code de statut
            response.raise_for_status()
            
            return response
            
        except requests.exceptions.SSLError as e:
            self.logger.error(f"Erreur SSL lors de la requête vers {url}: {type(e).__name__}")
            raise
            
        except requests.exceptions.ConnectionError as e:
            self.logger.error(f"Erreur de connexion lors de la requête vers {url}: {type(e).__name__}")
            raise
            
        except requests.exceptions.Timeout as e:
            self.logger.error(f"Timeout lors de la requête vers {url}: {type(e).__name__}")
            raise
            
        except requests.exceptions.HTTPError as e:
            self.logger.error(f"Erreur HTTP {e.response.status_code} lors de la requête vers {url}")
            raise
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erreur lors de la requête vers {url}: {type(e).__name__}")
            raise
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """
        Effectue une requête GET sécurisée
        
        Args:
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour la méthode request
        
        Returns:
            Réponse HTTP
        """
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        """
        Effectue une requête POST sécurisée
        
        Args:
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour la méthode request
        
        Returns:
            Réponse HTTP
        """
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> requests.Response:
        """
        Effectue une requête PUT sécurisée
        
        Args:
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour la méthode request
        
        Returns:
            Réponse HTTP
        """
        return self.request("PUT", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> requests.Response:
        """
        Effectue une requête DELETE sécurisée
        
        Args:
            url: URL de la requête
            **kwargs: Arguments supplémentaires pour la méthode request
        
        Returns:
            Réponse HTTP
        """
        return self.request("DELETE", url, **kwargs)
