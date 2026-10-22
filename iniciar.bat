@echo off
chcp 65001 >nul
title InversionDashboard
cd /d "%~dp0"

echo ============================================
echo   InversionDashboard - Iniciando...
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 goto :nopython

if exist ".venv\Scripts\python.exe" goto :arrancar

echo [1/3] Creando entorno virtual - la primera vez tarda 1 a 2 minutos...
python -m venv .venv
if errorlevel 1 goto :novenv
echo [2/3] Instalando dependencias - descarga aproximada de 200 MB...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt --quiet
goto :arrancar

:arrancar
echo [3/3] Abriendo el dashboard en tu navegador...
echo       Si no se abre solo, copia http://localhost:8501 en tu navegador.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true
echo.
echo [AVISO] La aplicacion se cerro. Si hubo errores, revisa este mensaje.
pause
exit /b 0

:nopython
echo [ERROR] No se encontro Python en tu sistema.
echo         Instalalo desde https://www.python.org/downloads/
echo         y marca la casilla "Add Python to PATH" durante la instalacion.
pause
exit /b 1

:novenv
echo [ERROR] No se pudo crear el entorno virtual.
pause
exit /b 1
