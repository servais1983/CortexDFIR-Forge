import os
import logging
import magic
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class FileAnalyzer:
    """
    Classe pour l'analyse de différents types de fichiers
    """
    
    def __init__(self):
        """
        Initialisation de l'analyseur de fichiers
        """
        logger.info("FileAnalyzer initialisé")
    
    def get_file_type(self, file_path: str) -> str:
        """
        Détermine le type de fichier
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Type de fichier détecté
        """
        try:
            # Utilisation de python-magic pour détecter le type MIME
            mime_type = magic.from_file(file_path, mime=True)
            return mime_type
        except Exception as e:
            logger.error(f"Erreur lors de la détection du type de fichier: {str(e)}", exc_info=True)
            # Fallback sur l'extension
            _, ext = os.path.splitext(file_path)
            return f"unknown/{ext.lstrip('.')}" if ext else "unknown/unknown"
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier en fonction de son type
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        file_type = self.get_file_type(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        logger.info(f"Analyse du fichier {file_path} de type {file_type}")
        
        results = {
            "file_type": file_type,
            "file_extension": file_ext,
            "threats": []
        }
        
        # Analyse spécifique selon le type de fichier
        if "application/x-executable" in file_type or file_ext in [".exe", ".dll", ".sys"]:
            results.update(self._analyze_executable(file_path))
        elif "text/plain" in file_type or file_ext in [".log", ".txt"]:
            results.update(self._analyze_log_file(file_path))
        elif "text/csv" in file_type or file_ext == ".csv":
            results.update(self._analyze_csv_file(file_path))
        elif file_ext in [".vmdk", ".vhd", ".vhdx"]:
            results.update(self._analyze_disk_image(file_path))
        elif file_ext in [".ps1", ".vbs", ".js", ".hta"]:
            results.update(self._analyze_script(file_path))
        
        return results
    
    def _analyze_executable(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier exécutable
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse de l'exécutable {file_path}")
        
        results = {
            "threats": []
        }
        
        # Vérification des caractéristiques suspectes
        try:
            # Analyse de base des exécutables
            with open(file_path, "rb") as f:
                content = f.read()
                
                # Recherche de chaînes suspectes
                suspicious_strings = [
                    b"cmd.exe", b"powershell.exe", b"rundll32.exe", b"regsvr32.exe",
                    b"CreateRemoteThread", b"VirtualAlloc", b"WriteProcessMemory",
                    b"http://", b"https://", b"ftp://", b"ws://"
                ]
                
                for string in suspicious_strings:
                    if string in content:
                        results["threats"].append({
                            "type": "suspicious_string",
                            "name": f"Chaîne suspecte: {string.decode('utf-8', errors='ignore')}",
                            "severity": "medium",
                            "description": f"L'exécutable contient la chaîne suspecte: {string.decode('utf-8', errors='ignore')}"
                        })
                
                # Vérification des caractéristiques de packing
                packing_indicators = [
                    b"UPX", b"ASPack", b"PECompact", b"FSG", b"MPRESS"
                ]
                
                for indicator in packing_indicators:
                    if indicator in content:
                        results["threats"].append({
                            "type": "packer_detected",
                            "name": f"Packer détecté: {indicator.decode('utf-8', errors='ignore')}",
                            "severity": "medium",
                            "description": f"L'exécutable semble être packé avec {indicator.decode('utf-8', errors='ignore')}, ce qui peut indiquer une tentative d'obfuscation"
                        })
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de l'exécutable: {str(e)}", exc_info=True)
        
        return results
    
    def _analyze_log_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier de log
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse du fichier de log {file_path}")
        
        results = {
            "threats": []
        }
        
        # Recherche d'indicateurs de compromission dans les logs
        try:
            suspicious_patterns = [
                ("error", "low"),
                ("failed login", "medium"),
                ("authentication failure", "medium"),
                ("access denied", "low"),
                ("malware", "high"),
                ("virus", "high"),
                ("trojan", "high"),
                ("backdoor", "high"),
                ("exploit", "high"),
                ("attack", "medium"),
                ("suspicious", "medium"),
                ("unauthorized", "medium"),
                ("permission denied", "low"),
                ("brute force", "high"),
                ("injection", "high"),
                ("xss", "high"),
                ("sql injection", "high"),
                ("remote code execution", "critical"),
                ("privilege escalation", "critical"),
                ("ransomware", "critical"),
                ("data exfiltration", "high")
            ]
            
            with open(file_path, "r", errors="ignore") as f:
                line_count = 0
                for line in f:
                    line_count += 1
                    line_lower = line.lower()
                    
                    for pattern, severity in suspicious_patterns:
                        if pattern in line_lower:
                            results["threats"].append({
                                "type": "suspicious_log_entry",
                                "name": f"Entrée de log suspecte: {pattern}",
                                "severity": severity,
                                "description": f"Ligne {line_count}: {line.strip()}",
                                "details": {
                                    "line_number": line_count,
                                    "pattern": pattern
                                }
                            })
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du fichier de log: {str(e)}", exc_info=True)
        
        return results
    
    def _analyze_csv_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier CSV
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse du fichier CSV {file_path}")
        
        results = {
            "threats": []
        }
        
        try:
            import csv
            
            with open(file_path, "r", newline="", errors="ignore") as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader, [])
                
                # Analyse des en-têtes pour détecter des colonnes sensibles
                sensitive_headers = [
                    "password", "mot de passe", "mdp", "pwd", "passwd",
                    "credit card", "carte de crédit", "cc", "cvv", "ccv",
                    "social security", "ssn", "numéro de sécurité sociale",
                    "token", "api key", "clé api", "secret"
                ]
                
                for header in headers:
                    header_lower = header.lower()
                    for sensitive in sensitive_headers:
                        if sensitive in header_lower:
                            results["threats"].append({
                                "type": "sensitive_data_column",
                                "name": f"Colonne de données sensibles: {header}",
                                "severity": "high",
                                "description": f"Le fichier CSV contient une colonne qui pourrait contenir des données sensibles: {header}"
                            })
                
                # Analyse des données pour détecter des valeurs suspectes
                row_count = 0
                for row in csv_reader:
                    row_count += 1
                    if row_count > 1000:  # Limite pour éviter d'analyser des fichiers trop volumineux
                        break
                    
                    for i, cell in enumerate(row):
                        if i < len(headers):
                            # Vérification des URL suspectes
                            if ("http://" in cell or "https://" in cell) and any(domain in cell.lower() for domain in [
                                "pastebin.com", "github.io", "raw.githubusercontent.com", 
                                "dropbox.com", "drive.google.com", "mega.nz"
                            ]):
                                results["threats"].append({
                                    "type": "suspicious_url",
                                    "name": f"URL suspecte dans {headers[i]}",
                                    "severity": "medium",
                                    "description": f"Ligne {row_count}: URL potentiellement suspecte détectée dans la colonne {headers[i]}: {cell}"
                                })
                            
                            # Vérification des commandes suspectes
                            suspicious_commands = [
                                "cmd.exe", "powershell", "bash", "wget", "curl", "nc ", "netcat",
                                "chmod +x", "sudo ", "rm -rf", "del /", "format c:", "mkfs",
                                "dd if=", "dd of=", ">dev/null", "2>&1", "|base64", "eval("
                            ]
                            
                            for cmd in suspicious_commands:
                                if cmd in cell:
                                    results["threats"].append({
                                        "type": "suspicious_command",
                                        "name": f"Commande suspecte dans {headers[i]}",
                                        "severity": "high",
                                        "description": f"Ligne {row_count}: Commande potentiellement suspecte détectée dans la colonne {headers[i]}: {cell}"
                                    })
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du fichier CSV: {str(e)}", exc_info=True)
        
        return results
    
    def _analyze_disk_image(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse une image disque (VMDK, VHD, etc.)
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse de l'image disque {file_path}")
        
        results = {
            "threats": []
        }
        
        # Pour l'instant, on ne fait qu'une analyse basique
        # Une analyse complète nécessiterait de monter l'image et d'analyser son contenu
        
        results["threats"].append({
            "type": "disk_image",
            "name": "Image disque détectée",
            "severity": "info",
            "description": "Les images disque nécessitent une analyse approfondie pour détecter les menaces. Considérez l'utilisation d'outils spécialisés."
        })
        
        return results
    
    def _analyze_script(self, file_path: str) -> Dict[str, Any]:
        """
        Analyse un fichier script (PowerShell, VBS, JS, etc.)
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"Analyse du script {file_path}")
        
        results = {
            "threats": []
        }
        
        try:
            with open(file_path, "r", errors="ignore") as f:
                content = f.read()
                
                # Recherche de techniques d'obfuscation
                obfuscation_indicators = [
                    ("powershell -e", "high"),
                    ("powershell -enc", "high"),
                    ("FromBase64String", "medium"),
                    ("Convert.FromBase64String", "medium"),
                    ("IEX", "high"),
                    ("Invoke-Expression", "high"),
                    ("Invoke-Obfuscation", "high"),
                    ("Invoke-Mimikatz", "critical"),
                    ("Invoke-ReflectivePEInjection", "critical"),
                    ("char[]", "medium"),
                    ("\\u00", "medium"),
                    ("eval(", "high"),
                    ("String.fromCharCode", "medium"),
                    ("ActiveXObject", "medium"),
                    ("WScript.Shell", "medium"),
                    ("cmd /c", "high"),
                    ("cmd.exe /c", "high"),
                    ("bitsadmin", "high"),
                    ("certutil -urlcache", "high"),
                    ("certutil -decode", "high"),
                    ("regsvr32", "high"),
                    ("rundll32", "high"),
                    ("wmic", "medium")
                ]
                
                for indicator, severity in obfuscation_indicators:
                    if indicator in content:
                        results["threats"].append({
                            "type": "suspicious_script_content",
                            "name": f"Contenu de script suspect: {indicator}",
                            "severity": severity,
                            "description": f"Le script contient du code potentiellement malveillant: {indicator}"
                        })
                
                # Recherche d'URL
                import re
                urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', content)
                for url in urls:
                    results["threats"].append({
                        "type": "script_url",
                        "name": "URL dans le script",
                        "severity": "medium",
                        "description": f"Le script contient une URL qui pourrait être utilisée pour télécharger du contenu malveillant: {url}"
                    })
        
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du script: {str(e)}", exc_info=True)
        
        return results
