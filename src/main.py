import os
import sys
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from ui.main_window import Ui_MainWindow
from core.analyzer import CortexAnalyzer
from core.report_generator import ReportGenerator
from utils.config_manager import ConfigManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cortexdfir.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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
            logger.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
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
        
    def select_files(self):
        """Sélection des fichiers à analyser"""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Tous les fichiers (*.*)")
        
        if file_dialog.exec_():
            self.selected_files = file_dialog.selectedFiles()
            self.ui.lstFiles.clear()
            for file_path in self.selected_files:
                self.ui.lstFiles.addItem(file_path)
            
            self.ui.btnStartAnalysis.setEnabled(len(self.selected_files) > 0)
            self.ui.statusbar.showMessage(f"{len(self.selected_files)} fichiers sélectionnés")
            logger.info(f"{len(self.selected_files)} fichiers sélectionnés pour analyse")
    
    def start_analysis(self):
        """Démarrage de l'analyse des fichiers sélectionnés"""
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
        
        logger.info(f"Analyse démarrée pour {len(self.selected_files)} fichiers avec types: {', '.join(analysis_types)}")
    
    def update_progress(self, value, message):
        """Mise à jour de la barre de progression"""
        self.ui.progressBar.setValue(value)
        self.ui.statusbar.showMessage(message)
    
    def analysis_completed(self, results):
        """Traitement des résultats d'analyse"""
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
        
        logger.info(f"Analyse terminée avec {total_threats} menaces détectées")
    
    def analysis_error(self, error_message):
        """Gestion des erreurs d'analyse"""
        QMessageBox.critical(self, "Erreur d'analyse", error_message)
        
        # Réactivation des contrôles
        self.ui.btnSelectFiles.setEnabled(True)
        self.ui.btnStartAnalysis.setEnabled(True)
        self.ui.progressBar.setValue(0)
        self.ui.statusbar.showMessage("Erreur lors de l'analyse")
        
        logger.error(f"Erreur d'analyse: {error_message}")
    
    def display_results(self, results):
        """Affichage des résultats dans l'interface"""
        self.ui.treeResults.clear()
        
        # TODO: Implémenter l'affichage des résultats dans le TreeWidget
        # Cette fonction sera développée dans une prochaine étape
    
    def generate_report(self):
        """Génération du rapport d'analyse"""
        if not self.analysis_results:
            QMessageBox.warning(self, "Attention", "Aucun résultat d'analyse disponible.")
            return
        
        # Sélection du dossier de destination
        output_dir = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de destination")
        if not output_dir:
            return
        
        try:
            # Génération du rapport
            report_path = self.report_generator.generate_html_report(self.analysis_results, output_dir)
            
            QMessageBox.information(
                self, 
                "Rapport généré", 
                f"Le rapport a été généré avec succès:\n{report_path}"
            )
            
            logger.info(f"Rapport généré: {report_path}")
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Erreur de génération", 
                f"Erreur lors de la génération du rapport: {str(e)}"
            )
            logger.error(f"Erreur de génération de rapport: {str(e)}", exc_info=True)
    
    def open_settings(self):
        """Ouverture de la fenêtre de paramètres"""
        # TODO: Implémenter la fenêtre de paramètres
        # Cette fonction sera développée dans une prochaine étape
        QMessageBox.information(self, "Paramètres", "Fonctionnalité à venir dans une prochaine version.")

def main():
    """Point d'entrée principal de l'application"""
    app = QApplication(sys.argv)
    window = MainApplication()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
