import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Ajout du répertoire parent au chemin de recherche
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.secrets_manager import SecretsManager
from src.utils.input_validator import InputValidator
from src.utils.secure_logger import SecureLogger
from src.utils.network_security import SecureRequestManager

class TestSecurityCorrections(unittest.TestCase):
    """Tests unitaires pour les corrections de sécurité"""
    
    def setUp(self):
        """Initialisation avant chaque test"""
        # Création d'un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        
        # Création d'un fichier .env de test
        self.env_path = os.path.join(self.test_dir, '.env')
        with open(self.env_path, 'w') as f:
            f.write("CORTEX_API_KEY=test_api_key\n")
            f.write("CORTEX_API_KEY_ID=test_api_key_id\n")
            f.write("CORTEX_TENANT_ID=test_tenant_id\n")
            f.write("ENCRYPTION_KEY=test_encryption_key_for_secure_storage\n")
    
    def tearDown(self):
        """Nettoyage après chaque test"""
        # Suppression du répertoire temporaire
        shutil.rmtree(self.test_dir)
    
    def test_secrets_manager_load_env(self):
        """Test du chargement des variables d'environnement"""
        secrets_manager = SecretsManager(self.env_path)
        
        # Vérification que les secrets sont correctement chargés
        self.assertEqual(secrets_manager.get_secret('CORTEX_API_KEY'), 'test_api_key')
        self.assertEqual(secrets_manager.get_secret('CORTEX_API_KEY_ID'), 'test_api_key_id')
        self.assertEqual(secrets_manager.get_secret('CORTEX_TENANT_ID'), 'test_tenant_id')
    
    def test_secrets_manager_encryption(self):
        """Test du chiffrement et déchiffrement des données"""
        secrets_manager = SecretsManager(self.env_path)
        
        # Test du chiffrement
        test_data = "données sensibles à chiffrer"
        encrypted = secrets_manager.encrypt_data(test_data)
        
        # Vérification que les données sont chiffrées
        self.assertIsNotNone(encrypted)
        self.assertNotEqual(encrypted, test_data)
        
        # Test du déchiffrement
        decrypted = secrets_manager.decrypt_data(encrypted)
        
        # Vérification que les données sont correctement déchiffrées
        self.assertEqual(decrypted, test_data)
    
    def test_secrets_manager_token_storage(self):
        """Test du stockage sécurisé des tokens"""
        secrets_manager = SecretsManager(self.env_path)
        
        # Test du stockage de token
        test_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test_token"
        test_expiry = "2025-05-26T20:00:00"
        
        token_data = secrets_manager.store_token(test_token, test_expiry)
        
        # Vérification que le token est stocké de manière chiffrée
        self.assertIsNotNone(token_data)
        self.assertIn('token', token_data)
        self.assertIn('expiry', token_data)
        self.assertIn('encrypted', token_data)
        self.assertTrue(token_data['encrypted'])
        
        # Test de la récupération du token
        retrieved_token = secrets_manager.retrieve_token(token_data)
        
        # Vérification que le token est correctement récupéré
        self.assertEqual(retrieved_token, test_token)
    
    def test_input_validator_file_path(self):
        """Test de la validation des chemins de fichiers"""
        validator = InputValidator()
        
        # Création d'un fichier de test
        test_file = os.path.join(self.test_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write("Contenu de test")
        
        # Test de validation d'un chemin valide
        is_valid, _ = validator.validate_file_path(test_file)
        self.assertTrue(is_valid)
        
        # Test de validation d'un chemin invalide
        is_valid, _ = validator.validate_file_path(os.path.join(self.test_dir, 'fichier_inexistant.txt'))
        self.assertFalse(is_valid)
        
        # Test de validation d'un chemin potentiellement dangereux
        dangerous_path = os.path.join(self.test_dir, '..', 'etc', 'passwd')
        is_valid, _ = validator.validate_file_path(dangerous_path)
        self.assertFalse(is_valid)
    
    def test_input_validator_file_type(self):
        """Test de la validation des types de fichiers"""
        validator = InputValidator()
        
        # Création de fichiers de test avec différentes extensions
        test_files = {
            'executable': os.path.join(self.test_dir, 'test.exe'),
            'document': os.path.join(self.test_dir, 'test.pdf'),
            'log': os.path.join(self.test_dir, 'test.log'),
            'unknown': os.path.join(self.test_dir, 'test.xyz')
        }
        
        for file_path in test_files.values():
            with open(file_path, 'w') as f:
                f.write("Contenu de test")
        
        # Test de validation avec catégories spécifiques
        is_valid, _ = validator.validate_file_type(test_files['executable'], ['executable'])
        self.assertTrue(is_valid)
        
        is_valid, _ = validator.validate_file_type(test_files['document'], ['executable'])
        self.assertFalse(is_valid)
        
        # Test de validation avec plusieurs catégories
        is_valid, _ = validator.validate_file_type(test_files['log'], ['document', 'log'])
        self.assertTrue(is_valid)
        
        # Test de validation d'un type inconnu
        is_valid, _ = validator.validate_file_type(test_files['unknown'])
        self.assertFalse(is_valid)
    
    def test_secure_logger_filtering(self):
        """Test du filtrage des informations sensibles dans les logs"""
        # Création d'un fichier de log de test
        log_file = os.path.join(self.test_dir, 'test.log')
        
        # Configuration du logger de test
        logger = SecureLogger('test_logger')
        
        # Ajout d'un handler de fichier pour les tests
        import logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(message)s')  # Format simplifié pour les tests
        file_handler.setFormatter(formatter)
        logger.logger.addHandler(file_handler)
        
        # Test de journalisation avec des informations sensibles
        sensitive_message = "api_key=secret_value&password=123456"
        logger.info(sensitive_message)
        
        # Vérification que les informations sensibles sont filtrées
        with open(log_file, 'r') as f:
            log_content = f.read()
            self.assertNotIn('secret_value', log_content)
            self.assertNotIn('123456', log_content)
            self.assertIn('***REDACTED***', log_content)
    
    @patch('requests.Session')
    def test_secure_request_manager(self, mock_session):
        """Test du gestionnaire de requêtes sécurisées"""
        # Configuration du mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.return_value.request.return_value = mock_response
        
        # Création du gestionnaire de requêtes
        request_manager = SecureRequestManager()
        
        # Test d'une requête GET
        response = request_manager.get('https://example.com/api')
        
        # Vérification que la requête a été effectuée avec les paramètres de sécurité
        mock_session.return_value.request.assert_called_once()
        call_args = mock_session.return_value.request.call_args[1]
        
        self.assertEqual(call_args['method'], 'GET')
        self.assertEqual(call_args['url'], 'https://example.com/api')
        self.assertTrue(call_args['verify'])  # Vérification SSL activée
        self.assertIsNotNone(call_args['timeout'])  # Timeout défini

if __name__ == '__main__':
    unittest.main()
