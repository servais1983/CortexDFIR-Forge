import os
import logging
import jinja2
import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Générateur de rapports HTML pour les résultats d'analyse
    """
    
    def __init__(self):
        """
        Initialisation du générateur de rapports
        """
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Création du répertoire de templates s'il n'existe pas
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir, exist_ok=True)
            self._create_default_templates()
        
        logger.info("ReportGenerator initialisé")
    
    def generate_html_report(self, analysis_results: Dict[str, Any], output_dir: str) -> str:
        """
        Génère un rapport HTML à partir des résultats d'analyse
        
        Args:
            analysis_results: Résultats d'analyse
            output_dir: Répertoire de sortie pour le rapport
        
        Returns:
            Chemin du rapport généré
        """
        logger.info(f"Génération du rapport HTML dans {output_dir}")
        
        try:
            # Vérification du répertoire de sortie
            if not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # Préparation des données pour le template
            template_data = self._prepare_template_data(analysis_results)
            
            # Chargement du template
            template = self.env.get_template("report.html")
            
            # Génération du rapport
            report_html = template.render(**template_data)
            
            # Création du nom de fichier avec horodatage
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"cortexdfir_report_{timestamp}.html"
            report_path = os.path.join(output_dir, report_filename)
            
            # Écriture du rapport
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_html)
            
            # Copie des ressources statiques
            self._copy_static_resources(output_dir)
            
            logger.info(f"Rapport HTML généré: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport HTML: {str(e)}", exc_info=True)
            raise
    
    def _prepare_template_data(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare les données pour le template de rapport
        
        Args:
            analysis_results: Résultats d'analyse
        
        Returns:
            Dictionnaire de données pour le template
        """
        # Calcul des statistiques globales
        total_files = len(analysis_results)
        total_threats = sum(len(result.get("threats", [])) for result in analysis_results.values())
        
        threat_severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        threat_types = {}
        
        # Analyse des menaces
        for file_path, result in analysis_results.items():
            for threat in result.get("threats", []):
                severity = threat.get("severity", "info").lower()
                if severity in threat_severity_counts:
                    threat_severity_counts[severity] += 1
                
                threat_type = threat.get("type", "unknown")
                if threat_type in threat_types:
                    threat_types[threat_type] += 1
                else:
                    threat_types[threat_type] = 1
        
        # Calcul du score global
        global_score = 0
        if total_files > 0:
            global_score = sum(result.get("score", 0) for result in analysis_results.values()) / total_files
        
        # Préparation des données
        template_data = {
            "report_title": "Rapport d'analyse CortexDFIR-Forge",
            "report_date": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "total_files": total_files,
            "total_threats": total_threats,
            "global_score": int(global_score),
            "threat_severity_counts": threat_severity_counts,
            "threat_types": threat_types,
            "results": []
        }
        
        # Tri des résultats par score décroissant
        sorted_results = sorted(
            [(file_path, result) for file_path, result in analysis_results.items()],
            key=lambda x: x[1].get("score", 0),
            reverse=True
        )
        
        # Formatage des résultats pour le template
        for file_path, result in sorted_results:
            template_data["results"].append({
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": result.get("file_size", 0),
                "file_type": result.get("file_type", "unknown"),
                "score": result.get("score", 0),
                "threats": result.get("threats", []),
                "analysis_types": result.get("analysis_types", [])
            })
        
        return template_data
    
    def _copy_static_resources(self, output_dir: str) -> None:
        """
        Copie les ressources statiques nécessaires pour le rapport
        
        Args:
            output_dir: Répertoire de sortie pour les ressources
        """
        static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
        
        if not os.path.exists(static_dir):
            os.makedirs(static_dir, exist_ok=True)
            self._create_default_static_resources()
        
        # Création du répertoire static dans le répertoire de sortie
        output_static_dir = os.path.join(output_dir, "static")
        if not os.path.exists(output_static_dir):
            os.makedirs(output_static_dir, exist_ok=True)
        
        # Copie des fichiers CSS
        css_file = os.path.join(static_dir, "report.css")
        if os.path.exists(css_file):
            import shutil
            shutil.copy2(css_file, os.path.join(output_static_dir, "report.css"))
    
    def _create_default_templates(self) -> None:
        """
        Crée les templates par défaut si aucun n'est trouvé
        """
        try:
            # Template de rapport HTML
            report_template = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ report_title }}</title>
    <link rel="stylesheet" href="static/report.css">
