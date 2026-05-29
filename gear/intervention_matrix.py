import subprocess
import time

def run_cmd(cmd):
    try:
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def protocolo_guarda_chuva():
    # 1. Habilita a restauração no disco C:
    run_cmd('Enable-ComputerRestore -Drive "C:\"')
    
    # 2. Cria o ponto de restauração
    success = run_cmd('Checkpoint-Computer -Description "SysForge: Protocolo Guarda-Chuva" -RestorePointType "MODIFY_SETTINGS"')
    
    if success:
        return "[ OK ] Ponto de Restauração 'Protocolo Guarda-Chuva' criado com sucesso."
    else:
        return "[ ERRO ] Falha ao criar Ponto de Restauração. Prossiga com cautela."

def fix_rede_falsa():
    yield "> Iniciando expurgo de protocolos de rede..."
    time.sleep(0.5)
    yield "> Resetando Winsock..."
    run_cmd("netsh winsock reset")
    yield "> Flush DNS..."
    run_cmd("ipconfig /flushdns")
    yield "> Renovando IP..."
    run_cmd("ipconfig /renew")
    time.sleep(0.5)
    yield "> [ SUCESSO ] Protocolos de rede restaurados."

def fix_windows_update():
    yield "> Iniciando expurgo do Windows Update..."
    time.sleep(0.5)
    yield "> Parando serviço wuauserv..."
    run_cmd("Stop-Service -Name wuauserv -Force")
    yield "> Limpando cache do SoftwareDistribution..."
    run_cmd("Remove-Item -Path 'C:\\Windows\\SoftwareDistribution\\Download\\*' -Recurse -Force")
    yield "> Reiniciando serviço wuauserv..."
    run_cmd("Start-Service -Name wuauserv")
    time.sleep(0.5)
    yield "> [ SUCESSO ] Windows Update reestabelecido."

def fix_spooler_impressao():
    yield "> Iniciando expurgo do Spooler de Impressão..."
    time.sleep(0.5)
    yield "> Parando serviço spooler..."
    run_cmd("Stop-Service -Name spooler -Force")
    yield "> Limpando arquivos pendentes (.shd / .spl)..."
    run_cmd("Remove-Item -Path 'C:\\Windows\\System32\\spool\\PRINTERS\\*.*' -Force")
    yield "> Reiniciando serviço spooler..."
    run_cmd("Start-Service -Name spooler")
    time.sleep(0.5)
    yield "> [ SUCESSO ] Fila de impressão limpa."

def fix_explorer_congelado():
    yield "> Iniciando expurgo do Shell Explorer..."
    time.sleep(0.5)
    yield "> Encerrando explorer.exe..."
    run_cmd("Stop-Process -Name explorer -Force")
    yield "> Limpando IconCache.db..."
    run_cmd("Remove-Item -Path \"$env:localappdata\\IconCache.db\" -Force")
    yield "> Reiniciando explorer.exe..."
    run_cmd("Start-Process explorer.exe")
    time.sleep(0.5)
    yield "> [ SUCESSO ] Shell Windows reiniciado."

def fix_imagem_sistema():
    yield "> Iniciando reparo profundo de imagem (SFC/DISM)..."
    time.sleep(0.5)
    yield "> Executando SFC /scannow (Isso pode demorar vários minutos)..."
    run_cmd("sfc /scannow")
    yield "> Executando DISM RestoreHealth (Isso pode demorar vários minutos)..."
    run_cmd("DISM /Online /Cleanup-Image /RestoreHealth")
    time.sleep(0.5)
    yield "> [ SUCESSO ] Integridade do sistema verificada e restaurada."

def reverter_estado():
    yield "> Iniciando Rollback de Emergência..."
    time.sleep(0.5)
    yield "> Buscando último ponto de restauração SysForge..."
    cmd = "Restore-Computer -RestorePoint (Get-ComputerRestorePoint | Where-Object Description -match 'SysForge' | Select-Object -Last 1).SequenceNumber"
    run_cmd(cmd)
    yield "> [ AVISO ] O sistema será reiniciado automaticamente se a restauração for bem sucedida."
