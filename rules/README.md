# Règles YARA pour CortexDFIR-Forge

Ce répertoire contient une collection complète de règles YARA pour la détection de menaces dans le cadre d'analyses forensiques.

## Structure des règles

Les règles sont organisées par catégories pour faciliter leur maintenance et leur utilisation :

- **malware/** - Règles pour la détection de malwares génériques et spécifiques
- **ransomware/** - Règles spécialisées pour la détection de ransomwares (dont LockBit 3.0)
- **backdoors/** - Règles pour la détection de backdoors et shells distants
- **phishing/** - Règles pour l'identification de tentatives de phishing
- **antidebug/** - Règles pour détecter les techniques d'anti-débogage et d'anti-VM
- **exploits/** - Règles pour la détection d'exploits et kits d'exploitation
- **webshells/** - Règles pour l'identification de webshells
- **maldocs/** - Règles pour la détection de documents malveillants
- **crypto/** - Règles pour l'identification d'algorithmes cryptographiques

## Sources

Les règles YARA incluses dans ce répertoire proviennent de plusieurs sources reconnues :

1. **YARA-Rules Project** - [https://github.com/Yara-Rules/rules](https://github.com/Yara-Rules/rules)
2. **Signature-Base** - [https://github.com/Neo23x0/signature-base](https://github.com/Neo23x0/signature-base)
3. **Règles personnalisées CortexDFIR-Forge** - Développées spécifiquement pour ce projet

## Utilisation

Le moteur YARA de CortexDFIR-Forge charge automatiquement toutes les règles présentes dans ce répertoire et ses sous-répertoires. Les règles sont utilisées pour analyser les fichiers sélectionnés par l'utilisateur.

## Maintenance et mise à jour

Pour maintenir les règles à jour :

1. Vérifiez régulièrement les dépôts sources pour les nouvelles règles
2. Testez les nouvelles règles avant de les intégrer pour éviter les faux positifs
3. Documentez les modifications apportées aux règles existantes

## Contribution

Pour contribuer de nouvelles règles :

1. Créez un fichier .yar ou .yara dans le sous-répertoire approprié
2. Suivez les conventions de nommage existantes
3. Incluez des métadonnées complètes (description, auteur, date, etc.)
4. Testez la règle sur des échantillons connus avant de la soumettre

## Licence

Les règles YARA sont soumises aux licences de leurs projets d'origine respectifs. Veuillez consulter les fichiers LICENSE dans les dépôts sources pour plus d'informations.
