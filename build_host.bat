@echo off
echo Iniciando Build: SysForge HOST (Completo)
echo.
if exist build rmdir /s /q build
python builder.py HOST
pause

