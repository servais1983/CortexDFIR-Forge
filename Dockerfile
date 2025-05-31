# Dockerfile optimisé pour la production
FROM python:3.11-slim-bullseye AS base

# Métadonnées
LABEL maintainer="CortexDFIR-Forge Team <support@cortexdfir-forge.com>"
LABEL version="2.0.0"
LABEL description="CortexDFIR-Forge - Production Container for DFIR Analysis with Cortex XDR Integration"
LABEL org.opencontainers.image.source="https://github.com/servais1983/CortexDFIR-Forge"
LABEL org.opencontainers.image.documentation="https://github.com/servais1983/CortexDFIR-Forge/blob/master/docs/"
LABEL org.opencontainers.image.licenses="MIT"

# Variables d'environnement de base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_HOME=/app \
    APP_USER=cortexdfir \
    APP_GROUP=cortexdfir \
    APP_UID=1000 \
    APP_GID=1000

# ==============================================================================
# ÉTAPE 1: BUILD - Installation des dépendances et compilation
# ==============================================================================
FROM base AS builder

# Installation des outils de build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    cmake \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libmagic-dev \
    libyara-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Création de l'environnement virtuel
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copie et installation des dépendances
COPY requirements-updated.txt /tmp/
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r /tmp/requirements-updated.txt

# ==============================================================================
# ÉTAPE 2: RUNTIME - Image finale optimisée
# ==============================================================================
FROM base AS runtime

# Installation des dépendances runtime uniquement
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libyara10 \
    libssl1.1 \
    libffi7 \
    ca-certificates \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Création de l'utilisateur non-privilégié
RUN groupadd -g $APP_GID $APP_GROUP && \
    useradd -u $APP_UID -g $APP_GID -d $APP_HOME -s /bin/bash -m $APP_USER

# Copie de l'environnement virtuel depuis l'étape de build
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Création de la structure des répertoires
RUN mkdir -p $APP_HOME/{data,logs,config,rules,static,templates,reports} && \
    chown -R $APP_USER:$APP_GROUP $APP_HOME

# Définition du répertoire de travail
WORKDIR $APP_HOME

# Copie du code source avec permissions appropriées
COPY --chown=$APP_USER:$APP_GROUP . .

# Configuration des permissions spécifiques
RUN chmod -R 755 src/ && \
    chmod -R 644 rules/ && \
    chmod -R 755 scripts/ && \
    find . -name "*.py" -exec chmod 644 {} \; && \
    find src/ -name "main.py" -exec chmod 755 {} \;

# Configuration du répertoire de logs
RUN mkdir -p /var/log/cortexdfir-forge && \
    chown $APP_USER:$APP_GROUP /var/log/cortexdfir-forge && \
    ln -sf /var/log/cortexdfir-forge $APP_HOME/logs

# Variables d'environnement pour l'application
ENV ENV=production \
    LOG_LEVEL=INFO \
    LOG_FILE=/var/log/cortexdfir-forge/cortexdfir-forge.log \
    CONFIG_FILE=$APP_HOME/config/config.json \
    WORKERS=4 \
    TIMEOUT=300

# Exposition des ports
EXPOSE 8000 9090

# Configuration des volumes
VOLUME ["$APP_HOME/data", "$APP_HOME/config", "/var/log/cortexdfir-forge"]

# Health check amélioré
HEALTHCHECK --interval=30s \
            --timeout=10s \
            --start-period=40s \
            --retries=3 \
            CMD python src/utils/health_check.py || exit 1

# Changement vers l'utilisateur non-privilégié
USER $APP_USER

# Point d'entrée avec tini pour la gestion des signaux
ENTRYPOINT ["tini", "--"]

# Commande par défaut
CMD ["python", "src/main.py", "--server", "--host", "0.0.0.0", "--port", "8000"]
