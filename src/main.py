import os
import logging
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.main_window import Ui_MainWindow
from core.analyzer import CortexAnalyzer
from core.report_generator import ReportGenerator
from utils.config_manager import ConfigManager
from utils.input_validator import InputValidator
from utils.secure_logger import SecureLogger

# Initialisation du logger sécurisé
logger = SecureLogger("main_application")

class AnalysisThread(QThread):
    """Thread pour exécuter l'analyse en arrière-plan"""
    progress_update = pyqtSignal(int, str)
    analysis_complete = pyqtSignal(dict)
    analysis_error = pyqtSignal(str)

    def __init__(self, analyzer, files, analysis_types):
        super().__init__()
        self.analyzer = analyzer
        self.files = files
        self.analysis_types = analysis_types

    def run(self):
        try:
            total_files = len(self.files)
            results = {}
            
            for i, file_path in enumerate(self.files):
                self.progress_update.emit(int((i / total_files) * 100), f"Analyse de {os.path.basename(file_path)}...")
                file_result = self.analyzer.analyze_file(file_path, self.analysis_types)
                results[file_path] = file_result
                
            self.analysis_complete.emit(results)
        except Exception as e:
            logger.log_exception(f"Erreur lors de l'analyse: {str(e)}")
            self.analysis_error.emit(f"Erreur lors de l'analyse: {str(e)}")

