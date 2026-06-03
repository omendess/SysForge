@echo off
echo Iniciando Build: SysForge PORTABLE (Leve)
echo.
if exist build rmdir /s /q build
python builder.py PORTABLE
pause

