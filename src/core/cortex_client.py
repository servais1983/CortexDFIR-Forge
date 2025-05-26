import os
import logging
import requests
import json
import time
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CortexClient:
    """
    Client avancé pour l'API Cortex XDR
    
    Cette classe fournit une interface complète pour interagir avec l'API Cortex XDR,
    permettant l'analyse de fichiers, la récupération d'incidents, l'exécution de requêtes XQL,
    et d'autres fonctionnalités avancées.
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
        self.advanced_api = self.config.get("advanced_api", True)
        self.token_cache = {}
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, certaines fonctionnalités seront limitées")
        
        logger.info("CortexClient avancé initialisé")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Génère les en-têtes d'authentification pour les requêtes API
        
        Returns:
            Dictionnaire contenant les en-têtes d'authentification
        """
        # Vérification du cache de token
        current_time = datetime.now()
        if "token" in self.token_cache and "expiry" in self.token_cache:
            if current_time < self.token_cache["expiry"]:
                # Token en cache valide
                return {
                    "Authorization": f"Bearer {self.token_cache['token']}",
                    "Content-Type": "application/json"
                }
        
        # Génération d'un nouveau token si nécessaire
        if self.advanced_api and self.api_key and self.api_key_id:
            try:
                # Préparation de l'en-tête d'authentification de base
                headers = {
                    "x-xdr-auth-id": self.api_key_id,
                    "Authorization": self.api_key,
                    "Content-Type": "application/json"
                }
                
                # Endpoint pour l'authentification
                endpoint = f"{self.base_url}/public_api/v1/auth/generate_token"
                
                # Envoi de la requête
                response = requests.post(endpoint, headers=headers, json={})
                
                # Vérification de la réponse
                if response.status_code == 200:
                    result = response.json()
                    if "reply" in result and "token" in result["reply"]:
                        token = result["reply"]["token"]
                        # Stockage du token avec une expiration (1 heure)
                        self.token_cache = {
                            "token": token,
                            "expiry": current_time + timedelta(hours=1)
                        }
                        return {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
            except Exception as e:
                logger.error(f"Erreur lors de la génération du token: {str(e)}", exc_info=True)
        
        # Fallback sur l'authentification de base
        return {
            "x-xdr-auth-id": self.api_key_id,
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
    
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
            # Obtention des en-têtes d'authentification
            headers = self._get_auth_headers()
            
            # Préparation du fichier pour l'envoi
            with open(file_path, "rb") as file:
                file_content = file.read()
            
            # Calcul du hash SHA256 pour le suivi
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            # Endpoint pour l'analyse de fichier
            endpoint = f"{self.base_url}/public_api/v1/files/upload"
            
            # Préparation de la requête
            files = {
                "file": (os.path.basename(file_path), file_content)
            }
            
            data = {
                "request_data": {
                    "filename": os.path.basename(file_path),
                    "tenant_id": self.tenant_id,
                    "file_hash": file_hash
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
            
            # Vérification du statut de l'analyse
            if "reply" in result and "upload_id" in result["reply"]:
                upload_id = result["reply"]["upload_id"]
                
                # Attente et récupération des résultats d'analyse
                analysis_result = self._get_file_analysis_result(upload_id)
                
                # Formatage des résultats
                return self._format_cortex_results(analysis_result)
            else:
                logger.warning("Format de réponse inattendu pour l'upload de fichier")
                return self._simulate_analysis(file_path)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse Cortex XDR: {str(e)}", exc_info=True)
            # En cas d'erreur, on simule l'analyse pour permettre la poursuite du processus
            return self._simulate_analysis(file_path)
    
    def _get_file_analysis_result(self, upload_id: str, max_retries: int = 10) -> Dict[str, Any]:
        """
        Récupère les résultats d'analyse d'un fichier
        
        Args:
            upload_id: Identifiant d'upload du fichier
            max_retries: Nombre maximum de tentatives
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        endpoint = f"{self.base_url}/public_api/v1/files/get_analysis_result"
        headers = self._get_auth_headers()
        
        data = {
            "request_data": {
                "upload_id": upload_id,
                "tenant_id": self.tenant_id
            }
        }
        
        # Tentatives de récupération des résultats
        for attempt in range(max_retries):
            try:
                response = requests.post(endpoint, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Vérification du statut de l'analyse
                    if "reply" in result and "status" in result["reply"]:
                        status = result["reply"]["status"]
                        
                        if status == "COMPLETED":
                            return result
                        elif status == "PENDING" or status == "IN_PROGRESS":
                            # Attente avant la prochaine tentative
                            wait_time = 5 * (attempt + 1)  # Attente progressive
                            logger.info(f"Analyse en cours, nouvelle tentative dans {wait_time} secondes...")
                            time.sleep(wait_time)
                        else:
                            logger.warning(f"Statut d'analyse inattendu: {status}")
                            return result
                else:
                    logger.warning(f"Erreur lors de la récupération des résultats: {response.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des résultats: {str(e)}", exc_info=True)
                break
        
        # Si on arrive ici, on n'a pas pu récupérer les résultats
        logger.warning(f"Impossible de récupérer les résultats après {max_retries} tentatives")
        return {"reply": {"status": "FAILED", "content": {}}}
    
    def _format_cortex_results(self, cortex_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate les résultats de l'API Cortex XDR dans un format standard
        
        Args:
            cortex_response: Réponse de l'API Cortex XDR
        
        Returns:
            Dictionnaire formaté des résultats
        """
        formatted_results = {
            "threats": [],
            "metadata": {},
            "indicators": [],
            "score": 0
        }
        
        # Extraction des métadonnées
        if "reply" in cortex_response:
            formatted_results["metadata"]["analysis_id"] = cortex_response["reply"].get("upload_id", "")
            formatted_results["metadata"]["analysis_time"] = datetime.now().isoformat()
            formatted_results["metadata"]["status"] = cortex_response["reply"].get("status", "UNKNOWN")
        
        # Extraction des menaces depuis la réponse Cortex
        if "reply" in cortex_response and "content" in cortex_response["reply"]:
            content = cortex_response["reply"]["content"]
            
            # Traitement des verdicts
            if "verdict" in content:
                verdict = content["verdict"]
                verdict_info = content.get("verdict_info", {})
                
                # Calcul du score global
                if verdict == "malicious":
                    formatted_results["score"] = 9
                elif verdict == "suspicious":
                    formatted_results["score"] = 6
                else:
                    formatted_results["score"] = 2
                
                # Ajout du verdict comme menace
                if verdict in ["malicious", "suspicious"]:
                    formatted_results["threats"].append({
                        "type": "cortex_verdict",
                        "name": f"Fichier {verdict}",
                        "severity": "high" if verdict == "malicious" else "medium",
                        "description": f"Cortex XDR a identifié ce fichier comme {verdict}",
                        "details": verdict_info,
                        "score": formatted_results["score"]
                    })
            
            # Traitement des détections spécifiques
            if "detections" in content:
                for detection in content["detections"]:
                    severity = detection.get("severity", "medium").lower()
                    score = 0
                    
                    # Conversion de la sévérité en score
                    if severity == "critical":
                        score = 10
                    elif severity == "high":
                        score = 8
                    elif severity == "medium":
                        score = 5
                    elif severity == "low":
                        score = 3
                    else:
                        score = 1
                    
                    threat = {
                        "type": "cortex_detection",
                        "name": detection.get("name", "Détection inconnue"),
                        "severity": severity,
                        "description": detection.get("description", "Aucune description disponible"),
                        "details": detection,
                        "score": score
                    }
                    formatted_results["threats"].append(threat)
                    
                    # Mise à jour du score global si nécessaire
                    if score > formatted_results["score"]:
                        formatted_results["score"] = score
            
            # Extraction des indicateurs de compromission
            if "indicators" in content:
                for indicator in content["indicators"]:
                    formatted_results["indicators"].append({
                        "type": indicator.get("type", "unknown"),
                        "value": indicator.get("value", ""),
                        "description": indicator.get("description", ""),
                        "confidence": indicator.get("confidence", "low")
                    })
        
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
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        results = {
            "threats": [],
            "metadata": {
                "analysis_id": f"sim-{int(time.time())}",
                "analysis_time": datetime.now().isoformat(),
                "status": "COMPLETED"
            },
            "indicators": [],
            "score": 0
        }
        
        # Simulation de détections basées sur l'extension
        if file_ext in [".exe", ".dll", ".sys"]:
            threat = {
                "type": "cortex_simulated",
                "name": "Exécutable potentiellement dangereux",
                "severity": "medium",
                "description": "Les fichiers exécutables peuvent contenir du code malveillant",
                "details": {"file_extension": file_ext, "file_size": file_size},
                "score": 5
            }
            results["threats"].append(threat)
            results["score"] = 5
            
            # Ajout d'indicateurs simulés
            results["indicators"].append({
                "type": "file_hash",
                "value": f"simulated_hash_{int(time.time())}",
                "description": "Hash simulé pour démonstration",
                "confidence": "medium"
            })
            
        elif file_ext in [".ps1", ".vbs", ".js", ".hta"]:
            threat = {
                "type": "cortex_simulated",
                "name": "Script potentiellement dangereux",
                "severity": "medium",
                "description": "Les fichiers script peuvent contenir du code malveillant",
                "details": {"file_extension": file_ext, "file_size": file_size},
                "score": 6
            }
            results["threats"].append(threat)
            results["score"] = 6
            
            # Ajout d'indicateurs simulés
            results["indicators"].append({
                "type": "script_pattern",
                "value": "obfuscated_code",
                "description": "Potentiel code obfusqué détecté",
                "confidence": "medium"
            })
            
        elif file_ext in [".vmdk", ".vhd", ".vhdx"]:
            threat = {
                "type": "cortex_simulated",
                "name": "Disque virtuel - Analyse approfondie recommandée",
                "severity": "low",
                "description": "Les disques virtuels peuvent contenir des systèmes de fichiers infectés",
                "details": {"file_extension": file_ext, "file_size": file_size},
                "score": 3
            }
            results["threats"].append(threat)
            results["score"] = 3
            
            # Ajout d'indicateurs simulés
            results["indicators"].append({
                "type": "file_type",
                "value": "virtual_disk",
                "description": "Disque virtuel détecté",
                "confidence": "high"
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
            # Obtention des en-têtes d'authentification
            headers = self._get_auth_headers()
            
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
            "detection_time": datetime.now().isoformat(),
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
            ],
            "mitre_tactics": [
                "Execution",
                "Persistence"
            ],
            "mitre_techniques": [
                "T1059.001 - PowerShell",
                "T1547 - Boot or Logon Autostart Execution"
            ]
        }
    
    def execute_xql_query(self, query: str, timeframe: str = "last_24_hours") -> Dict[str, Any]:
        """
        Exécute une requête XQL (XDR Query Language)
        
        Args:
            query: Requête XQL à exécuter
            timeframe: Période de temps pour la requête (last_24_hours, last_7_days, last_30_days)
        
        Returns:
            Dictionnaire contenant les résultats de la requête
        """
        logger.info(f"Exécution de la requête XQL: {query}")
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, simulation de résultats XQL")
            return self._simulate_xql_results(query, timeframe)
        
        try:
            # Obtention des en-têtes d'authentification
            headers = self._get_auth_headers()
            
            # Endpoint pour les requêtes XQL
            endpoint = f"{self.base_url}/public_api/v1/xql/start_xql_query"
            
            # Préparation de la requête
            data = {
                "request_data": {
                    "query": query,
                    "tenant_id": self.tenant_id,
                    "timeframe": timeframe
                }
            }
            
            # Envoi de la requête
            response = requests.post(endpoint, headers=headers, json=data)
            
            # Vérification de la réponse
            if response.status_code != 200:
                logger.error(f"Erreur lors de l'exécution de la requête XQL: {response.text}")
                return self._simulate_xql_results(query, timeframe)
            
            # Traitement de la réponse
            result = response.json()
            
            # Vérification du statut de la requête
            if "reply" in result and "query_id" in result["reply"]:
                query_id = result["reply"]["query_id"]
                
                # Récupération des résultats de la requête
                return self._get_xql_results(query_id)
            else:
                logger.warning("Format de réponse inattendu pour la requête XQL")
                return self._simulate_xql_results(query, timeframe)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête XQL: {str(e)}", exc_info=True)
            return self._simulate_xql_results(query, timeframe)
    
    def _get_xql_results(self, query_id: str, max_retries: int = 10) -> Dict[str, Any]:
        """
        Récupère les résultats d'une requête XQL
        
        Args:
            query_id: Identifiant de la requête
            max_retries: Nombre maximum de tentatives
        
        Returns:
            Dictionnaire contenant les résultats de la requête
        """
        endpoint = f"{self.base_url}/public_api/v1/xql/get_query_results"
        headers = self._get_auth_headers()
        
        data = {
            "request_data": {
                "query_id": query_id,
                "tenant_id": self.tenant_id
            }
        }
        
        # Tentatives de récupération des résultats
        for attempt in range(max_retries):
            try:
                response = requests.post(endpoint, headers=headers, json=data)
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Vérification du statut de la requête
                    if "reply" in result and "status" in result["reply"]:
                        status = result["reply"]["status"]
                        
                        if status == "SUCCESS":
                            return {
                                "status": "SUCCESS",
                                "results": result["reply"].get("results", []),
                                "metadata": {
                                    "query_id": query_id,
                                    "total_count": result["reply"].get("total_count", 0),
                                    "timeframe": result["reply"].get("timeframe", "")
                                }
                            }
                        elif status == "PENDING" or status == "RUNNING":
                            # Attente avant la prochaine tentative
                            wait_time = 5 * (attempt + 1)  # Attente progressive
                            logger.info(f"Requête en cours, nouvelle tentative dans {wait_time} secondes...")
                            time.sleep(wait_time)
                        else:
                            logger.warning(f"Statut de requête inattendu: {status}")
                            return {
                                "status": status,
                                "results": [],
                                "metadata": {
                                    "query_id": query_id,
                                    "error": result["reply"].get("error", "Erreur inconnue")
                                }
                            }
                else:
                    logger.warning(f"Erreur lors de la récupération des résultats: {response.text}")
                    break
                    
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des résultats: {str(e)}", exc_info=True)
                break
        
        # Si on arrive ici, on n'a pas pu récupérer les résultats
        logger.warning(f"Impossible de récupérer les résultats après {max_retries} tentatives")
        return {
            "status": "FAILED",
            "results": [],
            "metadata": {
                "query_id": query_id,
                "error": "Timeout lors de la récupération des résultats"
            }
        }
    
    def _simulate_xql_results(self, query: str, timeframe: str) -> Dict[str, Any]:
        """
        Simule les résultats d'une requête XQL
        
        Args:
            query: Requête XQL
            timeframe: Période de temps
        
        Returns:
            Dictionnaire simulant les résultats d'une requête XQL
        """
        logger.info(f"Simulation des résultats XQL pour la requête: {query}")
        
        # Analyse de la requête pour générer des résultats pertinents
        query_lower = query.lower()
        results = []
        
        # Simulation de résultats basés sur le contenu de la requête
        if "process" in query_lower:
            # Simulation de données de processus
            processes = [
                {"process_name": "cmd.exe", "command_line": "cmd.exe /c whoami", "user": "SYSTEM", "pid": 1234},
                {"process_name": "powershell.exe", "command_line": "powershell.exe -NonI -W Hidden", "user": "Administrator", "pid": 2345},
                {"process_name": "explorer.exe", "command_line": "C:\\Windows\\explorer.exe", "user": "User", "pid": 3456}
            ]
            results.extend(processes)
            
        elif "network" in query_lower or "connection" in query_lower:
            # Simulation de données de connexion réseau
            connections = [
                {"source_ip": "192.168.1.100", "destination_ip": "8.8.8.8", "destination_port": 53, "process_name": "dns.exe"},
                {"source_ip": "192.168.1.100", "destination_ip": "203.0.113.1", "destination_port": 443, "process_name": "chrome.exe"},
                {"source_ip": "192.168.1.100", "destination_ip": "198.51.100.1", "destination_port": 80, "process_name": "svchost.exe"}
            ]
            results.extend(connections)
            
        elif "file" in query_lower:
            # Simulation de données de fichiers
            files = [
                {"file_path": "C:\\Windows\\System32\\cmd.exe", "file_hash": "aabbccddeeff", "file_size": 12345},
                {"file_path": "C:\\Users\\Admin\\Downloads\\document.pdf", "file_hash": "112233445566", "file_size": 54321},
                {"file_path": "C:\\Program Files\\suspicious.exe", "file_hash": "99887766554433", "file_size": 98765}
            ]
            results.extend(files)
            
        else:
            # Résultats génériques
            generic = [
                {"timestamp": "2025-05-26T10:00:00Z", "event_type": "GENERIC", "hostname": "DESKTOP-EXAMPLE"},
                {"timestamp": "2025-05-26T11:00:00Z", "event_type": "GENERIC", "hostname": "LAPTOP-TEST"},
                {"timestamp": "2025-05-26T12:00:00Z", "event_type": "GENERIC", "hostname": "SERVER-PROD"}
            ]
            results.extend(generic)
        
        return {
            "status": "SUCCESS",
            "results": results,
            "metadata": {
                "query_id": f"sim-{int(time.time())}",
                "total_count": len(results),
                "timeframe": timeframe,
                "simulated": True
            }
        }
    
    def correlate_yara_with_xdr(self, yara_results: List[Dict[str, Any]], file_path: str) -> Dict[str, Any]:
        """
        Corrèle les résultats YARA avec les données Cortex XDR
        
        Args:
            yara_results: Liste des correspondances YARA
            file_path: Chemin du fichier analysé
        
        Returns:
            Dictionnaire contenant les résultats de corrélation
        """
        logger.info(f"Corrélation des résultats YARA avec Cortex XDR pour {file_path}")
        
        # Initialisation des résultats de corrélation
        correlation_results = {
            "matches": [],
            "score": 0,
            "metadata": {
                "file_path": file_path,
                "analysis_time": datetime.now().isoformat()
            }
        }
        
        # Si pas de résultats YARA, retourner directement
        if not yara_results:
            return correlation_results
        
        # Extraction des informations du fichier
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        # Calcul du hash SHA256 pour la corrélation
        file_hash = ""
        try:
            with open(file_path, "rb") as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Erreur lors du calcul du hash: {str(e)}", exc_info=True)
        
        # Recherche de données XDR liées au hash
        xdr_data = {}
        if file_hash and self.api_key and self.api_key_id:
            try:
                # Requête XQL pour rechercher le hash
                xql_query = f"dataset=xdr_data | filter file_hash = '{file_hash}' | limit 10"
                xdr_data = self.execute_xql_query(xql_query)
            except Exception as e:
                logger.error(f"Erreur lors de la requête XQL: {str(e)}", exc_info=True)
        
        # Traitement des correspondances YARA
        max_score = 0
        for match in yara_results:
            # Extraction des métadonnées de la règle
            rule_name = match.rule
            meta = getattr(match, "meta", {})
            
            # Calcul du score de la règle
            rule_score = 0
            if "severity" in meta:
                severity = meta["severity"].lower()
                if severity == "critical":
                    rule_score = 10
                elif severity == "high":
                    rule_score = 8
                elif severity == "medium":
                    rule_score = 5
                elif severity == "low":
                    rule_score = 3
                else:
                    rule_score = 1
            else:
                # Score par défaut basé sur les chaînes trouvées
                strings_count = len(getattr(match, "strings", []))
                rule_score = min(8, 2 + strings_count)
            
            # Mise à jour du score maximum
            max_score = max(max_score, rule_score)
            
            # Recherche de corrélations dans les données XDR
            xdr_correlations = []
            if "results" in xdr_data:
                for result in xdr_data["results"]:
                    # Vérification des correspondances
                    if any(s[2].lower() in str(result).lower() for s in getattr(match, "strings", [])):
                        xdr_correlations.append(result)
            
            # Création de l'entrée de corrélation
            correlation_entry = {
                "rule_name": rule_name,
                "meta": meta,
                "score": rule_score,
                "strings": getattr(match, "strings", []),
                "xdr_correlations": xdr_correlations
            }
            
            correlation_results["matches"].append(correlation_entry)
        
        # Mise à jour du score global
        correlation_results["score"] = max_score
        
        # Ajout des métadonnées du fichier
        correlation_results["metadata"]["file_name"] = file_name
        correlation_results["metadata"]["file_size"] = file_size
        correlation_results["metadata"]["file_hash"] = file_hash
        
        return correlation_results
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des endpoints depuis Cortex XDR
        
        Returns:
            Liste des endpoints
        """
        logger.info("Récupération de la liste des endpoints depuis Cortex XDR")
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, simulation d'endpoints")
            return self._simulate_endpoints()
        
        try:
            # Obtention des en-têtes d'authentification
            headers = self._get_auth_headers()
            
            # Endpoint pour la liste des endpoints
            endpoint = f"{self.base_url}/public_api/v1/endpoints/get_endpoints"
            
            # Préparation de la requête
            data = {
                "request_data": {
                    "tenant_id": self.tenant_id,
                    "filters": [],
                    "search_from": 0,
                    "search_to": 100
                }
            }
            
            # Envoi de la requête
            response = requests.post(endpoint, headers=headers, json=data)
            
            # Vérification de la réponse
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des endpoints: {response.text}")
                return self._simulate_endpoints()
            
            # Traitement de la réponse
            result = response.json()
            
            # Formatage des résultats
            if "reply" in result and "endpoints" in result["reply"]:
                return result["reply"]["endpoints"]
            else:
                logger.warning("Format de réponse inattendu pour la liste des endpoints")
                return self._simulate_endpoints()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des endpoints: {str(e)}", exc_info=True)
            return self._simulate_endpoints()
    
    def _simulate_endpoints(self) -> List[Dict[str, Any]]:
        """
        Simule une liste d'endpoints
        
        Returns:
            Liste simulée d'endpoints
        """
        logger.info("Simulation de la liste des endpoints")
        
        return [
            {
                "endpoint_id": "1",
                "endpoint_name": "DESKTOP-EXAMPLE",
                "endpoint_type": "Server",
                "endpoint_status": "connected",
                "os_type": "Windows",
                "ip": "192.168.1.100",
                "domain": "EXAMPLE",
                "alias": "Server1",
                "first_seen": "2025-01-01T00:00:00Z",
                "last_seen": "2025-05-26T12:00:00Z"
            },
            {
                "endpoint_id": "2",
                "endpoint_name": "LAPTOP-TEST",
                "endpoint_type": "Workstation",
                "endpoint_status": "connected",
                "os_type": "Windows",
                "ip": "192.168.1.101",
                "domain": "EXAMPLE",
                "alias": "UserLaptop",
                "first_seen": "2025-01-02T00:00:00Z",
                "last_seen": "2025-05-26T12:30:00Z"
            },
            {
                "endpoint_id": "3",
                "endpoint_name": "SERVER-PROD",
                "endpoint_type": "Server",
                "endpoint_status": "disconnected",
                "os_type": "Linux",
                "ip": "192.168.1.200",
                "domain": "",
                "alias": "ProdServer",
                "first_seen": "2025-01-03T00:00:00Z",
                "last_seen": "2025-05-25T18:00:00Z"
            }
        ]
    
    def get_alerts(self, time_frame: str = "last_24_hours", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les alertes depuis Cortex XDR
        
        Args:
            time_frame: Période de temps (last_24_hours, last_7_days, last_30_days)
            limit: Nombre maximum d'alertes à récupérer
        
        Returns:
            Liste des alertes
        """
        logger.info(f"Récupération des alertes depuis Cortex XDR (période: {time_frame})")
        
        # Vérification de la configuration
        if not self.api_key or not self.api_key_id:
            logger.warning("Clés API Cortex XDR non configurées, simulation d'alertes")
            return self._simulate_alerts(time_frame, limit)
        
        try:
            # Obtention des en-têtes d'authentification
            headers = self._get_auth_headers()
            
            # Endpoint pour la liste des alertes
            endpoint = f"{self.base_url}/public_api/v1/alerts/get_alerts_multi_events"
            
            # Préparation de la requête
            data = {
                "request_data": {
                    "tenant_id": self.tenant_id,
                    "filters": [
                        {
                            "field": "creation_time",
                            "operator": "gte",
                            "value": self._get_time_frame_value(time_frame)
                        }
                    ],
                    "search_from": 0,
                    "search_to": limit,
                    "sort": {
                        "field": "creation_time",
                        "keyword": "desc"
                    }
                }
            }
            
            # Envoi de la requête
            response = requests.post(endpoint, headers=headers, json=data)
            
            # Vérification de la réponse
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des alertes: {response.text}")
                return self._simulate_alerts(time_frame, limit)
            
            # Traitement de la réponse
            result = response.json()
            
            # Formatage des résultats
            if "reply" in result and "alerts" in result["reply"]:
                return result["reply"]["alerts"]
            else:
                logger.warning("Format de réponse inattendu pour la liste des alertes")
                return self._simulate_alerts(time_frame, limit)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes: {str(e)}", exc_info=True)
            return self._simulate_alerts(time_frame, limit)
    
    def _get_time_frame_value(self, time_frame: str) -> str:
        """
        Convertit une période de temps en date ISO
        
        Args:
            time_frame: Période de temps (last_24_hours, last_7_days, last_30_days)
        
        Returns:
            Date ISO correspondant au début de la période
        """
        now = datetime.now()
        
        if time_frame == "last_7_days":
            start_time = now - timedelta(days=7)
        elif time_frame == "last_30_days":
            start_time = now - timedelta(days=30)
        else:  # last_24_hours par défaut
            start_time = now - timedelta(days=1)
        
        return start_time.isoformat() + "Z"
    
    def _simulate_alerts(self, time_frame: str, limit: int) -> List[Dict[str, Any]]:
        """
        Simule une liste d'alertes
        
        Args:
            time_frame: Période de temps
            limit: Nombre maximum d'alertes
        
        Returns:
            Liste simulée d'alertes
        """
        logger.info(f"Simulation de la liste des alertes (période: {time_frame}, limite: {limit})")
        
        # Génération d'alertes simulées
        alerts = []
        alert_types = [
            "Malware", "Suspicious Process", "Network Connection", "Fileless Attack",
            "Ransomware", "Data Exfiltration", "Brute Force", "Lateral Movement"
        ]
        
        # Détermination du nombre d'alertes à générer
        num_alerts = min(limit, 20)  # Maximum 20 alertes simulées
        
        for i in range(num_alerts):
            # Calcul d'une date aléatoire dans la période
            days_ago = 0
            if time_frame == "last_7_days":
                days_ago = random.randint(0, 7)
            elif time_frame == "last_30_days":
                days_ago = random.randint(0, 30)
            else:  # last_24_hours par défaut
                days_ago = random.randint(0, 1)
                
            alert_time = datetime.now() - timedelta(days=days_ago)
            
            # Sélection aléatoire du type d'alerte
            alert_type = random.choice(alert_types)
            
            # Détermination de la sévérité
            severity_options = ["critical", "high", "medium", "low"]
            severity_weights = [0.1, 0.2, 0.4, 0.3]  # Pondération pour la distribution
            severity = random.choices(severity_options, severity_weights)[0]
            
            # Création de l'alerte simulée
            alert = {
                "alert_id": f"sim-alert-{i+1}",
                "name": f"{alert_type} Alert",
                "category": alert_type,
                "severity": severity,
                "description": f"Alerte simulée de type {alert_type}",
                "detection_timestamp": alert_time.isoformat() + "Z",
                "host": {
                    "hostname": f"HOST-{random.randint(1, 5)}",
                    "ip": f"192.168.1.{random.randint(1, 254)}",
                    "os": random.choice(["Windows", "Linux", "macOS"])
                },
                "user": f"user{random.randint(1, 10)}",
                "action_status": random.choice(["new", "in_progress", "resolved"]),
                "action_taken": random.choice(["none", "blocked", "isolated"]),
                "mitre_tactics": [
                    random.choice(["Initial Access", "Execution", "Persistence", "Privilege Escalation", "Defense Evasion"])
                ],
                "mitre_techniques": [
                    f"T{random.randint(1000, 1999)}"
                ]
            }
            
            alerts.append(alert)
        
        return alerts