</head>
<body>
    <header>
        <div class="logo">
            <h1>CortexDFIR-Forge</h1>
        </div>
        <div class="report-info">
            <h2>{{ report_title }}</h2>
            <p>Date du rapport: {{ report_date }}</p>
        </div>
    </header>

    <section class="summary">
        <h2>Résumé de l'analyse</h2>
        <div class="summary-grid">
            <div class="summary-card">
                <h3>Fichiers analysés</h3>
                <p class="big-number">{{ total_files }}</p>
            </div>
            <div class="summary-card">
                <h3>Menaces détectées</h3>
                <p class="big-number">{{ total_threats }}</p>
            </div>
            <div class="summary-card">
                <h3>Score global</h3>
                <div class="score-container">
                    <div class="score-circle {% if global_score >= 75 %}critical{% elif global_score >= 50 %}high{% elif global_score >= 25 %}medium{% else %}low{% endif %}">
                        {{ global_score }}
                    </div>
                </div>
            </div>
        </div>
    </section>

    <section class="threat-distribution">
        <h2>Distribution des menaces</h2>
        <div class="threat-grid">
            <div class="threat-card">
                <h3>Par sévérité</h3>
                <ul class="severity-list">
                    <li class="severity-critical">Critique: {{ threat_severity_counts.critical }}</li>
                    <li class="severity-high">Élevée: {{ threat_severity_counts.high }}</li>
                    <li class="severity-medium">Moyenne: {{ threat_severity_counts.medium }}</li>
                    <li class="severity-low">Faible: {{ threat_severity_counts.low }}</li>
                    <li class="severity-info">Info: {{ threat_severity_counts.info }}</li>
                </ul>
            </div>
            <div class="threat-card">
                <h3>Par type</h3>
                <ul class="type-list">
                    {% for type, count in threat_types.items() %}
                    <li>{{ type }}: {{ count }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
    </section>

    <section class="detailed-results">
        <h2>Résultats détaillés</h2>
        
        {% for result in results %}
        <div class="file-result {% if result.score >= 75 %}critical{% elif result.score >= 50 %}high{% elif result.score >= 25 %}medium{% elif result.score > 0 %}low{% endif %}">
            <div class="file-header">
                <h3>{{ result.file_name }}</h3>
                <div class="file-score">
                    <div class="score-circle {% if result.score >= 75 %}critical{% elif result.score >= 50 %}high{% elif result.score >= 25 %}medium{% else %}low{% endif %}">
                        {{ result.score }}
                    </div>
                </div>
            </div>
            
            <div class="file-info">
                <p><strong>Chemin:</strong> {{ result.file_path }}</p>
                <p><strong>Type:</strong> {{ result.file_type }}</p>
                <p><strong>Taille:</strong> {{ result.file_size }} octets</p>
                <p><strong>Types d'analyse:</strong> {{ result.analysis_types|join(', ') }}</p>
            </div>
            
            {% if result.threats %}
            <div class="threats-container">
                <h4>Menaces détectées ({{ result.threats|length }})</h4>
                <table class="threats-table">
                    <thead>
                        <tr>
                            <th>Type</th>
                            <th>Nom</th>
                            <th>Sévérité</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for threat in result.threats %}
                        <tr class="severity-{{ threat.severity }}">
                            <td>{{ threat.type }}</td>
                            <td>{{ threat.name }}</td>
                            <td>{{ threat.severity|capitalize }}</td>
                            <td>{{ threat.description }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% else %}
            <div class="no-threats">
                <p>Aucune menace détectée</p>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </section>

    <footer>
        <p>Rapport généré par CortexDFIR-Forge - Solution industrialisée pour l'utilisation de Cortex XDR dans le cadre d'investigations DFIR</p>
    </footer>
</body>
</html>
"""
            
            # Écriture du template
            os.makedirs(self.template_dir, exist_ok=True)
            with open(os.path.join(self.template_dir, "report.html"), "w") as f:
                f.write(report_template)
            
            logger.info("Template de rapport par défaut créé")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du template par défaut: {str(e)}", exc_info=True)
    
    def _create_default_static_resources(self) -> None:
        """
        Crée les ressources statiques par défaut si aucune n'est trouvée
        """
        try:
            # CSS pour le rapport
            report_css = """/* Styles généraux */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
    color: #333;
    line-height: 1.6;
}