class MainApplication(QMainWindow):
    """Application principale CortexDFIR-Forge"""
    
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # Initialisation des composants
        self.config_manager = ConfigManager()
        self.analyzer = CortexAnalyzer(self.config_manager)
        self.report_generator = ReportGenerator()
        self.input_validator = InputValidator(self.config_manager)
        
        # Connexion des signaux
        self.ui.btnSelectFiles.clicked.connect(self.select_files)
        self.ui.btnStartAnalysis.clicked.connect(self.start_analysis)
        self.ui.btnGenerateReport.clicked.connect(self.generate_report)
        self.ui.btnSettings.clicked.connect(self.open_settings)
        
        # Initialisation de l'interface
        self.ui.btnGenerateReport.setEnabled(False)
        self.ui.progressBar.setValue(0)
        self.selected_files = []
        self.analysis_results = {}
        
        logger.info("Application CortexDFIR-Forge démarrée")
        logger.security("Application démarrée", {"version": "1.0.0"})
        
    def select_files(self):
        """Sélection des fichiers à analyser"""
        try:
            file_dialog = QFileDialog()
            file_dialog.setFileMode(QFileDialog.ExistingFiles)
            
            # Définition des filtres de fichiers autorisés
            allowed_extensions = []
            for category, extensions in self.input_validator.ALLOWED_EXTENSIONS.items():
                allowed_extensions.extend(extensions)
            
            filter_str = "Fichiers supportés ("
            for ext in allowed_extensions:
                filter_str += f"*{ext} "
            filter_str = filter_str.strip() + ")"
            
            file_dialog.setNameFilter(filter_str)
            
            if file_dialog.exec_():
                selected_files = file_dialog.selectedFiles()
                
                # Validation des fichiers sélectionnés
                valid_files = []
                invalid_files = []
                
                for file_path in selected_files:
                    # Sanitize le chemin du fichier
                    sanitized_path = self.input_validator.sanitize_file_path(file_path)
                    
                    # Valide le fichier
                    is_valid, error_message = self.input_validator.validate_file(sanitized_path)
                    
                    if is_valid:
                        valid_files.append(sanitized_path)
                    else:
                        invalid_files.append((sanitized_path, error_message))
                
                # Mise à jour de la liste des fichiers
                self.ui.lstFiles.clear()
                for file_path in valid_files:
                    self.ui.lstFiles.addItem(file_path)
                
                # Affichage des erreurs pour les fichiers invalides
                if invalid_files:
                    error_message = "Les fichiers suivants n'ont pas pu être ajoutés :\n\n"
                    for file_path, error in invalid_files:
                        error_message += f"- {os.path.basename(file_path)}: {error}\n"
                    
                    QMessageBox.warning(self, "Fichiers invalides", error_message)
                
                # Mise à jour des fichiers sélectionnés
                self.selected_files = valid_files
                
                self.ui.btnStartAnalysis.setEnabled(len(self.selected_files) > 0)
                self.ui.statusbar.showMessage(f"{len(self.selected_files)} fichiers valides sélectionnés")
                
                # Journalisation de l'événement
                logger.audit(
                    "select_files", 
                    "files", 
                    details={
                        "valid_count": len(valid_files),
                        "invalid_count": len(invalid_files),
                        "file_types": [os.path.splitext(f)[1] for f in valid_files]
                    }
                )
        except Exception as e:
            logger.log_exception(f"Erreur lors de la sélection des fichiers: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la sélection des fichiers: {str(e)}")
    
    def start_analysis(self):
        """Démarrage de l'analyse des fichiers sélectionnés"""
        try:
            if not self.selected_files:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un fichier à analyser.")
                return
            
            # Récupération des types d'analyse sélectionnés
            analysis_types = []
            if self.ui.chkMalware.isChecked():
                analysis_types.append("malware")
            if self.ui.chkRansomware.isChecked():
                analysis_types.append("ransomware")
            if self.ui.chkPhishing.isChecked():
                analysis_types.append("phishing")
            if self.ui.chkPersistence.isChecked():
                analysis_types.append("persistence")
            
            if not analysis_types:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un type d'analyse.")
                return
            
            # Validation finale des fichiers avant analyse
            valid_files = self.input_validator.get_valid_files(self.selected_files)
            
            if not valid_files:
                QMessageBox.critical(self, "Erreur", "Aucun fichier valide à analyser.")
                return
            
            if len(valid_files) < len(self.selected_files):
                QMessageBox.warning(
                    self, 
                    "Attention", 
                    f"{len(self.selected_files) - len(valid_files)} fichiers ont été exclus car ils ne sont plus valides."
                )
                
                # Mise à jour de la liste des fichiers
                self.ui.lstFiles.clear()
                for file_path in valid_files:
                    self.ui.lstFiles.addItem(file_path)
                
                self.selected_files = valid_files
            
            # Désactivation des contrôles pendant l'analyse
            self.ui.btnSelectFiles.setEnabled(False)
            self.ui.btnStartAnalysis.setEnabled(False)
            self.ui.btnGenerateReport.setEnabled(False)
            
            # Démarrage du thread d'analyse
            self.analysis_thread = AnalysisThread(self.analyzer, self.selected_files, analysis_types)
            self.analysis_thread.progress_update.connect(self.update_progress)
            self.analysis_thread.analysis_complete.connect(self.analysis_completed)
            self.analysis_thread.analysis_error.connect(self.analysis_error)
            self.analysis_thread.start()
            
            # Journalisation de l'événement
            logger.audit(
                "start_analysis", 
                "analysis", 
                details={
                    "file_count": len(self.selected_files),
                    "analysis_types": analysis_types
                }
            )
        except Exception as e:
            logger.log_exception(f"Erreur lors du démarrage de l'analyse: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du démarrage de l'analyse: {str(e)}")
    
    def update_progress(self, value, message):
        """Mise à jour de la barre de progression"""
        try:
            self.ui.progressBar.setValue(value)
            self.ui.statusbar.showMessage(message)
        except Exception as e:
            logger.log_exception(f"Erreur lors de la mise à jour de la progression: {str(e)}")
    
    def analysis_completed(self, results):
        """Traitement des résultats d'analyse"""
        try:
            self.analysis_results = results
            
            # Réactivation des contrôles
            self.ui.btnSelectFiles.setEnabled(True)
            self.ui.btnStartAnalysis.setEnabled(True)
            self.ui.btnGenerateReport.setEnabled(True)
            
            # Affichage du résumé
            total_threats = sum(len(result.get("threats", [])) for result in results.values())
            self.ui.statusbar.showMessage(f"Analyse terminée. {total_threats} menaces détectées.")
            
            # Mise à jour de l'interface avec les résultats
            self.display_results(results)
            
            # Journalisation de l'événement
            logger.audit(
                "analysis_completed", 
                "analysis", 
                details={
                    "file_count": len(results),
                    "threat_count": total_threats
                }
            )
        except Exception as e:
            logger.log_exception(f"Erreur lors du traitement des résultats d'analyse: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors du traitement des résultats: {str(e)}")
    
    def analysis_error(self, error_message):
        """Gestion des erreurs d'analyse"""
        try:
            QMessageBox.critical(self, "Erreur d'analyse", error_message)
            
            # Réactivation des contrôles
            self.ui.btnSelectFiles.setEnabled(True)
            self.ui.btnStartAnalysis.setEnabled(True)
            self.ui.progressBar.setValue(0)
            self.ui.statusbar.showMessage("Erreur lors de l'analyse")
            
            # Journalisation de l'événement
            logger.error(f"Erreur d'analyse: {error_message}")
        except Exception as e:
            logger.log_exception(f"Erreur lors de la gestion des erreurs d'analyse: {str(e)}")
    
    def display_results(self, results):
        """Affichage des résultats dans l'interface"""
        try:
            self.ui.treeResults.clear()
            
            # TODO: Implémenter l'affichage des résultats dans le TreeWidget
            # Cette fonction sera développée dans une prochaine étape
        except Exception as e:
            logger.log_exception(f"Erreur lors de l'affichage des résultats: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'affichage des résultats: {str(e)}")
    
    def generate_report(self):
        """Génération du rapport d'analyse"""
        try:
            if not self.analysis_results:
                QMessageBox.warning(self, "Attention", "Aucun résultat d'analyse disponible.")
                return
            
            # Sélection du dossier de destination
            output_dir = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de destination")
            if not output_dir:
                return
            
            # Validation du dossier de destination
            if not os.path.isdir(output_dir) or not os.access(output_dir, os.W_OK):
                QMessageBox.critical(self, "Erreur", "Le dossier sélectionné n'est pas accessible en écriture.")
                return
            
            # Génération du rapport
            report_path = self.report_generator.generate_html_report(self.analysis_results, output_dir)
            
            QMessageBox.information(
                self, 
                "Rapport généré", 
                f"Le rapport a été généré avec succès:\n{report_path}"
            )
            
            # Journalisation de l'événement
            logger.audit(
                "generate_report", 
                "report", 
                details={
                    "output_dir": output_dir,
                    "report_path": report_path
                }
            )
        except Exception as e:
            logger.log_exception(f"Erreur lors de la génération du rapport: {str(e)}")
            QMessageBox.critical(
                self, 
                "Erreur de génération", 
                f"Erreur lors de la génération du rapport: {str(e)}"
            )
    
    def open_settings(self):
        """Ouverture de la fenêtre de paramètres"""
        try:
            # TODO: Implémenter la fenêtre de paramètres
            # Cette fonction sera développée dans une prochaine étape
            QMessageBox.information(self, "Paramètres", "Fonctionnalité à venir dans une prochaine version.")
            
            # Journalisation de l'événement
            logger.audit("open_settings", "settings")
        except Exception as e:
            logger.log_exception(f"Erreur lors de l'ouverture des paramètres: {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")

def main():
    """Point d'entrée principal de l'application"""
    try:
        # Création du répertoire de logs s'il n'existe pas
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        app = QApplication(sys.argv)
        window = MainApplication()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        # En cas d'erreur critique, on utilise le logging standard
        logging.basicConfig(level=logging.ERROR)
        logging.error(f"Erreur critique lors du démarrage de l'application: {str(e)}", exc_info=True)
        
        # Affichage d'un message d'erreur à l'utilisateur
        if QApplication.instance():
            QMessageBox.critical(
                None, 
                "Erreur critique", 
                f"Une erreur critique est survenue lors du démarrage de l'application:\n{str(e)}\n\nConsultez les logs pour plus de détails."
            )
        
        sys.exit(1)

if __name__ == "__main__":
    main()
