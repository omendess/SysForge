import subprocess
import os

CREATE_NO_WINDOW = 0x08000000

def _run_bg(cmd, cb=None):
    try:
        p = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp850', errors='ignore')
        if p.returncode == 0:
            if cb: cb("✅ Concluído.")
            return True
        else:
            if cb: cb(f"⚠️ Aviso (código {p.returncode}).")
            return False
    except Exception as e:
        if cb: cb(f"❌ Falha: {e}")
        return False

def force_restore_point(cb=None):
    if cb: cb("⏳ Criando Ponto de Restauração...")
    subprocess.run(["powershell", "-NoProfile", "-Command", "Enable-ComputerRestore -Drive 'C:\'"], creationflags=CREATE_NO_WINDOW)
    return _run_bg(["powershell", "-NoProfile", "-Command", "Checkpoint-Computer -Description 'SysForge_Backup' -RestorePointType 'MODIFY_SETTINGS'"], cb)

def repair_sfc_dism(cb=None):
    if cb: cb("⏳ Iniciando Reparo DISM (Restauração da Imagem)...")
    _run_bg(["dism", "/Online", "/Cleanup-Image", "/RestoreHealth"])
    if cb: cb("⏳ Iniciando Reparo SFC (Arquivos do Sistema)...")
    return _run_bg(["sfc", "/scannow"], cb)

def repair_disk_chkdsk(cb=None):
    if cb: cb("⏳ Agendando Chkdsk (Reparo físico/lógico) para o próximo Boot...")
    cmd = ["cmd", "/c", "echo Y | chkdsk C: /f /r /x"]
    return _run_bg(cmd, cb)

def reset_network(cb=None):
    if cb: cb("⏳ Resetando Rede (Winsock, IP, DNS)...")
    _run_bg(["netsh", "winsock", "reset"])
    _run_bg(["netsh", "int", "ip", "reset"])
    _run_bg(["ipconfig", "/flushdns"])
    if cb: cb("✅ Rede resetada.")
    return True

def reset_windows_update(cb=None):
    if cb: cb("⏳ Recriando cache do Windows Update...")
    cmd = [
        "cmd", "/c",
        "net stop wuauserv & net stop cryptSvc & net stop bits & net stop msiserver & "
        "ren C:\\Windows\\SoftwareDistribution SoftwareDistribution.old & "
        "ren C:\\Windows\\System32\\catroot2 catroot2.old & "
        "net start wuauserv & net start cryptSvc & net start bits & net start msiserver"
    ]
    return _run_bg(cmd, cb)

def scan_network_devices():
    devices = []
    
    # Wi-Fi e CABO via ARP
    out_arp = subprocess.run(["arp", "-a"], creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp850', errors='ignore')
    for line in out_arp.stdout.splitlines():
        if "din" in line.lower() or "dynamic" in line.lower():
            parts = line.split()
            if len(parts) >= 2:
                devices.append(f"📡 IP: {parts[0]:<15} | MAC: {parts[1]}")
                
    # Interfaces Wi-Fi
    out_wifi = subprocess.run(["netsh", "wlan", "show", "interfaces"], creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp850', errors='ignore')
    for line in out_wifi.stdout.splitlines():
        if "SSID" in line and "BSSID" not in line:
            ssid = line.split(":", 1)[-1].strip()
            if ssid: devices.append(f"📶 Wi-Fi Conectado: {ssid}")

    # Bluetooth
    bt_cmd = ["powershell", "-NoProfile", "-Command", "Get-PnpDevice -Class Bluetooth | Where-Object Status -eq 'OK' | Select-Object -ExpandProperty FriendlyName"]
    out_bt = subprocess.run(bt_cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, encoding='cp850', errors='ignore')
    for line in out_bt.stdout.splitlines():
        if line.strip():
            devices.append(f"🔵 Bluetooth: {line.strip()}")
            
    return devices if devices else ["Nenhum dispositivo encontrado."]
