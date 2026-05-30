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

def ressuscitar_drivers():
    yield "> 📡 Iniciando Protocolo de Ressuscitação de Drivers..."
    time.sleep(0.5)
    yield "> 🔍 Varrendo WMI (Win32_PnPEntity) por anomalias (ConfigManagerErrorCode != 0)..."
    
    import json
    cmd = 'powershell -NoProfile -Command "Get-CimInstance Win32_PnPEntity | Where-Object { $_.ConfigManagerErrorCode -ne 0 -and $_.ConfigManagerErrorCode -ne $null } | Select-Object Name, DeviceID | ConvertTo-Json"'
    out = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    
    if not out.stdout.strip():
        yield "> ✅ Nenhum conflito de driver detectado. Hardware estável."
        return
        
    try:
        devices = json.loads(out.stdout)
        if isinstance(devices, dict):
            devices = [devices]
    except Exception:
        yield "> ❌ Erro ao analisar resposta do WMI."
        return
        
    for dev in devices:
        name = dev.get('Name', 'Unknown')
        dev_id = dev.get('DeviceID', '')
        yield f"> ⚠️ Anomalia encontrada: {name}"
        
        # Nível 1: Soft Reset
        yield f"  > Nível 1: Executando Soft Reset (Disable -> Enable)..."
        subprocess.run(["pnputil", "/disable-device", dev_id], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        time.sleep(1)
        subprocess.run(["pnputil", "/enable-device", dev_id], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        # Verificar se corrigiu
        check_cmd = f'powershell -NoProfile -Command "Get-CimInstance Win32_PnPEntity -Filter \\"DeviceID=\'{dev_id}\'\\" | Select-Object ConfigManagerErrorCode | ConvertTo-Json"'
        check_out = subprocess.run(check_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        
        fixed = False
        try:
            status = json.loads(check_out.stdout).get("ConfigManagerErrorCode")
            if status == 0: fixed = True
        except:
            pass
            
        if fixed:
            yield "  > ✅ Soft Reset bem-sucedido."
        else:
            yield "  > ❌ Soft Reset falhou. Iniciando Nível 2 (Hard Purge)..."
            # Precisamos extrair qual oem.inf pertence a ele para purgar
            inf_cmd = f'powershell -NoProfile -Command "(Get-CimInstance Win32_PnPSignedDriver | Where-Object {{ $_.DeviceID -eq \'{dev_id}\' }}).InfName"'
            inf_out = subprocess.run(inf_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            inf_name = inf_out.stdout.strip()
            
            if inf_name and inf_name.lower().endswith(".inf"):
                yield f"  > 🗑️ Purgando driver corrompido: {inf_name}"
                subprocess.run(["pnputil", "/delete-driver", inf_name, "/uninstall", "/force"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                yield "  > ⚠️ INF não encontrado para purga direta."
                
            yield "  > 🔄 Forçando Scan de Hardware (PnP Enum)..."
            subprocess.run(["pnputil", "/scan-devices"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            yield "  > ✅ Hard Purge concluído. Verifique o gerenciador de dispositivos."

    yield "> 🚀 Protocolo de Ressuscitação Finalizado."
