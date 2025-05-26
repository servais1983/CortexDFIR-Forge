/**
 * CortexDFIR-Forge - Script principal
 * Gère les interactions utilisateur et les visualisations de données
 */

// Initialisation au chargement du document
document.addEventListener('DOMContentLoaded', function() {
    initializeUI();
    setupEventListeners();
});

/**
 * Initialise l'interface utilisateur
 */
function initializeUI() {
    // Affiche la version actuelle
    const versionElement = document.getElementById('app-version');
    if (versionElement) {
        versionElement.textContent = APP_VERSION || 'v1.0.0';
    }
    
    // Initialise les tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(tooltip => {
        // Simple tooltip implementation
        tooltip.addEventListener('mouseenter', function(e) {
            const tooltipText = this.getAttribute('data-tooltip');
            const tooltipEl = document.createElement('div');
            tooltipEl.className = 'tooltip';
            tooltipEl.textContent = tooltipText;
            document.body.appendChild(tooltipEl);
            
            const rect = this.getBoundingClientRect();
            tooltipEl.style.top = `${rect.top - tooltipEl.offsetHeight - 5}px`;
            tooltipEl.style.left = `${rect.left + (rect.width / 2) - (tooltipEl.offsetWidth / 2)}px`;
            tooltipEl.style.opacity = '1';
            
            this.addEventListener('mouseleave', function() {
                tooltipEl.remove();
            }, { once: true });
        });
    });
    
    // Initialise les onglets si présents
    initTabs();
}

/**
 * Configure les écouteurs d'événements
 */
function setupEventListeners() {
    // Gestion du formulaire d'analyse
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.addEventListener('submit', function(e) {
            e.preventDefault();
            startAnalysis();
        });
    }
    
    // Gestion du bouton d'arrêt d'analyse
    const stopButton = document.getElementById('stop-analysis');
    if (stopButton) {
        stopButton.addEventListener('click', function() {
            stopAnalysis();
        });
    }
    
    // Gestion des boutons d'exportation
    const exportButtons = document.querySelectorAll('.export-button');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const format = this.getAttribute('data-format');
            exportReport(format);
        });
    });
    
    // Gestion des filtres de résultats
    const filterInputs = document.querySelectorAll('.result-filter');
    filterInputs.forEach(input => {
        input.addEventListener('input', function() {
            filterResults();
        });
    });
}

/**
 * Initialise le système d'onglets
 */
function initTabs() {
    const tabContainers = document.querySelectorAll('.tabs-container');
    tabContainers.forEach(container => {
        const tabs = container.querySelectorAll('.tab');
        const tabContents = container.querySelectorAll('.tab-content');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                
                // Désactive tous les onglets et contenus
                tabs.forEach(t => t.classList.remove('active'));
                tabContents.forEach(c => c.classList.remove('active'));
                
                // Active l'onglet cliqué et son contenu
                this.classList.add('active');
                const activeContent = container.querySelector(`.tab-content[data-tab="${tabId}"]`);
                if (activeContent) {
                    activeContent.classList.add('active');
                }
            });
        });
        
        // Active le premier onglet par défaut
        if (tabs.length > 0) {
            tabs[0].click();
        }
    });
}

/**
 * Démarre l'analyse des fichiers
 */
function startAnalysis() {
    // Récupère les fichiers sélectionnés
    const fileInput = document.getElementById('file-input');
    const files = fileInput.files;
    
    if (files.length === 0) {
        showNotification('Veuillez sélectionner au moins un fichier à analyser', 'warning');
        return;
    }
    
    // Récupère les options d'analyse
    const options = {
        useYara: document.getElementById('use-yara').checked,
        detectRansomware: document.getElementById('detect-ransomware').checked,
        detectPhishing: document.getElementById('detect-phishing').checked,
        detectBackdoors: document.getElementById('detect-backdoors').checked,
        generateReport: document.getElementById('generate-report').checked
    };
    
    // Affiche l'interface de progression
    showProgressUI();
    
    // Simule l'envoi des fichiers et options au backend
    // Dans une implémentation réelle, cela serait géré par une API
    console.log('Démarrage de l\'analyse avec les options:', options);
    console.log('Fichiers à analyser:', files);
    
    // Simule une progression
    simulateAnalysisProgress();
}

/**
 * Arrête l'analyse en cours
 */
function stopAnalysis() {
    // Implémentation réelle: appel à une API pour arrêter l'analyse
    console.log('Arrêt de l\'analyse demandé');
    showNotification('Analyse arrêtée par l\'utilisateur', 'info');
    
    // Réinitialise l'interface
    hideProgressUI();
}

/**
 * Affiche l'interface de progression
 */
function showProgressUI() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'block';
    }
    
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.style.display = 'none';
    }
}

/**
 * Masque l'interface de progression
 */
function hideProgressUI() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
    
    const analysisForm = document.getElementById('analysis-form');
    if (analysisForm) {
        analysisForm.style.display = 'block';
    }
}

/**
 * Simule la progression de l'analyse
 */
