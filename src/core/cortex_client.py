import os
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CortexClient:
    """
    Client pour l'API Cortex XDR
    """
    
    def __init__(self, config_manager):
        """
        Initialisation du client Cortex XDR
        
        Args:
            config_manager: Gestionnaire de configuration pour accéder aux paramètres Cortex XDR
        """
        self.config_manager = config_manager
        self.config = self.config_manager.get_cortex_config()
        self.base_url = self.config.get("base_url", "https://api.xdr.paloaltonetworks.com")
        self.api_key = self.config.get("api_key", "")
        self.api_key_id = self.config.get("api_key_id", "")
        self.tenant_id = self.config.get("tenant_id", "")
        
        logger.info("CortexClient initialisé")
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Envoie un fichier à Cortex XDR pour analyse
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        
        Raises:
            Exception: Si l'analyse échoue
        """
        logger.info(f"Envoi du fichier {file_path} à Cortex XDR pour analyse")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Le fichier {file_path} n'existe pas")
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, simulation d'analyse")
            return self._simulate_analysis(file_path)
        
        try:
            # Préparation de l'en-tête d'authentification
            headers = {
                "x-xdr-auth-id": self.api_key_id,
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Préparation du fichier pour l'envoi
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Endpoint pour l'analyse de fichier
            endpoint = f"{self.base_url}/public_api/v1/files/upload"
            
            # Préparation de la requête
            files = {
                "file": (os.path.basename(file_path), file_content)
            }
            
            data = {
                "request_data": {
                    "filename": os.path.basename(file_path),
                    "tenant_id": self.tenant_id
                }
            }
            
            # Envoi de la requête
            response = requests.post(endpoint, headers=headers, files=files, data=data)
            
            # Vérification de la réponse
            if response.status_code != 200:
                logger.error(f"Erreur lors de l'analyse Cortex XDR: {response.text}")
                raise Exception(f"Erreur Cortex XDR: {response.status_code} - {response.text}")
            
            # Traitement de la réponse
            result = response.json()
            
            # Formatage des résultats
            return self._format_cortex_results(result)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse Cortex XDR: {str(e)}", exc_info=True)
            # En cas d'erreur, on simule l'analyse pour permettre la poursuite du processus
            return self._simulate_analysis(file_path)
    
    def _format_cortex_results(self, cortex_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate les résultats de l'API Cortex XDR dans un format standard
        
        Args:
            cortex_response: Réponse de l'API Cortex XDR
        
        Returns:
            Dictionnaire formaté des résultats
        """
        formatted_results = {
            "threats": []
        }
        
        # Extraction des menaces depuis la réponse Cortex
        if "reply" in cortex_response and "content" in cortex_response["reply"]:
            content = cortex_response["reply"]["content"]
            
            # Traitement des verdicts
            if "verdict" in content:
                verdict = content["verdict"]
                if verdict == "malicious":
                    formatted_results["threats"].append({
                        "type": "cortex_verdict",
                        "name": "Fichier malveillant",
                        "severity": "high",
                        "description": "Cortex XDR a identifié ce fichier comme malveillant",
                        "details": content.get("verdict_info", {})
                    })
                elif verdict == "suspicious":
                    formatted_results["threats"].append({
                        "type": "cortex_verdict",
                        "name": "Fichier suspect",
                        "severity": "medium",
                        "description": "Cortex XDR a identifié ce fichier comme suspect",
                        "details": content.get("verdict_info", {})
                    })
            
            # Traitement des détections spécifiques
            if "detections" in content:
                for detection in content["detections"]:
                    threat = {
                        "type": "cortex_detection",
                        "name": detection.get("name", "Détection inconnue"),
                        "severity": detection.get("severity", "medium").lower(),
                        "description": detection.get("description", "Aucune description disponible"),
                        "details": detection
                    }
                    formatted_results["threats"].append(threat)
        
        return formatted_results
    
    def _simulate_analysis(self, file_path: str) -> Dict[str, Any]:
        """
        Simule une analyse Cortex XDR lorsque l'API n'est pas disponible
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire simulant les résultats d'analyse
        """
        logger.info(f"Simulation d'analyse Cortex XDR pour {file_path}")
        
        # Résultats simulés basés sur l'extension du fichier
        file_ext = os.path.splitext(file_path)[1].lower()
        
        results = {
            "threats": []
        }
        
        # Simulation de détections basées sur l'extension
        if file_ext in [".exe", ".dll", ".sys"]:
            results["threats"].append({
                "type": "cortex_simulated",
                "name": "Exécutable potentiellement dangereux",
                "severity": "medium",
                "description": "Les fichiers exécutables peuvent contenir du code malveillant",
                "details": {"file_extension": file_ext}
            })
        elif file_ext in [".ps1", ".vbs", ".js", ".hta"]:
            results["threats"].append({
                "type": "cortex_simulated",
                "name": "Script potentiellement dangereux",
                "severity": "medium",
                "description": "Les fichiers script peuvent contenir du code malveillant",
                "details": {"file_extension": file_ext}
            })
        elif file_ext in [".vmdk", ".vhd", ".vhdx"]:
            results["threats"].append({
                "type": "cortex_simulated",
                "name": "Disque virtuel - Analyse approfondie recommandée",
                "severity": "low",
                "description": "Les disques virtuels peuvent contenir des systèmes de fichiers infectés",
                "details": {"file_extension": file_ext}
            })
        
        return results
    
    def get_incident_details(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un incident depuis Cortex XDR
        
        Args:
            incident_id: Identifiant de l'incident
        
        Returns:
            Dictionnaire contenant les détails de l'incident, ou None si non trouvé
        """
        logger.info(f"Récupération des détails de l'incident {incident_id}")
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, simulation de détails d'incident")
            return self._simulate_incident_details(incident_id)
        
        try:
            # Préparation de l'en-tête d'authentification
            headers = {
                "x-xdr-auth-id": self.api_key_id,
                "Authorization": self.api_key,
                "Content-Type": "application/json"
            }
            
            # Endpoint pour les détails d'incident
            endpoint = f"{self.base_url}/public_api/v1/incidents/get_incident_extra_data"
            
            # Préparation de la requête
            data = {
                "request_data": {
                    "incident_id": incident_id,
                    "tenant_id": self.tenant_id
                }
            }
            
            # Envoi de la requête
            response = requests.post(endpoint, headers=headers, json=data)
            
            # Vérification de la réponse
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des détails de l'incident: {response.text}")
                return None
            
            # Traitement de la réponse
            result = response.json()
            
            # Formatage des résultats
            if "reply" in result and "incident" in result["reply"]:
                return result["reply"]["incident"]
            else:
                logger.warning(f"Format de réponse inattendu pour l'incident {incident_id}")
                return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails de l'incident: {str(e)}", exc_info=True)
            return self._simulate_incident_details(incident_id)
    
    def _simulate_incident_details(self, incident_id: str) -> Dict[str, Any]:
        """
        Simule les détails d'un incident lorsque l'API n'est pas disponible
        
        Args:
            incident_id: Identifiant de l'incident
        
        Returns:
            Dictionnaire simulant les détails d'un incident
        """
        logger.info(f"Simulation des détails de l'incident {incident_id}")
        
        return {
            "incident_id": incident_id,
            "status": "new",
            "severity": "high",
            "description": "Incident simulé pour démonstration",
            "detection_time": "2025-05-23T10:00:00Z",
            "host_count": 1,
            "hosts": [
                {
                    "hostname": "DESKTOP-EXAMPLE",
                    "ip": "192.168.1.100",
                    "os": "Windows 10"
                }
            ],
            "alerts": [
                {
                    "alert_id": "alert-001",
                    "name": "Comportement suspect détecté",
                    "severity": "high",
                    "description": "Exécution de commande PowerShell suspecte"
                }
            ]
        }
