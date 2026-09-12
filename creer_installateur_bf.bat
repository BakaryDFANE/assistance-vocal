@echo off
setlocal
cd /d "%~dp0"

if not exist "dist\BF\BF.exe" (
    echo BF.exe introuvable. Lance d'abord build_bf_exe.bat.
    exit /b 1
)

where iscc >nul 2>nul
if errorlevel 1 (
    echo Inno Setup introuvable.
    echo Installe Inno Setup puis relance ce fichier:
    echo https://jrsoftware.org/isinfo.php
    exit /b 1
)

iscc installer\BF.iss
if errorlevel 1 exit /b 1

echo.
echo Installateur cree:
echo release\BF-Setup.exe