/* En-tête */
header {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo h1 {
    margin: 0;
    font-size: 24px;
}

.report-info h2 {
    margin: 0;
    font-size: 20px;
}

.report-info p {
    margin: 5px 0 0;
    font-size: 14px;
}

/* Sections */
section {
    background-color: white;
    margin: 20px;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

section h2 {
    margin-top: 0;
    color: #2c3e50;
    border-bottom: 2px solid #ecf0f1;
    padding-bottom: 10px;
}

/* Résumé */
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.summary-card {
    background-color: #ecf0f1;
    padding: 20px;
    border-radius: 5px;
    text-align: center;
}

.summary-card h3 {
    margin-top: 0;
    color: #2c3e50;
}

.big-number {
    font-size: 36px;
    font-weight: bold;
    margin: 10px 0;
    color: #2c3e50;
}

/* Score */
.score-container {
    display: flex;
    justify-content: center;
}

.score-circle {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 24px;
    font-weight: bold;
    color: white;
}

.score-circle.critical {
    background-color: #e74c3c;
}

.score-circle.high {
    background-color: #e67e22;
}

.score-circle.medium {
    background-color: #f1c40f;
}

.score-circle.low {
    background-color: #2ecc71;
}

/* Distribution des menaces */
.threat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.threat-card {
    background-color: #ecf0f1;
    padding: 20px;
    border-radius: 5px;
}

.threat-card h3 {
    margin-top: 0;
    color: #2c3e50;
}

.severity-list, .type-list {
    list-style-type: none;
    padding: 0;
}

.severity-list li, .type-list li {
    padding: 5px 0;
    font-weight: 500;
}

.severity-critical {
    color: #e74c3c;
}

.severity-high {
    color: #e67e22;
}

.severity-medium {
    color: #f1c40f;
}

.severity-low {
    color: #2ecc71;
}

.severity-info {
    color: #3498db;
}

/* Résultats détaillés */
.file-result {
    margin-bottom: 20px;
    border-left: 5px solid #ecf0f1;
    background-color: #ecf0f1;
    border-radius: 5px;
    overflow: hidden;
}

.file-result.critical {
    border-left-color: #e74c3c;
}

.file-result.high {
    border-left-color: #e67e22;
}

.file-result.medium {
    border-left-color: #f1c40f;
}

.file-result.low {
    border-left-color: #2ecc71;
}

.file-header {
    background-color: #ecf0f1;
    padding: 15px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.file-header h3 {
    margin: 0;
    color: #2c3e50;
}

.file-score .score-circle {
    width: 50px;
    height: 50px;
    font-size: 18px;
}

.file-info {
    background-color: white;
    padding: 15px;
}

.file-info p {
    margin: 5px 0;
}

.threats-container {
    padding: 15px;
    background-color: white;
}

.threats-container h4 {
    margin-top: 0;
    color: #2c3e50;
}

.threats-table {
    width: 100%;
    border-collapse: collapse;
}

.threats-table th, .threats-table td {
    padding: 10px;
    text-align: left;
    border-bottom: 1px solid #ecf0f1;
}

.threats-table th {
    background-color: #ecf0f1;
    color: #2c3e50;
}

.threats-table tr.severity-critical {
    background-color: rgba(231, 76, 60, 0.1);
}

.threats-table tr.severity-high {
    background-color: rgba(230, 126, 34, 0.1);
}

.threats-table tr.severity-medium {
    background-color: rgba(241, 196, 15, 0.1);
}

.threats-table tr.severity-low {
    background-color: rgba(46, 204, 113, 0.1);
}

.threats-table tr.severity-info {
    background-color: rgba(52, 152, 219, 0.1);
}

.no-threats {
    padding: 15px;
    background-color: white;
    color: #7f8c8d;
    font-style: italic;
}

/* Pied de page */
footer {
    background-color: #2c3e50;
    color: white;
    text-align: center;
    padding: 20px;
    margin-top: 20px;
    font-size: 14px;
}

/* Responsive */
@media (max-width: 768px) {
    header {
        flex-direction: column;
        text-align: center;
    }
    
    .report-info {
        margin-top: 10px;
    }
    
    .summary-grid, .threat-grid {
        grid-template-columns: 1fr;
    }
    
    .file-header {
        flex-direction: column;
    }
    
    .file-score {
        margin-top: 10px;
    }
    
    .threats-table {
        display: block;
        overflow-x: auto;
    }
}
"""
            
            # Création du répertoire static
            static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
            os.makedirs(static_dir, exist_ok=True)
            
            # Écriture du CSS
            with open(os.path.join(static_dir, "report.css"), "w") as f:
                f.write(report_css)
            
            logger.info("Ressources statiques par défaut créées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des ressources statiques par défaut: {str(e)}", exc_info=True)
