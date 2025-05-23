import os
import logging
import yara
from typing import List, Optional, Any

logger = logging.getLogger(__name__)

class YaraScanner:
    """
    Scanner utilisant les règles YARA pour la détection de menaces
    """
    
    def __init__(self, rules_dir: str):
        """
        Initialisation du scanner YARA
        
        Args:
            rules_dir: Répertoire contenant les règles YARA
        """
        self.rules_dir = rules_dir
        self.rules = None
        self._load_rules()
        
        logger.info(f"YaraScanner initialisé avec le répertoire de règles: {rules_dir}")
    
    def _load_rules(self) -> None:
        """
        Charge les règles YARA depuis le répertoire spécifié
        """
        try:
            if not os.path.exists(self.rules_dir):
                logger.warning(f"Le répertoire de règles YARA n'existe pas: {self.rules_dir}")
                os.makedirs(self.rules_dir, exist_ok=True)
                self._create_default_rules()
            
            rule_files = []
            for root, _, files in os.walk(self.rules_dir):
                for file in files:
                    if file.endswith('.yar') or file.endswith('.yara'):
                        rule_files.append(os.path.join(root, file))
            
            if not rule_files:
                logger.warning("Aucune règle YARA trouvée, création des règles par défaut")
                self._create_default_rules()
                # Recherche à nouveau après création des règles par défaut
                rule_files = [os.path.join(self.rules_dir, f) for f in os.listdir(self.rules_dir) 
                             if f.endswith('.yar') or f.endswith('.yara')]
            
            # Compilation des règles
            filepaths = {os.path.basename(f): f for f in rule_files}
            self.rules = yara.compile(filepaths=filepaths)
            
            logger.info(f"{len(filepaths)} règles YARA chargées")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles YARA: {str(e)}", exc_info=True)
            self.rules = None
    
    def _create_default_rules(self) -> None:
        """
        Crée des règles YARA par défaut si aucune n'est trouvée
        """
        try:
            # Règle pour la détection de ransomware
            ransomware_rule = """
rule generic_ransomware {
    meta:
        description = "Détecte des indicateurs génériques de ransomware"
        author = "CortexDFIR-Forge"
        severity = "critical"
    strings:
        $ransom_msg1 = "Your files have been encrypted" nocase
        $ransom_msg2 = "Your files are locked" nocase
        $ransom_msg3 = "Your files are no longer accessible" nocase
        $ransom_msg4 = "All your files have been encrypted" nocase
        $ransom_msg5 = "To get all your files back" nocase
        $ransom_msg6 = "Send us email" nocase
        $ransom_msg7 = "Bitcoin" nocase
        $ransom_msg8 = "BTC" nocase
        $ransom_msg9 = "Decryption key" nocase
        $ransom_msg10 = "Pay the ransom" nocase
        $ransom_msg11 = "Decrypt your files" nocase
        
        $lockbit1 = "LockBit" nocase
        $lockbit2 = "LOCKFILE" nocase
        $lockbit3 = ".lockbit" nocase
        
        $file_ext1 = ".encrypted" nocase
        $file_ext2 = ".locked" nocase
        $file_ext3 = ".crypt" nocase
        $file_ext4 = ".crypto" nocase
        $file_ext5 = ".locky" nocase
        $file_ext6 = ".zepto" nocase
        $file_ext7 = ".cerber" nocase
        $file_ext8 = ".osiris" nocase
        $file_ext9 = ".odin" nocase
        $file_ext10 = ".sage" nocase
    condition:
        2 of ($ransom_msg*) or 
        any of ($lockbit*) or 
        2 of ($file_ext*)
}
"""
            
            # Règle pour la détection de backdoors
            backdoor_rule = """
rule generic_backdoor {
    meta:
        description = "Détecte des indicateurs génériques de backdoor"
        author = "CortexDFIR-Forge"
        severity = "high"
    strings:
        $cmd1 = "cmd.exe" nocase
        $cmd2 = "powershell.exe" nocase
        $cmd3 = "sh -c" nocase
        $cmd4 = "bash -c" nocase
        $cmd5 = "cmd /c" nocase
        
        $net1 = "netcat" nocase
        $net2 = "nc -l" nocase
        $net3 = "ncat" nocase
        $net4 = "socat" nocase
        
        $connect1 = "CreateRemoteThread"
        $connect2 = "connect("
        $connect3 = "socket("
        $connect4 = "WSAConnect"
        $connect5 = "InternetConnect"
        
        $persist1 = "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" nocase
        $persist2 = "HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" nocase
        $persist3 = "HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" nocase
        $persist4 = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" nocase
        $persist5 = "crontab -e" nocase
        $persist6 = "/etc/cron" nocase
        $persist7 = "schtasks /create" nocase
        $persist8 = "New-ScheduledTask" nocase
        
        $payload1 = "meterpreter" nocase
        $payload2 = "metasploit" nocase
        $payload3 = "reverse shell" nocase
        $payload4 = "bind shell" nocase
        $payload5 = "empire" nocase
        $payload6 = "cobalt strike" nocase
        $payload7 = "cobaltstrike" nocase
    condition:
        (1 of ($cmd*) and 1 of ($net*)) or
        (1 of ($connect*) and 1 of ($persist*)) or
        any of ($payload*)
}
"""
            
            # Règle pour la détection de phishing
            phishing_rule = """
rule generic_phishing {
    meta:
        description = "Détecte des indicateurs génériques de phishing"
        author = "CortexDFIR-Forge"
        severity = "medium"
    strings:
        $domain1 = "login" nocase
        $domain2 = "signin" nocase
        $domain3 = "account" nocase
        $domain4 = "secure" nocase
        $domain5 = "verify" nocase
        $domain6 = "update" nocase
        $domain7 = "confirm" nocase
        
        $brand1 = "microsoft" nocase
        $brand2 = "apple" nocase
        $brand3 = "google" nocase
        $brand4 = "amazon" nocase
        $brand5 = "paypal" nocase
        $brand6 = "facebook" nocase
        $brand7 = "instagram" nocase
        $brand8 = "twitter" nocase
        $brand9 = "linkedin" nocase
        $brand10 = "netflix" nocase
        $brand11 = "bank" nocase
        $brand12 = "credit" nocase
        
        $form1 = "<form" nocase
        $form2 = "method=\"post\"" nocase
        $form3 = "input type=\"password\"" nocase
        $form4 = "input type=\"text\"" nocase
        $form5 = "input type=\"email\"" nocase
        
        $text1 = "password expired" nocase
        $text2 = "verify your account" nocase
        $text3 = "confirm your identity" nocase
        $text4 = "unusual activity" nocase
        $text5 = "suspicious login" nocase
        $text6 = "account suspended" nocase
        $text7 = "limited access" nocase
        $text8 = "security alert" nocase
    condition:
        (1 of ($domain*) and 1 of ($brand*)) and
        (1 of ($form*) or 1 of ($text*))
}
"""
            
            # Écriture des règles dans des fichiers
            with open(os.path.join(self.rules_dir, "ransomware.yar"), "w") as f:
                f.write(ransomware_rule)
            
            with open(os.path.join(self.rules_dir, "backdoor.yar"), "w") as f:
                f.write(backdoor_rule)
            
            with open(os.path.join(self.rules_dir, "phishing.yar"), "w") as f:
                f.write(phishing_rule)
            
            logger.info("Règles YARA par défaut créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des règles YARA par défaut: {str(e)}", exc_info=True)
    
    def scan_file(self, file_path: str) -> Optional[List[Any]]:
        """
        Analyse un fichier avec les règles YARA
        
        Args:
            file_path: Chemin du fichier à analyser
        
        Returns:
            Liste des correspondances YARA, ou None en cas d'erreur
        """
        if not self.rules:
            logger.warning("Aucune règle YARA chargée, impossible d'analyser le fichier")
            return None
        
        try:
            matches = self.rules.match(file_path)
            
            if matches:
                logger.info(f"Analyse YARA de {file_path}: {len(matches)} correspondances trouvées")
            else:
                logger.info(f"Analyse YARA de {file_path}: aucune correspondance trouvée")
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse YARA du fichier {file_path}: {str(e)}", exc_info=True)
            return None
    
    def scan_memory(self, data: bytes) -> Optional[List[Any]]:
        """
        Analyse des données en mémoire avec les règles YARA
        
        Args:
            data: Données à analyser
        
        Returns:
            Liste des correspondances YARA, ou None en cas d'erreur
        """
        if not self.rules:
            logger.warning("Aucune règle YARA chargée, impossible d'analyser les données")
            return None
        
        try:
            matches = self.rules.match(data=data)
            
            if matches:
                logger.info(f"Analyse YARA des données en mémoire: {len(matches)} correspondances trouvées")
            else:
                logger.info("Analyse YARA des données en mémoire: aucune correspondance trouvée")
            
            return matches
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse YARA des données en mémoire: {str(e)}", exc_info=True)
            return None
