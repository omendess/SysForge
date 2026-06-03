@echo off
cd /d "%~dp0"
echo Iniciando Higiene Profunda...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist Output rmdir /s /q Output
if exist __pycache__ rmdir /s /q __pycache__
del /q *.spec 2>nul
echo [+] Ambiente limpo.
pause
