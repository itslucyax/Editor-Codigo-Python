@echo off
REM Script para probar el editor con BD
REM ANTES DE EJECUTAR: Edita test_config.json con tus datos reales
echo Iniciando editor con conexion a BD...
py -3 main.py --config-file test_config.json
pause
