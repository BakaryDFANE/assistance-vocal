@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher introuvable. Installe Python 3.12 ou 3.13 depuis python.org.
    exit /b 1
)

py -3.12 --version >nul 2>nul
if errorlevel 1 (
    echo Python 3.12 introuvable. Installe Python 3.12 ou adapte ce fichier vers ta version Python.
    exit /b 1
)

echo Installation / mise a jour des dependances...
py -3.12 -m pip install --upgrade -r requirements.txt
if errorlevel 1 exit /b 1

echo Generation de l'icone BF...
py -3.12 scripts\generer_icone_bf.py
if errorlevel 1 exit /b 1

echo Creation de BF.exe...
py -3.12 -m PyInstaller --noconfirm --clean BF.spec
if errorlevel 1 exit /b 1

echo.
echo Terminee. Lance le logiciel ici:
echo dist\BF\BF.exe
