@echo off
cd /d "%~dp0"
echo Iniciando Build: SysForge HOST (Completo)
echo.
if exist build rmdir /s /q build
if exist "dist\SysForge_Host*.exe" del /q "dist\SysForge_Host*.exe"
if exist Output rmdir /s /q Output
if exist __pycache__ rmdir /s /q __pycache__
del /q *.spec 2>nul
del /q *.exe 2>nul
python builder.py HOST
pause

