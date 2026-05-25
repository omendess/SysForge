import psutil
import subprocess
import winreg
import os

CREATE_NO_WINDOW = 0x08000000

def get_motherboard_info():
    try:
        cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_BaseBoard | ForEach-Object { '{0} {1}' -f $_.Manufacturer, $_.Product }"]
        output = subprocess.check_output(cmd, creationflags=CREATE_NO_WINDOW, text=True)
        return output.strip() or "Desconhecida"
    except:
        return "Desconhecida"

def get_cpu_info():
    try:
        # Busca o nome exato do processador direto do registro do Windows
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        processor_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        
        # Limpa espaços em branco extras que a Microsoft costuma colocar no registro
        return processor_name.strip()
    except Exception:
        return "Desconhecido"

def get_ram_info():
    try:
        return f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
    except Exception:
        return "Desconhecido"

def get_gpu_info():
    try:
        # Usa PowerShell via CIM para substituir o obsoleto wmic, sem piscar tela preta
        cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance -ClassName Win32_VideoController | Select-Object -ExpandProperty Name"]
        output = subprocess.check_output(cmd, creationflags=CREATE_NO_WINDOW, text=True)
        
        # Filtra as linhas vazias e cria a separação por " / " se houver múltiplas placas de vídeo
        gpus = [line.strip() for line in output.split('\n') if line.strip()]
        if gpus:
            return " / ".join(gpus)
    except Exception:
        pass
    
    return "Desconhecido"

def get_all_disks_info():
    disks = []
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt' and ('cdrom' in part.opts or not part.fstype):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device.replace("\\", ""),
                "total": usage.total / (1024**3),
                "free": usage.free / (1024**3),
                "percent": usage.percent
            })
        except Exception:
            pass
    return disks

def get_all_hardware():
    return {
        "Placa Mãe": get_motherboard_info(),
        "CPU": get_cpu_info(),
        "RAM": get_ram_info(),
        "GPU": get_gpu_info(),
        "Disks": get_all_disks_info()
    }
