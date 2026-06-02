import subprocess

def run_system_triage():
    """
    Reads Windows System Event Log silently via PowerShell.
    Returns a dict with error counts: {"network": X, "update": Y, "kernel": Z, "other": W}
    """
    cmd = 'powershell.exe -NoProfile -Command "Get-WinEvent -FilterHashtable @{LogName=\'System\'; Level=2,3} -MaxEvents 150 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProviderName"'
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW, text=True)
        lines = output.strip().split('\n')
        
        counts = {"network": 0, "update": 0, "kernel": 0, "other": 0}
        
        for line in lines:
            line = line.strip().lower()
            if not line: continue
            
            # Matriz de classificação semântica
            if "dns" in line or "network" in line or "tcpip" in line or "netwtw" in line or "ndis" in line:
                counts["network"] += 1
            elif "update" in line or "wusa" in line or "servicing" in line:
                counts["update"] += 1
            elif "kernel" in line or "disk" in line or "ntfs" in line or "bugcheck" in line:
                counts["kernel"] += 1
            else:
                counts["other"] += 1
                
        return counts
    except Exception as e:
        # Fallback de segurança silencioso
        return {"network": 0, "update": 0, "kernel": 0, "other": 0}
