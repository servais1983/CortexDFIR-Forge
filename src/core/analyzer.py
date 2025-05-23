import os
import logging
from typing import Dict, List, Any

from core.cortex_client import CortexClient
from utils.file_analyzer import FileAnalyzer
from utils.yara_scanner import YaraScanner

logger = logging.getLogger(__name__)

class CortexAnalyzer:
    """
    Classe principale pour l'analyse des fichiers avec Cortex XDR
    """
    
    def __init__(self, config_manager):
        """
        Initialisation de l'analyseur Cortex
        
        Args:
            config_manager: Gestionnaire de configuration pour accéder aux paramètres Cortex XDR
        """
        self.config_manager = config_manager
        self.cortex_client = CortexClient(config_manager)
        self.file_analyzer = FileAnalyzer()
        self.yara_scanner = YaraScanner(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules"))
        
        logger.info("CortexAnalyzer initialisé")
    
    def analyze_file(self, file_path: str, analysis_types: List[str]) -> Dict[str, Any]:
        """
        Analyse un fichier avec les types d'analyse spécifiés
        
        Args:
            file_path: Chemin du fichier à analyser
            analysis_types: Liste des types d'analyse à effectuer
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse du fichier {file_path} avec types: {analysis_types}")
        
        results = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "file_size": os.path.getsize(file_path),
            "file_type": self.file_analyzer.get_file_type(file_path),
            "threats": [],
            "score": 0,
            "analysis_types": analysis_types
        }
        
        # Analyse locale avec YARA
        yara_results = self.yara_scanner.scan_file(file_path)
        if yara_results:
            for match in yara_results:
                threat = {
                    "type": "yara_match",
                    "name": match.rule,
                    "severity": self._get_rule_severity(match.rule),
                    "description": f"Correspondance avec la règle YARA: {match.rule}",
                    "details": match.strings
                }
                results["threats"].append(threat)
        
        # Analyse spécifique au type de fichier
        file_type_results = self.file_analyzer.analyze_file(file_path)
        if file_type_results.get("threats"):
            results["threats"].extend(file_type_results["threats"])
        
        # Intégration avec Cortex XDR pour les analyses avancées
        if "malware" in analysis_types or "ransomware" in analysis_types:
            try:
                cortex_results = self.cortex_client.analyze_file(file_path)
                if cortex_results.get("threats"):
                    results["threats"].extend(cortex_results["threats"])
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse Cortex XDR: {str(e)}", exc_info=True)
                results["errors"] = results.get("errors", []) + [f"Erreur Cortex XDR: {str(e)}"]
        
        # Calcul du score global
        results["score"] = self._calculate_score(results["threats"])
        
        logger.info(f"Analyse terminée pour {file_path}: {len(results['threats'])} menaces détectées, score {results['score']}")
        return results
    
    def _calculate_score(self, threats: List[Dict[str, Any]]) -> int:
        """
        Calcule un score de risque basé sur les menaces détectées
        
        Args:
            threats: Liste des menaces détectées
        
        Returns:
            Score de risque (0-100)
        """
        if not threats:
            return 0
        
        score = 0
        for threat in threats:
            severity = threat.get("severity", "medium").lower()
            if severity == "critical":
                score += 25
            elif severity == "high":
                score += 15
            elif severity == "medium":
                score += 7
            elif severity == "low":
                score += 3
        
        # Plafonnement à 100
        return min(score, 100)
    
    def _get_rule_severity(self, rule_name: str) -> str:
        """
        Détermine la sévérité d'une règle YARA basée sur son nom
        
        Args:
            rule_name: Nom de la règle YARA
        
        Returns:
            Niveau de sévérité (critical, high, medium, low)
        """
        rule_name_lower = rule_name.lower()
        
        if "ransomware" in rule_name_lower or "lockbit" in rule_name_lower:
            return "critical"
        elif "backdoor" in rule_name_lower or "rootkit" in rule_name_lower:
            return "high"
        elif "malware" in rule_name_lower or "trojan" in rule_name_lower:
            return "medium"
        else:
            return "low"
