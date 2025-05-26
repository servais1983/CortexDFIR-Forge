import os
import json
import gettext
from typing import Dict, Any, Optional

class I18nManager:
    """
    Gestionnaire d'internationalisation pour CortexDFIR-Forge
    
    Cette classe gère la traduction et l'internationalisation de l'application,
    permettant de supporter plusieurs langues dans l'interface et les rapports.
    """
    
    def __init__(self, locale_dir: str = None, default_locale: str = 'fr'):
        """
        Initialisation du gestionnaire d'internationalisation
        
        Args:
            locale_dir: Répertoire des fichiers de traduction (optionnel)
            default_locale: Locale par défaut (fr par défaut)
        """
        # Répertoire des locales
        if locale_dir is None:
            self.locale_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "locales")
        else:
            self.locale_dir = locale_dir
            
        # Création du répertoire des locales s'il n'existe pas
        os.makedirs(self.locale_dir, exist_ok=True)
        
        # Locale par défaut
        self.default_locale = default_locale
        
        # Locale courante
        self.current_locale = default_locale
        
        # Dictionnaire des traductions
        self.translations = {}
        
        # Chargement des traductions
        self._load_translations()
    
    def _load_translations(self):
        """Chargement des traductions disponibles"""
        # Parcours des répertoires de locales
        if os.path.exists(self.locale_dir):
            for locale in os.listdir(self.locale_dir):
                locale_path = os.path.join(self.locale_dir, locale, 'LC_MESSAGES')
                if os.path.isdir(locale_path):
                    try:
                        # Initialisation de gettext pour cette locale
                        translation = gettext.translation('cortexdfir', 
                                                         localedir=self.locale_dir, 
                                                         languages=[locale])
                        self.translations[locale] = translation
                    except Exception as e:
                        print(f"Erreur lors du chargement de la traduction pour {locale}: {str(e)}")
        
        # Si aucune traduction n'est disponible, on utilise gettext par défaut
        if not self.translations:
            self.translations[self.default_locale] = gettext.NullTranslations()
    
    def set_locale(self, locale: str) -> bool:
        """
        Définition de la locale courante
        
        Args:
            locale: Code de la locale (ex: 'fr', 'en')
            
        Returns:
            True si la locale a été changée, False sinon
        """
        if locale in self.translations:
            self.current_locale = locale
            return True
        elif locale[:2] in self.translations:  # Essai avec le code de langue court
            self.current_locale = locale[:2]
            return True
        else:
            return False
    
    def get_available_locales(self) -> Dict[str, str]:
        """
        Récupération des locales disponibles
        
        Returns:
            Dictionnaire des locales disponibles (code: nom)
        """
        locales = {}
        
        # Noms des langues
        language_names = {
            'fr': 'Français',
            'en': 'English',
            'es': 'Español',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'ru': 'Русский',
            'zh': '中文',
            'ja': '日本語',
            'ko': '한국어'
        }
        
        for locale in self.translations.keys():
            if locale in language_names:
                locales[locale] = language_names[locale]
            else:
                locales[locale] = locale
        
        return locales
    
    def translate(self, text: str) -> str:
        """
        Traduction d'un texte
        
        Args:
            text: Texte à traduire
            
        Returns:
            Texte traduit
        """
        if self.current_locale in self.translations:
            translation = self.translations[self.current_locale]
            return translation.gettext(text)
        else:
            # Fallback sur la locale par défaut
            if self.default_locale in self.translations:
                translation = self.translations[self.default_locale]
                return translation.gettext(text)
            else:
                return text
    
    def translate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Traduction des valeurs d'un dictionnaire
        
        Args:
            data: Dictionnaire à traduire
            
        Returns:
            Dictionnaire avec les valeurs traduites
        """
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.translate(value)
            elif isinstance(value, dict):
                result[key] = self.translate_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.translate_dict(item) if isinstance(item, dict) else
                    self.translate(item) if isinstance(item, str) else
                    item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    def generate_pot_file(self, output_file: str = None) -> bool:
        """
        Génération d'un fichier POT (template de traduction)
        
        Args:
            output_file: Chemin du fichier POT à générer (optionnel)
            
        Returns:
            True si la génération a réussi, False sinon
        """
        if output_file is None:
            output_file = os.path.join(self.locale_dir, 'cortexdfir.pot')
        
        try:
            # Création du répertoire parent si nécessaire
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            # Extraction des chaînes à traduire
            import subprocess
            
            # Répertoire source
            src_dir = os.path.dirname(os.path.dirname(__file__))
            
            # Commande xgettext
            cmd = [
                'xgettext',
                '--language=Python',
                '--keyword=_',
                '--keyword=gettext',
                '--keyword=translate',
                '--output=' + output_file,
                '--package-name=CortexDFIR-Forge',
                '--package-version=1.0',
                '--copyright-holder=CortexDFIR-Forge',
                '--msgid-bugs-address=contact@cortexdfir-forge.com'
            ]
            
            # Ajout des fichiers Python
            for root, _, files in os.walk(src_dir):
                for file in files:
                    if file.endswith('.py'):
                        cmd.append(os.path.join(root, file))
            
            # Exécution de la commande
            subprocess.run(cmd, check=True)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la génération du fichier POT: {str(e)}")
            return False
    
    def create_locale(self, locale: str) -> bool:
        """
        Création d'une nouvelle locale
        
        Args:
            locale: Code de la locale (ex: 'fr', 'en')
            
        Returns:
            True si la création a réussi, False sinon
        """
        try:
            # Création des répertoires
            locale_path = os.path.join(self.locale_dir, locale, 'LC_MESSAGES')
            os.makedirs(locale_path, exist_ok=True)
            
            # Génération du fichier POT
            pot_file = os.path.join(self.locale_dir, 'cortexdfir.pot')
            self.generate_pot_file(pot_file)
            
            # Création du fichier PO
            po_file = os.path.join(locale_path, 'cortexdfir.po')
            
            import subprocess
            
            # Si le fichier PO existe déjà, on le met à jour
            if os.path.exists(po_file):
                cmd = [
                    'msgmerge',
                    '--update',
                    po_file,
                    pot_file
                ]
            else:
                # Sinon, on le crée
                cmd = [
                    'msginit',
                    '--input=' + pot_file,
                    '--output=' + po_file,
                    '--locale=' + locale
                ]
            
            # Exécution de la commande
            subprocess.run(cmd, check=True)
            
            return True
        except Exception as e:
            print(f"Erreur lors de la création de la locale {locale}: {str(e)}")
            return False
    
    def compile_translations(self) -> bool:
        """
        Compilation des fichiers de traduction
        
        Returns:
            True si la compilation a réussi, False sinon
        """
        try:
            import subprocess
            
            # Parcours des répertoires de locales
            for locale in os.listdir(self.locale_dir):
                locale_path = os.path.join(self.locale_dir, locale, 'LC_MESSAGES')
                if os.path.isdir(locale_path):
                    po_file = os.path.join(locale_path, 'cortexdfir.po')
                    mo_file = os.path.join(locale_path, 'cortexdfir.mo')
                    
                    if os.path.exists(po_file):
                        # Compilation du fichier PO en MO
                        cmd = [
                            'msgfmt',
                            '--output-file=' + mo_file,
                            po_file
                        ]
                        
                        # Exécution de la commande
                        subprocess.run(cmd, check=True)
            
            # Rechargement des traductions
            self._load_translations()
            
            return True
        except Exception as e:
            print(f"Erreur lors de la compilation des traductions: {str(e)}")
            return False
    
    def get_translation_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Récupération des statistiques de traduction
        
        Returns:
            Dictionnaire des statistiques par locale
        """
        stats = {}
        
        try:
            import subprocess
            
            # Parcours des répertoires de locales
            for locale in os.listdir(self.locale_dir):
                locale_path = os.path.join(self.locale_dir, locale, 'LC_MESSAGES')
                if os.path.isdir(locale_path):
                    po_file = os.path.join(locale_path, 'cortexdfir.po')
                    
                    if os.path.exists(po_file):
                        # Exécution de msgfmt avec l'option --statistics
                        cmd = [
                            'msgfmt',
                            '--statistics',
                            po_file
                        ]
                        
                        # Exécution de la commande
                        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
                        
                        # Analyse de la sortie
                        if result.stderr:
                            # Format typique: "X translated messages, Y fuzzy translations, Z untranslated messages."
                            parts = result.stderr.strip().split(',')
                            
                            translated = 0
                            fuzzy = 0
                            untranslated = 0
                            
                            for part in parts:
                                if 'translated message' in part:
                                    translated = int(part.split()[0])
                                elif 'fuzzy translation' in part:
                                    fuzzy = int(part.split()[0])
                                elif 'untranslated message' in part:
                                    untranslated = int(part.split()[0])
                            
                            stats[locale] = {
                                'translated': translated,
                                'fuzzy': fuzzy,
                                'untranslated': untranslated,
                                'total': translated + fuzzy + untranslated,
                                'completion': round(translated / (translated + fuzzy + untranslated) * 100, 2) if (translated + fuzzy + untranslated) > 0 else 0
                            }
        except Exception as e:
            print(f"Erreur lors de la récupération des statistiques de traduction: {str(e)}")
        
        return stats
    
    def export_translations_to_json(self, output_dir: str = None) -> bool:
        """
        Exportation des traductions au format JSON
        
        Args:
            output_dir: Répertoire de sortie (optionnel)
            
        Returns:
            True si l'exportation a réussi, False sinon
        """
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static", "i18n")
        
        try:
            # Création du répertoire de sortie
            os.makedirs(output_dir, exist_ok=True)
            
            # Parcours des répertoires de locales
            for locale in self.translations.keys():
                # Sauvegarde de la locale courante
                current_locale = self.current_locale
                
                # Définition de la locale pour l'exportation
                self.set_locale(locale)
                
                # Dictionnaire des traductions
                translations = {}
                
                # Chargement des chaînes à traduire depuis le fichier POT
                pot_file = os.path.join(self.locale_dir, 'cortexdfir.pot')
                
                if os.path.exists(pot_file):
                    with open(pot_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Extraction des msgid
                        import re
                        msgids = re.findall(r'msgid "(.*?)"', content)
                        
                        # Traduction de chaque msgid
                        for msgid in msgids:
                            if msgid:  # Ignorer les msgid vides
                                translations[msgid] = self.translate(msgid)
                
                # Exportation au format JSON
                output_file = os.path.join(output_dir, f"{locale}.json")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=2)
                
                # Restauration de la locale courante
                self.set_locale(current_locale)
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'exportation des traductions au format JSON: {str(e)}")
            return False
