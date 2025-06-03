@echo off
echo Installation des outils de développement...

:: Installation de Visual Studio Build Tools
echo Téléchargement de Visual Studio Build Tools...
curl -L -o vs_buildtools.exe https://aka.ms/vs/17/release/vs_buildtools.exe

:: Installation des composants nécessaires
echo Installation des composants...
vs_buildtools.exe --quiet --wait --norestart ^
    --add Microsoft.VisualStudio.Workload.VCTools ^
    --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64 ^
    --add Microsoft.VisualStudio.Component.Windows10SDK

REM Téléchargement et installation d'OpenSSL
echo Téléchargement d'OpenSSL...
curl -L -o openssl.exe https://slproweb.com/download/Win64OpenSSL-3_1_4.exe
echo Installation d'OpenSSL...
start /wait openssl.exe /silent /sp- /suppressmsgboxes

:: Installation de yara-python
echo Installation de yara-python...
pip install yara-python==4.3.1

echo Installation terminée !
pause 