import unittest
import os
import sys
import json
from unittest.mock import MagicMock, patch
from datetime import datetime

# Ajout du chemin parent pour l'importation des modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.cortex_client import CortexClient
from src.utils.config_manager import ConfigManager

class TestCortexClient(unittest.TestCase):
    """Tests unitaires pour le client Cortex XDR"""

    def setUp(self):
        """Configuration initiale pour chaque test"""
        # Mock du gestionnaire de configuration
        self.config_manager = MagicMock()
        self.config_manager.get_cortex_config.return_value = {
            "base_url": "https://api.xdr.paloaltonetworks.com",
            "api_key": "test_api_key",
            "api_key_id": "test_api_key_id",
            "tenant_id": "test_tenant_id",
            "advanced_api": True
        }
        
        # Création du client Cortex avec le mock
        self.cortex_client = CortexClient(self.config_manager)
        
        # Création d'un fichier de test temporaire
        self.test_file_path = os.path.join(os.path.dirname(__file__), 'test_file.txt')
        with open(self.test_file_path, 'w') as f:
            f.write("Test file content for Cortex XDR client testing")

    def tearDown(self):
        """Nettoyage après chaque test"""
        # Suppression du fichier de test
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def test_initialization(self):
        """Test de l'initialisation du client Cortex XDR"""
        self.assertEqual(self.cortex_client.base_url, "https://api.xdr.paloaltonetworks.com")
        self.assertEqual(self.cortex_client.api_key, "test_api_key")
        self.assertEqual(self.cortex_client.api_key_id, "test_api_key_id")
        self.assertEqual(self.cortex_client.tenant_id, "test_tenant_id")
        self.assertTrue(self.cortex_client.advanced_api)

    @patch('requests.post')
    def test_get_auth_headers(self, mock_post):
        """Test de la génération des en-têtes d'authentification"""
        # Configuration du mock pour simuler une réponse de token
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reply": {
                "token": "test_token"
            }
        }
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        headers = self.cortex_client._get_auth_headers()
        
        # Vérification des résultats
        self.assertEqual(headers["Authorization"], "Bearer test_token")
        self.assertEqual(headers["Content-Type"], "application/json")
        
        # Vérification que le token est mis en cache
        self.assertIn("token", self.cortex_client.token_cache)
        self.assertEqual(self.cortex_client.token_cache["token"], "test_token")
        self.assertIn("expiry", self.cortex_client.token_cache)

    @patch('requests.post')
    def test_analyze_file(self, mock_post):
        """Test de l'analyse de fichier"""
        # Configuration des mocks pour simuler l'upload et l'analyse
        upload_response = MagicMock()
        upload_response.status_code = 200
        upload_response.json.return_value = {
            "reply": {
                "upload_id": "test_upload_id"
            }
        }
        
        analysis_response = MagicMock()
        analysis_response.status_code = 200
        analysis_response.json.return_value = {
            "reply": {
                "status": "COMPLETED",
                "content": {
                    "verdict": "malicious",
                    "verdict_info": {"confidence": "high"},
                    "detections": [
                        {
                            "name": "Test Detection",
                            "severity": "high",
                            "description": "Test detection description"
                        }
                    ],
                    "indicators": [
                        {
                            "type": "file_hash",
                            "value": "test_hash",
                            "description": "Test indicator",
                            "confidence": "high"
                        }
                    ]
                }
            }
        }
        
        # Configuration du mock pour retourner différentes réponses selon l'appel
        mock_post.side_effect = [upload_response, analysis_response]
        
        # Appel de la méthode à tester
        result = self.cortex_client.analyze_file(self.test_file_path)
        
        # Vérification des résultats
        self.assertIn("threats", result)
        self.assertIn("metadata", result)
        self.assertIn("indicators", result)
        self.assertIn("score", result)
        
        # Vérification des menaces détectées
        self.assertEqual(len(result["threats"]), 2)  # Verdict + détection
        self.assertEqual(result["threats"][0]["type"], "cortex_verdict")
        self.assertEqual(result["threats"][0]["severity"], "high")
        
        # Vérification des indicateurs
        self.assertEqual(len(result["indicators"]), 1)
        self.assertEqual(result["indicators"][0]["type"], "file_hash")
        self.assertEqual(result["indicators"][0]["value"], "test_hash")
        
        # Vérification du score
        self.assertEqual(result["score"], 9)  # Score pour verdict malicious

    def test_simulate_analysis(self):
        """Test de la simulation d'analyse"""
        # Test avec un fichier exécutable
        result = self.cortex_client._simulate_analysis(self.test_file_path + ".exe")
        
        self.assertIn("threats", result)
        self.assertIn("metadata", result)
        self.assertIn("indicators", result)
        self.assertIn("score", result)
        
        self.assertEqual(len(result["threats"]), 1)
        self.assertEqual(result["threats"][0]["type"], "cortex_simulated")
        self.assertEqual(result["threats"][0]["severity"], "medium")
        self.assertEqual(result["score"], 5)
        
        # Test avec un script
        result = self.cortex_client._simulate_analysis(self.test_file_path + ".ps1")
        
        self.assertEqual(len(result["threats"]), 1)
        self.assertEqual(result["threats"][0]["type"], "cortex_simulated")
        self.assertEqual(result["threats"][0]["severity"], "medium")
        self.assertEqual(result["score"], 6)
        
        # Test avec un disque virtuel
        result = self.cortex_client._simulate_analysis(self.test_file_path + ".vmdk")
        
        self.assertEqual(len(result["threats"]), 1)
        self.assertEqual(result["threats"][0]["type"], "cortex_simulated")
        self.assertEqual(result["threats"][0]["severity"], "low")
        self.assertEqual(result["score"], 3)

    @patch('requests.post')
    def test_get_incident_details(self, mock_post):
        """Test de la récupération des détails d'un incident"""
        # Configuration du mock pour simuler une réponse d'incident
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reply": {
                "incident": {
                    "incident_id": "test_incident_id",
                    "status": "new",
                    "severity": "high",
                    "description": "Test incident",
                    "detection_time": "2025-05-26T12:00:00Z",
                    "host_count": 1,
                    "hosts": [
                        {
                            "hostname": "test-host",
                            "ip": "192.168.1.100",
                            "os": "Windows 10"
                        }
                    ],
                    "alerts": [
                        {
                            "alert_id": "test-alert-id",
                            "name": "Test Alert",
                            "severity": "high",
                            "description": "Test alert description"
                        }
                    ]
                }
            }
        }
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        result = self.cortex_client.get_incident_details("test_incident_id")
        
        # Vérification des résultats
        self.assertEqual(result["incident_id"], "test_incident_id")
        self.assertEqual(result["status"], "new")
        self.assertEqual(result["severity"], "high")
        self.assertEqual(len(result["hosts"]), 1)
        self.assertEqual(len(result["alerts"]), 1)
        self.assertEqual(result["hosts"][0]["hostname"], "test-host")
        self.assertEqual(result["alerts"][0]["name"], "Test Alert")

    def test_simulate_incident_details(self):
        """Test de la simulation des détails d'un incident"""
        result = self.cortex_client._simulate_incident_details("test_incident_id")
        
        self.assertEqual(result["incident_id"], "test_incident_id")
        self.assertEqual(result["status"], "new")
        self.assertEqual(result["severity"], "high")
        self.assertIn("hosts", result)
        self.assertIn("alerts", result)
        self.assertIn("mitre_tactics", result)
        self.assertIn("mitre_techniques", result)

    @patch('requests.post')
    def test_execute_xql_query(self, mock_post):
        """Test de l'exécution d'une requête XQL"""
        # Configuration des mocks pour simuler l'exécution de requête et les résultats
        query_response = MagicMock()
        query_response.status_code = 200
        query_response.json.return_value = {
            "reply": {
                "query_id": "test_query_id"
            }
        }
        
        results_response = MagicMock()
        results_response.status_code = 200
        results_response.json.return_value = {
            "reply": {
                "status": "SUCCESS",
                "results": [
                    {"process_name": "test.exe", "command_line": "test command", "user": "test_user"},
                    {"process_name": "cmd.exe", "command_line": "cmd /c echo test", "user": "admin"}
                ],
                "total_count": 2,
                "timeframe": "last_24_hours"
            }
        }
        
        # Configuration du mock pour retourner différentes réponses selon l'appel
        mock_post.side_effect = [query_response, results_response]
        
        # Appel de la méthode à tester
        result = self.cortex_client.execute_xql_query("dataset=xdr_data | filter event_type='PROCESS'")
        
        # Vérification des résultats
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["metadata"]["query_id"], "test_query_id")
        self.assertEqual(result["metadata"]["total_count"], 2)
        self.assertEqual(result["results"][0]["process_name"], "test.exe")
        self.assertEqual(result["results"][1]["command_line"], "cmd /c echo test")

    def test_simulate_xql_results(self):
        """Test de la simulation des résultats XQL"""
        # Test avec une requête sur les processus
        result = self.cortex_client._simulate_xql_results("dataset=xdr_data | filter process", "last_24_hours")
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertIn("results", result)
        self.assertIn("metadata", result)
        self.assertTrue(len(result["results"]) > 0)
        self.assertEqual(result["metadata"]["timeframe"], "last_24_hours")
        self.assertTrue(result["metadata"]["simulated"])
        
        # Vérification que les résultats contiennent des données de processus
        self.assertIn("process_name", result["results"][0])
        
        # Test avec une requête sur les connexions réseau
        result = self.cortex_client._simulate_xql_results("dataset=xdr_data | filter network", "last_7_days")
        
        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(len(result["results"]) > 0)
        self.assertEqual(result["metadata"]["timeframe"], "last_7_days")
        
        # Vérification que les résultats contiennent des données de connexion réseau
        self.assertIn("source_ip", result["results"][0])
        self.assertIn("destination_ip", result["results"][0])

    def test_correlate_yara_with_xdr(self):
        """Test de la corrélation entre résultats YARA et données XDR"""
        # Création de résultats YARA simulés
        class YaraMatch:
            def __init__(self, rule, meta, strings):
                self.rule = rule
                self.meta = meta
                self.strings = strings
        
        yara_results = [
            YaraMatch(
                "test_rule",
                {"severity": "high", "description": "Test rule"},
                [(0, "$string1", b"test string")]
            )
        ]
        
        # Appel de la méthode à tester
        result = self.cortex_client.correlate_yara_with_xdr(yara_results, self.test_file_path)
        
        # Vérification des résultats
        self.assertIn("matches", result)
        self.assertIn("score", result)
        self.assertIn("metadata", result)
        
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["matches"][0]["rule_name"], "test_rule")
        self.assertEqual(result["matches"][0]["meta"]["severity"], "high")
        self.assertEqual(result["matches"][0]["score"], 8)
        self.assertEqual(result["score"], 8)
        
        # Vérification des métadonnées
        self.assertEqual(result["metadata"]["file_path"], self.test_file_path)
        self.assertIn("file_name", result["metadata"])
        self.assertIn("file_size", result["metadata"])
        self.assertIn("file_hash", result["metadata"])

    @patch('requests.post')
    def test_get_endpoints(self, mock_post):
        """Test de la récupération des endpoints"""
        # Configuration du mock pour simuler une réponse d'endpoints
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reply": {
                "endpoints": [
                    {
                        "endpoint_id": "1",
                        "endpoint_name": "test-endpoint-1",
                        "endpoint_type": "Server",
                        "endpoint_status": "connected",
                        "os_type": "Windows",
                        "ip": "192.168.1.100"
                    },
                    {
                        "endpoint_id": "2",
                        "endpoint_name": "test-endpoint-2",
                        "endpoint_type": "Workstation",
                        "endpoint_status": "disconnected",
                        "os_type": "Linux",
                        "ip": "192.168.1.101"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        result = self.cortex_client.get_endpoints()
        
        # Vérification des résultats
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["endpoint_id"], "1")
        self.assertEqual(result[0]["endpoint_name"], "test-endpoint-1")
        self.assertEqual(result[0]["endpoint_status"], "connected")
        self.assertEqual(result[1]["endpoint_id"], "2")
        self.assertEqual(result[1]["endpoint_type"], "Workstation")
        self.assertEqual(result[1]["os_type"], "Linux")

    def test_simulate_endpoints(self):
        """Test de la simulation des endpoints"""
        result = self.cortex_client._simulate_endpoints()
        
        self.assertTrue(len(result) > 0)
        self.assertIn("endpoint_id", result[0])
        self.assertIn("endpoint_name", result[0])
        self.assertIn("endpoint_status", result[0])
        self.assertIn("os_type", result[0])
        self.assertIn("ip", result[0])

    @patch('requests.post')
    def test_get_alerts(self, mock_post):
        """Test de la récupération des alertes"""
        # Configuration du mock pour simuler une réponse d'alertes
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reply": {
                "alerts": [
                    {
                        "alert_id": "alert-1",
                        "name": "Test Alert 1",
                        "category": "Malware",
                        "severity": "high",
                        "description": "Test alert description 1",
                        "detection_timestamp": "2025-05-26T10:00:00Z"
                    },
                    {
                        "alert_id": "alert-2",
                        "name": "Test Alert 2",
                        "category": "Network",
                        "severity": "medium",
                        "description": "Test alert description 2",
                        "detection_timestamp": "2025-05-26T11:00:00Z"
                    }
                ]
            }
        }
        mock_post.return_value = mock_response
        
        # Appel de la méthode à tester
        result = self.cortex_client.get_alerts()
        
        # Vérification des résultats
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["alert_id"], "alert-1")
        self.assertEqual(result[0]["name"], "Test Alert 1")
        self.assertEqual(result[0]["severity"], "high")
        self.assertEqual(result[1]["alert_id"], "alert-2")
        self.assertEqual(result[1]["category"], "Network")
        self.assertEqual(result[1]["severity"], "medium")

    def test_simulate_alerts(self):
        """Test de la simulation des alertes"""
        result = self.cortex_client._simulate_alerts("last_24_hours", 10)
        
        self.assertTrue(len(result) > 0)
        self.assertTrue(len(result) <= 10)
        self.assertIn("alert_id", result[0])
        self.assertIn("name", result[0])
        self.assertIn("category", result[0])
        self.assertIn("severity", result[0])
        self.assertIn("description", result[0])
        self.assertIn("detection_timestamp", result[0])

    def test_get_time_frame_value(self):
        """Test de la conversion de période de temps en date ISO"""
        # Test avec last_24_hours
        result = self.cortex_client._get_time_frame_value("last_24_hours")
        self.assertTrue(result.endswith("Z"))
        
        # Test avec last_7_days
        result = self.cortex_client._get_time_frame_value("last_7_days")
        self.assertTrue(result.endswith("Z"))
        
        # Test avec last_30_days
        result = self.cortex_client._get_time_frame_value("last_30_days")
        self.assertTrue(result.endswith("Z"))

if __name__ == '__main__':
    unittest.main()
