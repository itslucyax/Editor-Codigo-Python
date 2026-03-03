@echo off
REM ==================================================================
REM DEMO CON BASE DE DATOS REAL
REM ==================================================================
REM 
REM ANTES DE EJECUTAR:
REM 1. Edita las variables de configuracion abajo con tus datos reales
REM 2. Asegurate de tener acceso a la BD
REM 3. Ejecuta este script
REM
REM ==================================================================

echo.
echo ====================================================================
echo   DEMO: Conexion REAL a Base de Datos
echo ====================================================================
echo.

REM ============================================
REM CONFIGURACION - EDITA ESTOS VALORES
REM ============================================
set SERVER=TU_SERVIDOR\INSTANCIA
set DATABASE=TU_BASE_DATOS
set TABLE=G_SCRIPT
set USER=tu_usuario
set PASSWORD=tu_password
set MODELO=T01
set CODIGO=BOBINADO
REM ============================================

echo Configuracion actual:
echo   Servidor: %SERVER%
echo   Base de datos: %DATABASE%
echo   Tabla: %TABLE%
echo   Modelo: %MODELO%
echo   Codigo: %CODIGO%
echo.

REM Verificar que se editaron los valores
if "%SERVER%"=="TU_SERVIDOR\INSTANCIA" (
    echo.
    echo ========================================
    echo ERROR: Debes editar este archivo primero
    echo ========================================
    echo.
    echo Este script contiene valores placeholder.
    echo.
    echo Abre este archivo con un editor de texto y cambia:
    echo   - SERVER: Tu servidor SQL Server
    echo   - DATABASE: Tu base de datos
    echo   - TABLE: Tu tabla
    echo   - USER: Tu usuario SQL
    echo   - PASSWORD: Tu password
    echo   - MODELO y CODIGO: Un registro real que exista
    echo.
    echo Luego vuelve a ejecutar este script.
    echo.
    pause
    exit /b 1
)

echo Creando configuracion JSON...

REM Crear archivo de configuración con datos reales
(
echo {
echo   "connection": {
echo     "server": "%SERVER%",
echo     "database": "%DATABASE%",
echo     "table": "%TABLE%",
echo     "user": "%USER%",
echo     "password": "%PASSWORD%",
echo     "content_column": "SCRIPT"
echo   },
echo   "script": {
echo     "key_columns": ["MODELO", "CODIGO"],
echo     "key_values": ["%MODELO%", "%CODIGO%"],
echo     "editable_columns": ["GRUPO"]
echo   }
echo }
) > temp_bd_real.json

echo.
echo Configuracion generada:
type temp_bd_real.json
echo.
echo.
echo Presiona cualquier tecla para conectar y abrir el editor...
pause > nul

echo.
echo Conectando a base de datos...
echo.

REM Lanzar el editor con conexion real
py -3 main.py --config-file temp_bd_real.json

echo.
echo ====================================================================
echo Editor cerrado. Cambios guardados en la base de datos.
echo ====================================================================
echo.

REM Limpiar archivo temporal
del temp_bd_real.json

pause