function simulateAnalysisProgress() {
    const progressBar = document.getElementById('analysis-progress');
    const progressText = document.getElementById('progress-text');
    const statusText = document.getElementById('status-text');
    
    let progress = 0;
    const interval = setInterval(() => {
        progress += 1;
        
        if (progressBar) {
            progressBar.value = progress;
            progressBar.style.width = `${progress}%`;
        }
        
        if (progressText) {
            progressText.textContent = `${progress}%`;
        }
        
        // Met à jour le texte de statut en fonction de la progression
        if (statusText) {
            if (progress < 20) {
                statusText.textContent = 'Initialisation de l\'analyse...';
            } else if (progress < 40) {
                statusText.textContent = 'Analyse des fichiers avec règles YARA...';
            } else if (progress < 60) {
                statusText.textContent = 'Détection des menaces...';
            } else if (progress < 80) {
                statusText.textContent = 'Analyse des indicateurs de compromission...';
            } else {
                statusText.textContent = 'Génération du rapport...';
            }
        }
        
        if (progress >= 100) {
            clearInterval(interval);
            
            // Simule un délai avant d'afficher les résultats
            setTimeout(() => {
                hideProgressUI();
                showResults();
            }, 500);
        }
    }, 100);
}

/**
 * Affiche les résultats de l'analyse
 */
function showResults() {
    // Dans une implémentation réelle, les résultats seraient récupérés depuis le backend
    
    // Affiche la section de résultats
    const resultsContainer = document.getElementById('results-container');
    if (resultsContainer) {
        resultsContainer.style.display = 'block';
    }
    
    // Affiche une notification
    showNotification('Analyse terminée avec succès', 'success');
    
    // Initialise les graphiques si Chart.js est disponible
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
}

/**
 * Initialise les graphiques de visualisation
 */
function initializeCharts() {
    // Exemple de graphique en camembert pour les types de menaces
    const threatTypesCtx = document.getElementById('threat-types-chart');
    if (threatTypesCtx) {
        new Chart(threatTypesCtx, {
            type: 'pie',
            data: {
                labels: ['Ransomware', 'Backdoor', 'Phishing', 'Malware', 'Autre'],
                datasets: [{
                    data: [12, 19, 8, 15, 5],
                    backgroundColor: [
                        '#e74c3c',
                        '#3498db',
                        '#f1c40f',
                        '#2ecc71',
                        '#9b59b6'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right'
                    },
                    title: {
                        display: true,
                        text: 'Répartition des menaces par type'
                    }
                }
            }
        });
    }
    
    // Exemple de graphique à barres pour les scores de menace
    const threatScoresCtx = document.getElementById('threat-scores-chart');
    if (threatScoresCtx) {
        new Chart(threatScoresCtx, {
            type: 'bar',
            data: {
                labels: ['Critique', 'Élevé', 'Moyen', 'Faible', 'Info'],
                datasets: [{
                    label: 'Nombre de menaces',
                    data: [5, 10, 15, 8, 12],
                    backgroundColor: [
                        '#e74c3c',
                        '#e67e22',
                        '#f1c40f',
                        '#2ecc71',
                        '#3498db'
                    ]
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Nombre de menaces par niveau de risque'
                    }
                }
            }
        });
    }
}

/**
 * Filtre les résultats en fonction des critères de recherche
 */
function filterResults() {
    const searchInput = document.getElementById('search-input');
    const severityFilter = document.getElementById('severity-filter');
    const typeFilter = document.getElementById('type-filter');
    
    if (!searchInput || !severityFilter || !typeFilter) {
        return;
    }
    
    const searchTerm = searchInput.value.toLowerCase();
    const severityValue = severityFilter.value;
    const typeValue = typeFilter.value;
    
    const findings = document.querySelectorAll('.finding');
    findings.forEach(finding => {
        const findingName = finding.querySelector('.finding-name').textContent.toLowerCase();
        const findingSeverity = finding.getAttribute('data-severity');
        const findingType = finding.getAttribute('data-type');
        
        const matchesSearch = searchTerm === '' || findingName.includes(searchTerm);
        const matchesSeverity = severityValue === 'all' || findingSeverity === severityValue;
        const matchesType = typeValue === 'all' || findingType === typeValue;
        
        if (matchesSearch && matchesSeverity && matchesType) {
            finding.style.display = 'block';
        } else {
            finding.style.display = 'none';
        }
    });
}

/**
 * Exporte le rapport dans le format spécifié
 */
function exportReport(format) {
    console.log(`Exportation du rapport au format ${format}`);
    showNotification(`Exportation du rapport au format ${format} en cours...`, 'info');
    
    // Simule un délai pour l'exportation
    setTimeout(() => {
        showNotification(`Rapport exporté avec succès au format ${format}`, 'success');
    }, 1500);
}

/**
 * Affiche une notification à l'utilisateur
 */
function showNotification(message, type = 'info') {
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        return;
    }
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    notificationContainer.appendChild(notification);
    
    // Fait disparaître la notification après un délai
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Variables globales
const APP_VERSION = 'v1.0.0';
