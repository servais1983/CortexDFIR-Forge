import os
import sys
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, QComboBox, 
                            QCheckBox, QProgressBar, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSplitter, QFrame, QTextEdit, QGroupBox, 
                            QFormLayout, QLineEdit, QMessageBox, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor, QPalette
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis

from src.core.analyzer import Analyzer
from src.core.cortex_client import CortexClient
from src.core.report_generator import ReportGenerator
from src.utils.config_manager import ConfigManager
from src.utils.yara_scanner import YaraScanner

class WorkerThread(QThread):
    """Thread pour exécuter des tâches en arrière-plan"""
    update_progress = pyqtSignal(int, str)
    analysis_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, analyzer, file_paths, options):
        super().__init__()
        self.analyzer = analyzer
        self.file_paths = file_paths
        self.options = options
    
    def run(self):
        try:
            total_files = len(self.file_paths)
            results = {"files": [], "threats": [], "indicators": [], "summary": {}}
            
            for i, file_path in enumerate(self.file_paths):
                # Mise à jour de la progression
                progress = int((i / total_files) * 100)
                self.update_progress.emit(progress, f"Analyse de {os.path.basename(file_path)}...")
                
                # Analyse du fichier
                file_result = self.analyzer.analyze_file(file_path, self.options)
                
                # Ajout des résultats
                results["files"].append(file_result)
                
                # Extraction des menaces et indicateurs
                if "threats" in file_result:
                    results["threats"].extend(file_result["threats"])
                if "indicators" in file_result:
                    results["indicators"].extend(file_result["indicators"])
            
            # Génération du résumé
            results["summary"] = self.analyzer.generate_summary(results["files"])
            
            # Analyse terminée
            self.update_progress.emit(100, "Analyse terminée")
            self.analysis_complete.emit(results)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'analyse: {str(e)}", exc_info=True)
            self.error_occurred.emit(f"Erreur lors de l'analyse: {str(e)}")

class XQLQueryThread(QThread):
    """Thread pour exécuter des requêtes XQL"""
    query_complete = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cortex_client, query, timeframe):
        super().__init__()
        self.cortex_client = cortex_client
        self.query = query
        self.timeframe = timeframe
    
    def run(self):
        try:
            # Exécution de la requête XQL
            results = self.cortex_client.execute_xql_query(self.query, self.timeframe)
            
            # Requête terminée
            self.query_complete.emit(results)
            
        except Exception as e:
            logging.error(f"Erreur lors de l'exécution de la requête XQL: {str(e)}", exc_info=True)
            self.error_occurred.emit(f"Erreur lors de l'exécution de la requête XQL: {str(e)}")

class AlertsThread(QThread):
    """Thread pour récupérer les alertes Cortex XDR"""
    alerts_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cortex_client, timeframe, limit):
        super().__init__()
        self.cortex_client = cortex_client
        self.timeframe = timeframe
        self.limit = limit
    
    def run(self):
        try:
            # Récupération des alertes
            alerts = self.cortex_client.get_alerts(self.timeframe, self.limit)
            
            # Récupération terminée
            self.alerts_complete.emit(alerts)
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des alertes: {str(e)}", exc_info=True)
            self.error_occurred.emit(f"Erreur lors de la récupération des alertes: {str(e)}")

