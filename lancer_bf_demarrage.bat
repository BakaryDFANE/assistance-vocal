@echo off
rem %~dp0 = dossier ou se trouve ce .bat : ca marche quel que soit
rem l'ordinateur ou le dossier dans lequel le projet est copie/clone,
rem contrairement au chemin en dur precedent qui ne fonctionnait que sur
rem un seul PC (C:\Users\faneb\...).
cd /d "%~dp0"
py -3.12 "assistant_bf.py"