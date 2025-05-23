from PyQt5.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QListWidget, QProgressBar, QCheckBox, QTreeWidget, QStatusBar, QFileDialog, QMessageBox
from PyQt5.QtCore import Qt

class Ui_MainWindow(object):
    """Interface utilisateur principale de CortexDFIR-Forge"""
    
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1024, 768)
        MainWindow.setWindowTitle("CortexDFIR-Forge - Solution DFIR industrialisée pour Cortex XDR")
        
        # Widget central
        self.centralwidget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.centralwidget)
        
        # Layout principal
        self.mainLayout = QVBoxLayout(self.centralwidget)
        
        # Onglets principaux
        self.tabWidget = QTabWidget(self.centralwidget)
        self.mainLayout.addWidget(self.tabWidget)
        
        # Onglet Analyse
        self.tabAnalysis = QWidget()
        self.tabWidget.addTab(self.tabAnalysis, "Analyse")
        
        # Layout de l'onglet Analyse
        self.analysisLayout = QVBoxLayout(self.tabAnalysis)
        
        # Section de sélection des fichiers
        self.fileSelectionLayout = QHBoxLayout()
        self.analysisLayout.addLayout(self.fileSelectionLayout)
        
        self.lblFiles = QLabel("Fichiers à analyser:")
        self.fileSelectionLayout.addWidget(self.lblFiles)
        
        self.btnSelectFiles = QPushButton("Sélectionner des fichiers")
        self.fileSelectionLayout.addWidget(self.btnSelectFiles)
        
        # Liste des fichiers sélectionnés
        self.lstFiles = QListWidget()
        self.analysisLayout.addWidget(self.lstFiles)
        
        # Options d'analyse
        self.analysisOptionsLayout = QHBoxLayout()
        self.analysisLayout.addLayout(self.analysisOptionsLayout)
        
        self.lblAnalysisTypes = QLabel("Types d'analyse:")
        self.analysisOptionsLayout.addWidget(self.lblAnalysisTypes)
        
        self.chkMalware = QCheckBox("Malware")
        self.chkMalware.setChecked(True)
        self.analysisOptionsLayout.addWidget(self.chkMalware)
        
        self.chkRansomware = QCheckBox("Ransomware")
        self.chkRansomware.setChecked(True)
        self.analysisOptionsLayout.addWidget(self.chkRansomware)
        
        self.chkPhishing = QCheckBox("Phishing")
        self.chkPhishing.setChecked(True)
        self.analysisOptionsLayout.addWidget(self.chkPhishing)
        
        self.chkPersistence = QCheckBox("Persistance")
        self.chkPersistence.setChecked(True)
        self.analysisOptionsLayout.addWidget(self.chkPersistence)
        
        # Bouton de démarrage de l'analyse
        self.btnStartAnalysis = QPushButton("Démarrer l'analyse")
        self.btnStartAnalysis.setEnabled(False)
        self.analysisLayout.addWidget(self.btnStartAnalysis)
        
        # Barre de progression
        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.analysisLayout.addWidget(self.progressBar)
        
        # Résultats de l'analyse
        self.lblResults = QLabel("Résultats:")
        self.analysisLayout.addWidget(self.lblResults)
        
        self.treeResults = QTreeWidget()
        self.treeResults.setHeaderLabels(["Fichier", "Type", "Sévérité", "Description"])
        self.treeResults.setColumnWidth(0, 300)
        self.treeResults.setColumnWidth(1, 150)
        self.treeResults.setColumnWidth(2, 100)
        self.analysisLayout.addWidget(self.treeResults)
        
        # Bouton de génération de rapport
        self.btnGenerateReport = QPushButton("Générer un rapport")
        self.btnGenerateReport.setEnabled(False)
        self.analysisLayout.addWidget(self.btnGenerateReport)
        
        # Onglet Configuration
        self.tabConfig = QWidget()
        self.tabWidget.addTab(self.tabConfig, "Configuration")
        
        # Layout de l'onglet Configuration
        self.configLayout = QVBoxLayout(self.tabConfig)
        
        # Bouton des paramètres
        self.btnSettings = QPushButton("Paramètres Cortex XDR")
        self.configLayout.addWidget(self.btnSettings)
        
        # Onglet Aide
        self.tabHelp = QWidget()
        self.tabWidget.addTab(self.tabHelp, "Aide")
        
        # Layout de l'onglet Aide
        self.helpLayout = QVBoxLayout(self.tabHelp)
        
        self.lblHelp = QLabel("CortexDFIR-Forge est une solution industrialisée pour l'utilisation de Cortex XDR dans le cadre d'investigations DFIR.\n\nPour commencer, sélectionnez les fichiers à analyser dans l'onglet Analyse, choisissez les types d'analyse souhaités, puis cliquez sur 'Démarrer l'analyse'.")
        self.lblHelp.setWordWrap(True)
        self.helpLayout.addWidget(self.lblHelp)
        
        # Barre de statut
        self.statusbar = QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Prêt")