class EndpointsThread(QThread):
    """Thread pour récupérer les endpoints Cortex XDR"""
    endpoints_complete = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, cortex_client):
        super().__init__()
        self.cortex_client = cortex_client
    
    def run(self):
        try:
            # Récupération des endpoints
            endpoints = self.cortex_client.get_endpoints()
            
            # Récupération terminée
            self.endpoints_complete.emit(endpoints)
            
        except Exception as e:
            logging.error(f"Erreur lors de la récupération des endpoints: {str(e)}", exc_info=True)
            self.error_occurred.emit(f"Erreur lors de la récupération des endpoints: {str(e)}")

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application CortexDFIR-Forge"""
    
    def __init__(self):
        super().__init__()
        
        # Configuration du logger
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialisation des composants
        self.config_manager = ConfigManager()
        self.cortex_client = CortexClient(self.config_manager)
        self.yara_scanner = YaraScanner(os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules"))
        self.analyzer = Analyzer(self.yara_scanner, self.cortex_client)
        self.report_generator = ReportGenerator()
        
        # Variables d'état
        self.selected_files = []
        self.analysis_results = None
        self.current_xql_results = None
        self.current_alerts = None
        self.current_endpoints = None
        
        # Configuration de l'interface
        self.setup_ui()
        
        # Connexion des signaux
        self.connect_signals()
        
        # Chargement des configurations
        self.load_config()
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        # Configuration de la fenêtre principale
        self.setWindowTitle("CortexDFIR-Forge")
        self.setMinimumSize(1200, 800)
        
        # Création du widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Création des onglets
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Onglet d'analyse
        self.analysis_tab = QWidget()
        self.tabs.addTab(self.analysis_tab, "Analyse")
        
        # Onglet de requêtes XQL
        self.xql_tab = QWidget()
        self.tabs.addTab(self.xql_tab, "Requêtes XQL")
        
        # Onglet d'incidents et alertes
        self.incidents_tab = QWidget()
        self.tabs.addTab(self.incidents_tab, "Incidents & Alertes")
        
        # Onglet de configuration
        self.config_tab = QWidget()
        self.tabs.addTab(self.config_tab, "Configuration")
        
        # Configuration des onglets
        self.setup_analysis_tab()
        self.setup_xql_tab()
        self.setup_incidents_tab()
        self.setup_config_tab()
        
        # Barre de statut
        self.statusBar().showMessage("Prêt")
    
    def setup_analysis_tab(self):
        """Configuration de l'onglet d'analyse"""
        layout = QVBoxLayout(self.analysis_tab)
        
        # Section de sélection de fichiers
        file_group = QGroupBox("Sélection des fichiers")
        file_layout = QVBoxLayout(file_group)
        
        file_buttons_layout = QHBoxLayout()
        self.select_file_button = QPushButton("Sélectionner des fichiers")
        self.select_dir_button = QPushButton("Sélectionner un dossier")
        self.clear_selection_button = QPushButton("Effacer la sélection")
        
        file_buttons_layout.addWidget(self.select_file_button)
        file_buttons_layout.addWidget(self.select_dir_button)
        file_buttons_layout.addWidget(self.clear_selection_button)
        
        self.file_list = QListWidget()
        
        file_layout.addLayout(file_buttons_layout)
        file_layout.addWidget(QLabel("Fichiers sélectionnés:"))
        file_layout.addWidget(self.file_list)
        
        # Section d'options d'analyse
        options_group = QGroupBox("Options d'analyse")
        options_layout = QVBoxLayout(options_group)
        
        self.use_yara_checkbox = QCheckBox("Utiliser les règles YARA")
        self.use_yara_checkbox.setChecked(True)
        
        self.use_cortex_checkbox = QCheckBox("Analyser avec Cortex XDR")
        self.use_cortex_checkbox.setChecked(True)
        
        self.detect_ransomware_checkbox = QCheckBox("Détecter les ransomwares")
        self.detect_ransomware_checkbox.setChecked(True)
        
        self.detect_backdoors_checkbox = QCheckBox("Détecter les backdoors")
        self.detect_backdoors_checkbox.setChecked(True)
        
        self.detect_phishing_checkbox = QCheckBox("Détecter les tentatives de phishing")
        self.detect_phishing_checkbox.setChecked(True)
        
        self.correlate_checkbox = QCheckBox("Corréler avec Cortex XDR")
        self.correlate_checkbox.setChecked(True)
        
        options_layout.addWidget(self.use_yara_checkbox)
        options_layout.addWidget(self.use_cortex_checkbox)
        options_layout.addWidget(self.detect_ransomware_checkbox)
        options_layout.addWidget(self.detect_backdoors_checkbox)
        options_layout.addWidget(self.detect_phishing_checkbox)
        options_layout.addWidget(self.correlate_checkbox)
        
        # Section de contrôle d'analyse
        control_layout = QHBoxLayout()
        
        self.start_analysis_button = QPushButton("Lancer l'analyse")
        self.start_analysis_button.setMinimumHeight(40)
        self.start_analysis_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        self.stop_analysis_button = QPushButton("Arrêter l'analyse")
        self.stop_analysis_button.setMinimumHeight(40)
        self.stop_analysis_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.stop_analysis_button.setEnabled(False)
        
        control_layout.addWidget(self.start_analysis_button)
        control_layout.addWidget(self.stop_analysis_button)
        
        # Section de progression
        progress_group = QGroupBox("Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("En attente...")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # Section de résultats
        self.results_group = QGroupBox("Résultats")
        self.results_group.setVisible(False)
        results_layout = QVBoxLayout(self.results_group)
        
        # Onglets de résultats
        results_tabs = QTabWidget()
        
        # Onglet de résumé
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        
        # Graphiques
        charts_layout = QHBoxLayout()
        
        # Graphique de répartition des menaces
        self.threat_chart_view = QChartView()
        self.threat_chart_view.setRenderHint(QPainter.Antialiasing)
        
        # Graphique de scores
        self.score_chart_view = QChartView()
        self.score_chart_view.setRenderHint(QPainter.Antialiasing)
        
        charts_layout.addWidget(self.threat_chart_view)
        charts_layout.addWidget(self.score_chart_view)
        
        summary_layout.addLayout(charts_layout)
        summary_layout.addWidget(self.summary_text)
        
        # Onglet de menaces
        threats_tab = QWidget()
        threats_layout = QVBoxLayout(threats_tab)
        
        self.threats_table = QTableWidget()
        self.threats_table.setColumnCount(5)
        self.threats_table.setHorizontalHeaderLabels(["Type", "Nom", "Sévérité", "Score", "Description"])
        self.threats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        threats_layout.addWidget(self.threats_table)
        
        # Onglet d'indicateurs
        indicators_tab = QWidget()
        indicators_layout = QVBoxLayout(indicators_tab)
        
        self.indicators_table = QTableWidget()
        self.indicators_table.setColumnCount(4)
        self.indicators_table.setHorizontalHeaderLabels(["Type", "Valeur", "Confiance", "Description"])
        self.indicators_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        indicators_layout.addWidget(self.indicators_table)
        
        # Onglet de détails
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        
        details_layout.addWidget(self.details_text)
        
        # Ajout des onglets
        results_tabs.addTab(summary_tab, "Résumé")
        results_tabs.addTab(threats_tab, "Menaces")
        results_tabs.addTab(indicators_tab, "Indicateurs")
        results_tabs.addTab(details_tab, "Détails")
        
        results_layout.addWidget(results_tabs)
        
        # Boutons de rapport
        report_layout = QHBoxLayout()
        
        self.generate_report_button = QPushButton("Générer un rapport HTML")
        self.generate_report_button.setStyleSheet("background-color: #3498db; color: white;")
        
        self.export_csv_button = QPushButton("Exporter en CSV")
        
        report_layout.addWidget(self.generate_report_button)
        report_layout.addWidget(self.export_csv_button)
        
        results_layout.addLayout(report_layout)
        
        # Assemblage de l'onglet
        top_layout = QHBoxLayout()
        top_layout.addWidget(file_group, 2)
        top_layout.addWidget(options_group, 1)
        
        layout.addLayout(top_layout)
        layout.addLayout(control_layout)
        layout.addWidget(progress_group)
        layout.addWidget(self.results_group)
    
    def setup_xql_tab(self):
        """Configuration de l'onglet de requêtes XQL"""
        layout = QVBoxLayout(self.xql_tab)
        
        # Section de requête
        query_group = QGroupBox("Requête XQL")
        query_layout = QVBoxLayout(query_group)
        
        self.xql_editor = QTextEdit()
        self.xql_editor.setPlaceholderText("Entrez votre requête XQL ici...\nExemple: dataset=xdr_data | filter event_type='PROCESS' | limit 100")
        self.xql_editor.setMinimumHeight(150)
        
        query_controls = QHBoxLayout()
        
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["Dernières 24 heures", "7 derniers jours", "30 derniers jours"])
        
        self.execute_query_button = QPushButton("Exécuter la requête")
        self.execute_query_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        query_controls.addWidget(QLabel("Période:"))
        query_controls.addWidget(self.timeframe_combo)
        query_controls.addStretch()
        query_controls.addWidget(self.execute_query_button)
        
        query_layout.addWidget(self.xql_editor)
        query_layout.addLayout(query_controls)
        
        # Section de résultats
        results_group = QGroupBox("Résultats")
        results_layout = QVBoxLayout(results_group)
        
        self.xql_results_table = QTableWidget()
        self.xql_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        results_info = QHBoxLayout()
        self.xql_results_count = QLabel("0 résultats")
        self.xql_export_button = QPushButton("Exporter les résultats")
        
        results_info.addWidget(self.xql_results_count)
        results_info.addStretch()
        results_info.addWidget(self.xql_export_button)
        
        results_layout.addLayout(results_info)
        results_layout.addWidget(self.xql_results_table)
        
        # Exemples de requêtes
        examples_group = QGroupBox("Exemples de requêtes")
        examples_layout = QVBoxLayout(examples_group)
        
        self.examples_list = QListWidget()
        examples = [
            "Processus PowerShell suspects",
            "Connexions réseau vers des domaines suspects",
            "Fichiers créés dans des dossiers sensibles",
            "Exécutables lancés depuis des dossiers temporaires",
            "Activité de compte utilisateur en dehors des heures normales"
        ]
        self.examples_list.addItems(examples)
        
        examples_layout.addWidget(self.examples_list)
        
        # Assemblage de l'onglet
        layout.addWidget(query_group)
        layout.addWidget(results_group)
        layout.addWidget(examples_group)
    
    def setup_incidents_tab(self):
        """Configuration de l'onglet d'incidents et alertes"""
        layout = QVBoxLayout(self.incidents_tab)
        
        # Onglets internes
        incidents_tabs = QTabWidget()
        
        # Onglet d'alertes
        alerts_tab = QWidget()
        alerts_layout = QVBoxLayout(alerts_tab)
        
        alerts_controls = QHBoxLayout()
        
        self.alerts_timeframe_combo = QComboBox()
        self.alerts_timeframe_combo.addItems(["Dernières 24 heures", "7 derniers jours", "30 derniers jours"])
        
        self.alerts_limit_combo = QComboBox()
        self.alerts_limit_combo.addItems(["10", "50", "100", "200"])
        self.alerts_limit_combo.setCurrentIndex(1)  # 50 par défaut
        
        self.get_alerts_button = QPushButton("Récupérer les alertes")
        self.get_alerts_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        alerts_controls.addWidget(QLabel("Période:"))
        alerts_controls.addWidget(self.alerts_timeframe_combo)
        alerts_controls.addWidget(QLabel("Limite:"))
        alerts_controls.addWidget(self.alerts_limit_combo)
        alerts_controls.addStretch()
        alerts_controls.addWidget(self.get_alerts_button)
        
        self.alerts_table = QTableWidget()
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels(["ID", "Nom", "Catégorie", "Sévérité", "Hôte", "Date de détection"])
        self.alerts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        alerts_layout.addLayout(alerts_controls)
        alerts_layout.addWidget(self.alerts_table)
        
        # Onglet d'endpoints
        endpoints_tab = QWidget()
        endpoints_layout = QVBoxLayout(endpoints_tab)
        
        endpoints_controls = QHBoxLayout()
        
        self.get_endpoints_button = QPushButton("Récupérer les endpoints")
        self.get_endpoints_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        endpoints_controls.addStretch()
        endpoints_controls.addWidget(self.get_endpoints_button)
        
        self.endpoints_table = QTableWidget()
        self.endpoints_table.setColumnCount(6)
        self.endpoints_table.setHorizontalHeaderLabels(["ID", "Nom", "Type", "Statut", "OS", "IP"])
        self.endpoints_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        endpoints_layout.addLayout(endpoints_controls)
        endpoints_layout.addWidget(self.endpoints_table)
        
        # Ajout des onglets
        incidents_tabs.addTab(alerts_tab, "Alertes")
        incidents_tabs.addTab(endpoints_tab, "Endpoints")
        
        layout.addWidget(incidents_tabs)
    
    def setup_config_tab(self):
        """Configuration de l'onglet de configuration"""
        layout = QVBoxLayout(self.config_tab)
        
        # Section Cortex XDR
        cortex_group = QGroupBox("Configuration Cortex XDR")
        cortex_layout = QFormLayout(cortex_group)
        
        self.cortex_url_input = QLineEdit()
        self.cortex_url_input.setPlaceholderText("https://api.xdr.paloaltonetworks.com")
        
        self.cortex_api_key_input = QLineEdit()
        self.cortex_api_key_input.setEchoMode(QLineEdit.Password)
        
        self.cortex_api_key_id_input = QLineEdit()
        
        self.cortex_tenant_id_input = QLineEdit()
        
        self.cortex_advanced_api_checkbox = QCheckBox("Utiliser l'API avancée")
        
        cortex_layout.addRow("URL de base:", self.cortex_url_input)
        cortex_layout.addRow("API Key:", self.cortex_api_key_input)
        cortex_layout.addRow("API Key ID:", self.cortex_api_key_id_input)
        cortex_layout.addRow("Tenant ID:", self.cortex_tenant_id_input)
        cortex_layout.addRow("", self.cortex_advanced_api_checkbox)
        
        cortex_buttons = QHBoxLayout()
        self.test_cortex_button = QPushButton("Tester la connexion")
        self.save_cortex_button = QPushButton("Enregistrer")
        self.save_cortex_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        cortex_buttons.addWidget(self.test_cortex_button)
        cortex_buttons.addWidget(self.save_cortex_button)
        
        cortex_layout.addRow("", cortex_buttons)
        
        # Section YARA
        yara_group = QGroupBox("Configuration YARA")
        yara_layout = QFormLayout(yara_group)
        
        self.yara_rules_dir_input = QLineEdit()
        self.yara_rules_dir_input.setReadOnly(True)
        
        yara_dir_layout = QHBoxLayout()
        yara_dir_layout.addWidget(self.yara_rules_dir_input)
        self.browse_yara_dir_button = QPushButton("Parcourir")
        yara_dir_layout.addWidget(self.browse_yara_dir_button)
        
        self.reload_yara_rules_button = QPushButton("Recharger les règles")
        
        yara_layout.addRow("Répertoire des règles:", yara_dir_layout)
        yara_layout.addRow("", self.reload_yara_rules_button)
        
        # Section Interface
        ui_group = QGroupBox("Interface utilisateur")
        ui_layout = QFormLayout(ui_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Français", "English"])
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Clair", "Sombre", "Système"])
        
        ui_layout.addRow("Langue:", self.language_combo)
        ui_layout.addRow("Thème:", self.theme_combo)
        
        # Assemblage de l'onglet
        layout.addWidget(cortex_group)
        layout.addWidget(yara_group)
        layout.addWidget(ui_group)
        
        # Bouton de sauvegarde global
        save_layout = QHBoxLayout()
        self.save_config_button = QPushButton("Enregistrer toutes les configurations")
        self.save_config_button.setMinimumHeight(40)
        self.save_config_button.setStyleSheet("background-color: #2c3e50; color: white;")
        
        save_layout.addStretch()
        save_layout.addWidget(self.save_config_button)
        
        layout.addLayout(save_layout)
    
    def connect_signals(self):
        """Connexion des signaux aux slots"""
        # Onglet d'analyse
        self.select_file_button.clicked.connect(self.select_files)
        self.select_dir_button.clicked.connect(self.select_directory)
        self.clear_selection_button.clicked.connect(self.clear_file_selection)
        self.start_analysis_button.clicked.connect(self.start_analysis)
        self.stop_analysis_button.clicked.connect(self.stop_analysis)
        self.generate_report_button.clicked.connect(self.generate_report)
        self.export_csv_button.clicked.connect(self.export_csv)
        self.threats_table.itemClicked.connect(self.show_threat_details)
        
        # Onglet XQL
        self.execute_query_button.clicked.connect(self.execute_xql_query)
        self.xql_export_button.clicked.connect(self.export_xql_results)
        self.examples_list.itemClicked.connect(self.load_xql_example)
        
        # Onglet Incidents & Alertes
        self.get_alerts_button.clicked.connect(self.get_alerts)
        self.get_endpoints_button.clicked.connect(self.get_endpoints)
        
        # Onglet Configuration
        self.test_cortex_button.clicked.connect(self.test_cortex_connection)
        self.save_cortex_button.clicked.connect(self.save_cortex_config)
        self.browse_yara_dir_button.clicked.connect(self.browse_yara_directory)
        self.reload_yara_rules_button.clicked.connect(self.reload_yara_rules)
        self.save_config_button.clicked.connect(self.save_all_config)
        self.theme_combo.currentIndexChanged.connect(self.apply_theme)
    
    def load_config(self):
        """Chargement des configurations"""
        # Chargement de la configuration Cortex XDR
        cortex_config = self.config_manager.get_cortex_config()
        
        self.cortex_url_input.setText(cortex_config.get("base_url", "https://api.xdr.paloaltonetworks.com"))
        self.cortex_api_key_input.setText(cortex_config.get("api_key", ""))
        self.cortex_api_key_id_input.setText(cortex_config.get("api_key_id", ""))
        self.cortex_tenant_id_input.setText(cortex_config.get("tenant_id", ""))
        self.cortex_advanced_api_checkbox.setChecked(cortex_config.get("advanced_api", True))
        
        # Chargement de la configuration YARA
        yara_config = self.config_manager.get_yara_config()
        
        rules_dir = yara_config.get("rules_dir", os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules"))
        self.yara_rules_dir_input.setText(rules_dir)
        
        # Chargement de la configuration UI
        ui_config = self.config_manager.get_ui_config()
        
        language = ui_config.get("language", "fr")
        self.language_combo.setCurrentIndex(0 if language == "fr" else 1)
        
        theme = ui_config.get("theme", "system")
        if theme == "light":
            self.theme_combo.setCurrentIndex(0)
        elif theme == "dark":
            self.theme_combo.setCurrentIndex(1)
        else:
            self.theme_combo.setCurrentIndex(2)
        
        # Application du thème
        self.apply_theme()
    
    def apply_theme(self):
        """Application du thème sélectionné"""
        theme_index = self.theme_combo.currentIndex()
        
        if theme_index == 0:  # Clair
            QApplication.setStyle("Fusion")
            palette = QPalette()
            QApplication.setPalette(palette)
        elif theme_index == 1:  # Sombre
            QApplication.setStyle("Fusion")
            palette = QPalette()
            palette.setColor(QPalette.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(25, 25, 25))
            palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ToolTipBase, Qt.white)
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.HighlightedText, Qt.black)
            QApplication.setPalette(palette)
        else:  # Système
            QApplication.setStyle("")
            QApplication.setPalette(QApplication.style().standardPalette())
    
    def select_files(self):
        """Sélection de fichiers à analyser"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Sélectionner des fichiers", "", "Tous les fichiers (*.*)"
        )
        
        if files:
            self.selected_files.extend(files)
            self.update_file_list()
    
    def select_directory(self):
        """Sélection d'un dossier à analyser"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner un dossier", ""
        )
        
        if directory:
            for root, _, files in os.walk(directory):
                for file in files:
                    self.selected_files.append(os.path.join(root, file))
            
            self.update_file_list()
    
    def clear_file_selection(self):
        """Effacement de la sélection de fichiers"""
        self.selected_files = []
        self.update_file_list()
    
    def update_file_list(self):
        """Mise à jour de la liste des fichiers sélectionnés"""
        self.file_list.clear()
        
        for file_path in self.selected_files:
            item = QListWidgetItem(os.path.basename(file_path))
            item.setToolTip(file_path)
            self.file_list.addItem(item)
    
    def start_analysis(self):
        """Démarrage de l'analyse"""
        if not self.selected_files:
            QMessageBox.warning(self, "Aucun fichier sélectionné", 
                               "Veuillez sélectionner au moins un fichier à analyser.")
            return
        
        # Préparation des options d'analyse
        options = {
            "use_yara": self.use_yara_checkbox.isChecked(),
            "use_cortex": self.use_cortex_checkbox.isChecked(),
            "detect_ransomware": self.detect_ransomware_checkbox.isChecked(),
            "detect_backdoors": self.detect_backdoors_checkbox.isChecked(),
            "detect_phishing": self.detect_phishing_checkbox.isChecked(),
            "correlate": self.correlate_checkbox.isChecked()
        }
        
        # Mise à jour de l'interface
        self.start_analysis_button.setEnabled(False)
        self.stop_analysis_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Initialisation de l'analyse...")
        self.results_group.setVisible(False)
        
        # Création et démarrage du thread d'analyse
        self.analysis_thread = WorkerThread(self.analyzer, self.selected_files, options)
        self.analysis_thread.update_progress.connect(self.update_analysis_progress)
        self.analysis_thread.analysis_complete.connect(self.analysis_completed)
        self.analysis_thread.error_occurred.connect(self.analysis_error)
        self.analysis_thread.start()
    
    def stop_analysis(self):
        """Arrêt de l'analyse"""
        if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
            self.analysis_thread.terminate()
            self.analysis_thread.wait()
            
            self.progress_label.setText("Analyse arrêtée par l'utilisateur")
            self.start_analysis_button.setEnabled(True)
            self.stop_analysis_button.setEnabled(False)
    
    def update_analysis_progress(self, progress, status):
        """Mise à jour de la progression de l'analyse"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(status)
    
    def analysis_completed(self, results):
        """Traitement des résultats de l'analyse"""
        self.analysis_results = results
        
        # Mise à jour de l'interface
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        self.results_group.setVisible(True)
        
        # Mise à jour du résumé
        self.update_summary()
        
        # Mise à jour des tableaux
        self.update_threats_table()
        self.update_indicators_table()
        
        # Mise à jour des graphiques
        self.update_charts()
    
    def analysis_error(self, error_message):
        """Gestion des erreurs d'analyse"""
        self.start_analysis_button.setEnabled(True)
        self.stop_analysis_button.setEnabled(False)
        
        QMessageBox.critical(self, "Erreur d'analyse", error_message)
    
    def update_summary(self):
        """Mise à jour du résumé des résultats"""
        if not self.analysis_results:
            return
        
        summary = self.analysis_results.get("summary", {})
        
        # Création du texte de résumé
        summary_html = "<h2>Résumé de l'analyse</h2>"
        summary_html += f"<p><b>Fichiers analysés:</b> {len(self.analysis_results.get('files', []))}</p>"
        summary_html += f"<p><b>Menaces détectées:</b> {len(self.analysis_results.get('threats', []))}</p>"
        summary_html += f"<p><b>Indicateurs identifiés:</b> {len(self.analysis_results.get('indicators', []))}</p>"
        
        if "score" in summary:
            score = summary["score"]
            score_text = ""
            score_color = ""
            
            if score >= 8:
                score_text = "Critique"
                score_color = "#e74c3c"
            elif score >= 6:
                score_text = "Élevé"
                score_color = "#e67e22"
            elif score >= 4:
                score_text = "Moyen"
                score_color = "#f1c40f"
            elif score >= 2:
                score_text = "Faible"
                score_color = "#2ecc71"
            else:
                score_text = "Info"
                score_color = "#3498db"
            
            summary_html += f"<p><b>Score global:</b> <span style='color: {score_color};'>{score} - {score_text}</span></p>"
        
        if "categories" in summary:
            summary_html += "<h3>Catégories de menaces</h3><ul>"
            for category, count in summary["categories"].items():
                summary_html += f"<li>{category}: {count}</li>"
            summary_html += "</ul>"
        
        self.summary_text.setHtml(summary_html)
    
    def update_threats_table(self):
        """Mise à jour du tableau des menaces"""
        if not self.analysis_results:
            return
        
        threats = self.analysis_results.get("threats", [])
        
        self.threats_table.setRowCount(len(threats))
        
        for i, threat in enumerate(threats):
            # Type
            type_item = QTableWidgetItem(threat.get("type", ""))
            self.threats_table.setItem(i, 0, type_item)
            
            # Nom
            name_item = QTableWidgetItem(threat.get("name", ""))
            self.threats_table.setItem(i, 1, name_item)
            
            # Sévérité
            severity = threat.get("severity", "")
            severity_item = QTableWidgetItem(severity)
            
            # Coloration selon la sévérité
            if severity == "critical":
                severity_item.setBackground(QColor("#e74c3c"))
                severity_item.setForeground(QColor("white"))
            elif severity == "high":
                severity_item.setBackground(QColor("#e67e22"))
                severity_item.setForeground(QColor("white"))
            elif severity == "medium":
                severity_item.setBackground(QColor("#f1c40f"))
            elif severity == "low":
                severity_item.setBackground(QColor("#2ecc71"))
                severity_item.setForeground(QColor("white"))
            
            self.threats_table.setItem(i, 2, severity_item)
            
            # Score
            score_item = QTableWidgetItem(str(threat.get("score", 0)))
            self.threats_table.setItem(i, 3, score_item)
            
            # Description
            description_item = QTableWidgetItem(threat.get("description", ""))
            self.threats_table.setItem(i, 4, description_item)
    
    def update_indicators_table(self):
        """Mise à jour du tableau des indicateurs"""
        if not self.analysis_results:
            return
        
        indicators = self.analysis_results.get("indicators", [])
        
        self.indicators_table.setRowCount(len(indicators))
        
        for i, indicator in enumerate(indicators):
            # Type
            type_item = QTableWidgetItem(indicator.get("type", ""))
            self.indicators_table.setItem(i, 0, type_item)
            
            # Valeur
            value_item = QTableWidgetItem(indicator.get("value", ""))
            self.indicators_table.setItem(i, 1, value_item)
            
            # Confiance
            confidence = indicator.get("confidence", "")
            confidence_item = QTableWidgetItem(confidence)
            
            # Coloration selon la confiance
            if confidence == "high":
                confidence_item.setBackground(QColor("#2ecc71"))
                confidence_item.setForeground(QColor("white"))
            elif confidence == "medium":
                confidence_item.setBackground(QColor("#f1c40f"))
            elif confidence == "low":
                confidence_item.setBackground(QColor("#e67e22"))
                confidence_item.setForeground(QColor("white"))
            
            self.indicators_table.setItem(i, 2, confidence_item)
            
            # Description
            description_item = QTableWidgetItem(indicator.get("description", ""))
            self.indicators_table.setItem(i, 3, description_item)
    
    def update_charts(self):
        """Mise à jour des graphiques"""
        if not self.analysis_results:
            return
        
        # Graphique de répartition des menaces
        threat_chart = QChart()
        threat_chart.setTitle("Répartition des menaces par type")
        threat_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Création de la série
        threat_series = QPieSeries()
        
        # Comptage des types de menaces
        threat_types = {}
        for threat in self.analysis_results.get("threats", []):
            threat_type = threat.get("type", "unknown")
            if threat_type in threat_types:
                threat_types[threat_type] += 1
            else:
                threat_types[threat_type] = 1
        
        # Ajout des données
        for threat_type, count in threat_types.items():
            slice = threat_series.append(threat_type, count)
            slice.setLabelVisible(True)
        
        threat_chart.addSeries(threat_series)
        threat_chart.legend().setVisible(True)
        threat_chart.legend().setAlignment(Qt.AlignBottom)
        
        self.threat_chart_view.setChart(threat_chart)
        
        # Graphique des scores
        score_chart = QChart()
        score_chart.setTitle("Répartition des menaces par score")
        score_chart.setAnimationOptions(QChart.SeriesAnimations)
        
        # Création de la série
        score_set = QBarSet("Nombre de menaces")
        
        # Comptage des scores
        scores = [0, 0, 0, 0, 0]  # 0-2, 2-4, 4-6, 6-8, 8-10
        for threat in self.analysis_results.get("threats", []):
            score = threat.get("score", 0)
            if score >= 8:
                scores[4] += 1
            elif score >= 6:
                scores[3] += 1
            elif score >= 4:
                scores[2] += 1
            elif score >= 2:
                scores[1] += 1
            else:
                scores[0] += 1
        
        score_set.append(scores)
        
        score_series = QBarSeries()
        score_series.append(score_set)
        
        score_chart.addSeries(score_series)
        
        categories = ["Info (0-2)", "Faible (2-4)", "Moyen (4-6)", "Élevé (6-8)", "Critique (8-10)"]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        score_chart.addAxis(axis_x, Qt.AlignBottom)
        score_series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setRange(0, max(scores) + 1)
        score_chart.addAxis(axis_y, Qt.AlignLeft)
        score_series.attachAxis(axis_y)
        
        score_chart.legend().setVisible(True)
        score_chart.legend().setAlignment(Qt.AlignBottom)
        
        self.score_chart_view.setChart(score_chart)
    
    def show_threat_details(self, item):
        """Affichage des détails d'une menace"""
        if not self.analysis_results:
            return
        
        row = item.row()
        threats = self.analysis_results.get("threats", [])
        
        if row < 0 or row >= len(threats):
            return
        
        threat = threats[row]
        
        # Création du texte de détails
        details_html = f"<h2>{threat.get('name', 'Menace inconnue')}</h2>"
        details_html += f"<p><b>Type:</b> {threat.get('type', '')}</p>"
        details_html += f"<p><b>Sévérité:</b> {threat.get('severity', '')}</p>"
        details_html += f"<p><b>Score:</b> {threat.get('score', 0)}</p>"
        details_html += f"<p><b>Description:</b> {threat.get('description', '')}</p>"
        
        # Détails spécifiques
        details = threat.get("details", {})
        if details:
            details_html += "<h3>Détails techniques</h3>"
            details_html += "<pre>" + json.dumps(details, indent=2) + "</pre>"
        
        # Correspondances YARA
        if "strings" in threat:
            details_html += "<h3>Correspondances YARA</h3><ul>"
            for offset, identifier, string in threat["strings"]:
                details_html += f"<li>0x{offset:x}: {identifier} = {string.decode('utf-8', errors='replace')}</li>"
            details_html += "</ul>"
        
        # Corrélations Cortex XDR
        if "xdr_correlations" in threat and threat["xdr_correlations"]:
            details_html += "<h3>Corrélations Cortex XDR</h3>"
            details_html += "<pre>" + json.dumps(threat["xdr_correlations"], indent=2) + "</pre>"
        
        self.details_text.setHtml(details_html)
    
    def generate_report(self):
        """Génération d'un rapport HTML"""
        if not self.analysis_results:
            QMessageBox.warning(self, "Aucun résultat", 
                               "Aucun résultat d'analyse disponible pour générer un rapport.")
            return
        
        # Sélection du dossier de destination
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport", "", "Fichiers HTML (*.html)"
        )
        
        if not save_path:
            return
        
        try:
            # Génération du rapport
            self.report_generator.generate_html_report(self.analysis_results, save_path)
            
            QMessageBox.information(self, "Rapport généré", 
                                  f"Le rapport a été généré avec succès:\n{save_path}")
            
            # Ouverture du rapport dans le navigateur
            if QMessageBox.question(self, "Ouvrir le rapport", 
                                  "Voulez-vous ouvrir le rapport dans votre navigateur?",
                                  QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                import webbrowser
                webbrowser.open(f"file://{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de la génération du rapport:\n{str(e)}")
    
    def export_csv(self):
        """Exportation des résultats en CSV"""
        if not self.analysis_results:
            QMessageBox.warning(self, "Aucun résultat", 
                               "Aucun résultat d'analyse disponible pour exporter.")
            return
        
        # Sélection du dossier de destination
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer les résultats", "", "Fichiers CSV (*.csv)"
        )
        
        if not save_path:
            return
        
        try:
            # Exportation des menaces
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.writer(f)
                
                # En-tête
                writer.writerow(["Type", "Nom", "Sévérité", "Score", "Description"])
                
                # Données
                for threat in self.analysis_results.get("threats", []):
                    writer.writerow([
                        threat.get("type", ""),
                        threat.get("name", ""),
                        threat.get("severity", ""),
                        threat.get("score", 0),
                        threat.get("description", "")
                    ])
            
            QMessageBox.information(self, "Export réussi", 
                                  f"Les résultats ont été exportés avec succès:\n{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de l'exportation des résultats:\n{str(e)}")
    
    def execute_xql_query(self):
        """Exécution d'une requête XQL"""
        query = self.xql_editor.toPlainText().strip()
        
        if not query:
            QMessageBox.warning(self, "Requête vide", 
                               "Veuillez entrer une requête XQL.")
            return
        
        # Détermination de la période
        timeframe_index = self.timeframe_combo.currentIndex()
        timeframe = "last_24_hours"
        if timeframe_index == 1:
            timeframe = "last_7_days"
        elif timeframe_index == 2:
            timeframe = "last_30_days"
        
        # Mise à jour de l'interface
        self.execute_query_button.setEnabled(False)
        self.statusBar().showMessage("Exécution de la requête XQL...")
        
        # Création et démarrage du thread de requête
        self.xql_thread = XQLQueryThread(self.cortex_client, query, timeframe)
        self.xql_thread.query_complete.connect(self.xql_query_completed)
        self.xql_thread.error_occurred.connect(self.xql_query_error)
        self.xql_thread.start()
    
    def xql_query_completed(self, results):
        """Traitement des résultats de la requête XQL"""
        self.current_xql_results = results
        
        # Mise à jour de l'interface
        self.execute_query_button.setEnabled(True)
        self.statusBar().showMessage("Requête XQL terminée")
        
        # Mise à jour du compteur de résultats
        result_count = len(results.get("results", []))
        self.xql_results_count.setText(f"{result_count} résultats")
        
        # Mise à jour du tableau
        self.update_xql_results_table()
    
    def xql_query_error(self, error_message):
        """Gestion des erreurs de requête XQL"""
        self.execute_query_button.setEnabled(True)
        self.statusBar().showMessage("Erreur lors de l'exécution de la requête XQL")
        
        QMessageBox.critical(self, "Erreur de requête XQL", error_message)
    
    def update_xql_results_table(self):
        """Mise à jour du tableau des résultats XQL"""
        if not self.current_xql_results:
            return
        
        results = self.current_xql_results.get("results", [])
        
        if not results:
            self.xql_results_table.setRowCount(0)
            self.xql_results_table.setColumnCount(0)
            return
        
        # Détermination des colonnes
        columns = set()
        for result in results:
            columns.update(result.keys())
        
        columns = sorted(list(columns))
        
        # Configuration du tableau
        self.xql_results_table.setRowCount(len(results))
        self.xql_results_table.setColumnCount(len(columns))
        self.xql_results_table.setHorizontalHeaderLabels(columns)
        
        # Remplissage du tableau
        for i, result in enumerate(results):
            for j, column in enumerate(columns):
                value = result.get(column, "")
                if isinstance(value, dict) or isinstance(value, list):
                    value = json.dumps(value)
                
                item = QTableWidgetItem(str(value))
                self.xql_results_table.setItem(i, j, item)
    
    def export_xql_results(self):
        """Exportation des résultats XQL en CSV"""
        if not self.current_xql_results:
            QMessageBox.warning(self, "Aucun résultat", 
                               "Aucun résultat de requête XQL disponible pour exporter.")
            return
        
        # Sélection du dossier de destination
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer les résultats XQL", "", "Fichiers CSV (*.csv)"
        )
        
        if not save_path:
            return
        
        try:
            results = self.current_xql_results.get("results", [])
            
            if not results:
                QMessageBox.warning(self, "Aucun résultat", 
                                   "Aucun résultat à exporter.")
                return
            
            # Détermination des colonnes
            columns = set()
            for result in results:
                columns.update(result.keys())
            
            columns = sorted(list(columns))
            
            # Exportation des résultats
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                import csv
                writer = csv.writer(f)
                
                # En-tête
                writer.writerow(columns)
                
                # Données
                for result in results:
                    row = []
                    for column in columns:
                        value = result.get(column, "")
                        if isinstance(value, dict) or isinstance(value, list):
                            value = json.dumps(value)
                        row.append(value)
                    
                    writer.writerow(row)
            
            QMessageBox.information(self, "Export réussi", 
                                  f"Les résultats XQL ont été exportés avec succès:\n{save_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors de l'exportation des résultats XQL:\n{str(e)}")
    
    def load_xql_example(self, item):
        """Chargement d'un exemple de requête XQL"""
        example_text = item.text()
        
        if example_text == "Processus PowerShell suspects":
            query = "dataset=xdr_data | filter event_type=\"PROCESS\" AND process_name=\"powershell.exe\" AND command_line CONTAINS \"-enc\" | limit 100"
        elif example_text == "Connexions réseau vers des domaines suspects":
            query = "dataset=xdr_data | filter event_type=\"NETWORK\" AND (dst_domain CONTAINS \"pastebin\" OR dst_domain CONTAINS \"paste.ee\" OR dst_domain CONTAINS \"github.io\") | limit 100"
        elif example_text == "Fichiers créés dans des dossiers sensibles":
            query = "dataset=xdr_data | filter event_type=\"FILE\" AND action_type=\"CREATION\" AND (file_path CONTAINS \"\\Windows\\Temp\\\" OR file_path CONTAINS \"\\Windows\\System32\\Tasks\\\" OR file_path CONTAINS \"\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\\") | limit 100"
        elif example_text == "Exécutables lancés depuis des dossiers temporaires":
            query = "dataset=xdr_data | filter event_type=\"PROCESS\" AND (process_path CONTAINS \"\\Temp\\\" OR process_path CONTAINS \"\\Downloads\\\" OR process_path CONTAINS \"\\AppData\\Local\\Temp\\\") AND process_path CONTAINS \".exe\" | limit 100"
        elif example_text == "Activité de compte utilisateur en dehors des heures normales":
            query = "dataset=xdr_data | filter event_type=\"AUTHENTICATION\" AND (timestamp.hour < 8 OR timestamp.hour > 18) | limit 100"
        else:
            return
        
        self.xql_editor.setPlainText(query)
    
    def get_alerts(self):
        """Récupération des alertes Cortex XDR"""
        # Détermination de la période
        timeframe_index = self.alerts_timeframe_combo.currentIndex()
        timeframe = "last_24_hours"
        if timeframe_index == 1:
            timeframe = "last_7_days"
        elif timeframe_index == 2:
            timeframe = "last_30_days"
        
        # Détermination de la limite
        limit = int(self.alerts_limit_combo.currentText())
        
        # Mise à jour de l'interface
        self.get_alerts_button.setEnabled(False)
        self.statusBar().showMessage("Récupération des alertes Cortex XDR...")
        
        # Création et démarrage du thread d'alertes
        self.alerts_thread = AlertsThread(self.cortex_client, timeframe, limit)
        self.alerts_thread.alerts_complete.connect(self.alerts_completed)
        self.alerts_thread.error_occurred.connect(self.alerts_error)
        self.alerts_thread.start()
    
    def alerts_completed(self, alerts):
        """Traitement des alertes récupérées"""
        self.current_alerts = alerts
        
        # Mise à jour de l'interface
        self.get_alerts_button.setEnabled(True)
        self.statusBar().showMessage(f"{len(alerts)} alertes récupérées")
        
        # Mise à jour du tableau
        self.alerts_table.setRowCount(len(alerts))
        
        for i, alert in enumerate(alerts):
            # ID
            id_item = QTableWidgetItem(alert.get("alert_id", ""))
            self.alerts_table.setItem(i, 0, id_item)
            
            # Nom
            name_item = QTableWidgetItem(alert.get("name", ""))
            self.alerts_table.setItem(i, 1, name_item)
            
            # Catégorie
            category_item = QTableWidgetItem(alert.get("category", ""))
            self.alerts_table.setItem(i, 2, category_item)
            
            # Sévérité
            severity = alert.get("severity", "")
            severity_item = QTableWidgetItem(severity)
            
            # Coloration selon la sévérité
            if severity == "critical":
                severity_item.setBackground(QColor("#e74c3c"))
                severity_item.setForeground(QColor("white"))
            elif severity == "high":
                severity_item.setBackground(QColor("#e67e22"))
                severity_item.setForeground(QColor("white"))
            elif severity == "medium":
                severity_item.setBackground(QColor("#f1c40f"))
            elif severity == "low":
                severity_item.setBackground(QColor("#2ecc71"))
                severity_item.setForeground(QColor("white"))
            
            self.alerts_table.setItem(i, 3, severity_item)
            
            # Hôte
            host = alert.get("host", {})
            host_name = host.get("hostname", "") if host else ""
            host_item = QTableWidgetItem(host_name)
            self.alerts_table.setItem(i, 4, host_item)
            
            # Date de détection
            detection_time = alert.get("detection_timestamp", "")
            detection_item = QTableWidgetItem(detection_time)
            self.alerts_table.setItem(i, 5, detection_item)
    
    def alerts_error(self, error_message):
        """Gestion des erreurs de récupération d'alertes"""
        self.get_alerts_button.setEnabled(True)
        self.statusBar().showMessage("Erreur lors de la récupération des alertes")
        
        QMessageBox.critical(self, "Erreur de récupération d'alertes", error_message)
    
    def get_endpoints(self):
        """Récupération des endpoints Cortex XDR"""
        # Mise à jour de l'interface
        self.get_endpoints_button.setEnabled(False)
        self.statusBar().showMessage("Récupération des endpoints Cortex XDR...")
        
        # Création et démarrage du thread d'endpoints
        self.endpoints_thread = EndpointsThread(self.cortex_client)
        self.endpoints_thread.endpoints_complete.connect(self.endpoints_completed)
        self.endpoints_thread.error_occurred.connect(self.endpoints_error)
        self.endpoints_thread.start()
    
    def endpoints_completed(self, endpoints):
        """Traitement des endpoints récupérés"""
        self.current_endpoints = endpoints
        
        # Mise à jour de l'interface
        self.get_endpoints_button.setEnabled(True)
        self.statusBar().showMessage(f"{len(endpoints)} endpoints récupérés")
        
        # Mise à jour du tableau
        self.endpoints_table.setRowCount(len(endpoints))
        
        for i, endpoint in enumerate(endpoints):
            # ID
            id_item = QTableWidgetItem(endpoint.get("endpoint_id", ""))
            self.endpoints_table.setItem(i, 0, id_item)
            
            # Nom
            name_item = QTableWidgetItem(endpoint.get("endpoint_name", ""))
            self.endpoints_table.setItem(i, 1, name_item)
            
            # Type
            type_item = QTableWidgetItem(endpoint.get("endpoint_type", ""))
            self.endpoints_table.setItem(i, 2, type_item)
            
            # Statut
            status = endpoint.get("endpoint_status", "")
            status_item = QTableWidgetItem(status)
            
            # Coloration selon le statut
            if status == "connected":
                status_item.setBackground(QColor("#2ecc71"))
                status_item.setForeground(QColor("white"))
            elif status == "disconnected":
                status_item.setBackground(QColor("#e74c3c"))
                status_item.setForeground(QColor("white"))
            
            self.endpoints_table.setItem(i, 3, status_item)
            
            # OS
            os_item = QTableWidgetItem(endpoint.get("os_type", ""))
            self.endpoints_table.setItem(i, 4, os_item)
            
            # IP
            ip_item = QTableWidgetItem(endpoint.get("ip", ""))
            self.endpoints_table.setItem(i, 5, ip_item)
    
    def endpoints_error(self, error_message):
        """Gestion des erreurs de récupération d'endpoints"""
        self.get_endpoints_button.setEnabled(True)
        self.statusBar().showMessage("Erreur lors de la récupération des endpoints")
        
        QMessageBox.critical(self, "Erreur de récupération d'endpoints", error_message)
    
    def test_cortex_connection(self):
        """Test de la connexion Cortex XDR"""
        # Récupération des paramètres
        base_url = self.cortex_url_input.text()
        api_key = self.cortex_api_key_input.text()
        api_key_id = self.cortex_api_key_id_input.text()
        tenant_id = self.cortex_tenant_id_input.text()
        
        if not base_url or not api_key or not api_key_id:
            QMessageBox.warning(self, "Paramètres incomplets", 
                               "Veuillez remplir au moins l'URL de base, l'API Key et l'API Key ID.")
            return
        
        # Mise à jour de l'interface
        self.test_cortex_button.setEnabled(False)
        self.statusBar().showMessage("Test de la connexion Cortex XDR...")
        
        # Création d'un client temporaire
        config = {
            "base_url": base_url,
            "api_key": api_key,
            "api_key_id": api_key_id,
            "tenant_id": tenant_id,
            "advanced_api": self.cortex_advanced_api_checkbox.isChecked()
        }
        
        # Test de la connexion
        try:
            # Création d'un gestionnaire de configuration temporaire
            temp_config_manager = MagicMock()
            temp_config_manager.get_cortex_config.return_value = config
            
            # Création d'un client temporaire
            temp_client = CortexClient(temp_config_manager)
            
            # Test de la connexion en récupérant les endpoints
            endpoints = temp_client.get_endpoints()
            
            # Vérification du résultat
            if endpoints:
                QMessageBox.information(self, "Connexion réussie", 
                                      f"Connexion à Cortex XDR réussie. {len(endpoints)} endpoints récupérés.")
            else:
                QMessageBox.warning(self, "Connexion partielle", 
                                   "Connexion à Cortex XDR établie, mais aucun endpoint récupéré.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", 
                               f"Erreur lors de la connexion à Cortex XDR:\n{str(e)}")
        
        # Mise à jour de l'interface
        self.test_cortex_button.setEnabled(True)
        self.statusBar().showMessage("Test de connexion terminé")
    
    def save_cortex_config(self):
        """Sauvegarde de la configuration Cortex XDR"""
        # Récupération des paramètres
        base_url = self.cortex_url_input.text()
        api_key = self.cortex_api_key_input.text()
        api_key_id = self.cortex_api_key_id_input.text()
        tenant_id = self.cortex_tenant_id_input.text()
        advanced_api = self.cortex_advanced_api_checkbox.isChecked()
        
        # Sauvegarde de la configuration
        config = {
            "base_url": base_url,
            "api_key": api_key,
            "api_key_id": api_key_id,
            "tenant_id": tenant_id,
            "advanced_api": advanced_api
        }
        
        self.config_manager.save_cortex_config(config)
        
        # Mise à jour du client
        self.cortex_client = CortexClient(self.config_manager)
        
        QMessageBox.information(self, "Configuration sauvegardée", 
                              "La configuration Cortex XDR a été sauvegardée avec succès.")
    
    def browse_yara_directory(self):
        """Sélection du répertoire des règles YARA"""
        directory = QFileDialog.getExistingDirectory(
            self, "Sélectionner le répertoire des règles YARA", ""
        )
        
        if directory:
            self.yara_rules_dir_input.setText(directory)
    
    def reload_yara_rules(self):
        """Rechargement des règles YARA"""
        rules_dir = self.yara_rules_dir_input.text()
        
        if not rules_dir:
            QMessageBox.warning(self, "Répertoire non spécifié", 
                               "Veuillez spécifier le répertoire des règles YARA.")
            return
        
        # Sauvegarde de la configuration
        self.config_manager.save_yara_config({"rules_dir": rules_dir})
        
        # Rechargement des règles
        try:
            self.yara_scanner = YaraScanner(rules_dir)
            self.analyzer = Analyzer(self.yara_scanner, self.cortex_client)
            
            QMessageBox.information(self, "Règles rechargées", 
                                  "Les règles YARA ont été rechargées avec succès.")
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", 
                               f"Erreur lors du rechargement des règles YARA:\n{str(e)}")
    
    def save_all_config(self):
        """Sauvegarde de toutes les configurations"""
        # Sauvegarde de la configuration Cortex XDR
        self.save_cortex_config()
        
        # Sauvegarde de la configuration YARA
        rules_dir = self.yara_rules_dir_input.text()
        self.config_manager.save_yara_config({"rules_dir": rules_dir})
        
        # Sauvegarde de la configuration UI
        language = "fr" if self.language_combo.currentIndex() == 0 else "en"
        
        theme_index = self.theme_combo.currentIndex()
        theme = "light"
        if theme_index == 1:
            theme = "dark"
        elif theme_index == 2:
            theme = "system"
        
        self.config_manager.save_ui_config({
            "language": language,
            "theme": theme
        })
        
        # Application du thème
        self.apply_theme()
        
        QMessageBox.information(self, "Configurations sauvegardées", 
                              "Toutes les configurations ont été sauvegardées avec succès.")
