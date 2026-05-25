import subprocess
import socket

CREATE_NO_WINDOW = 0x08000000

def get_current_hostname():
    """Retorna o hostname atual da máquina."""
    return socket.gethostname()

def set_hostname(new_name, cb=None):
    """Renomeia o hostname da máquina (requer reinicialização)."""
    if not new_name or not new_name.strip():
        if cb: cb("⚠️ Nome inválido.")
        return False
    
    clean = new_name.strip().upper()
    
    # Validação: apenas letras, números e hífens
    if not all(c.isalnum() or c == '-' for c in clean):
        if cb: cb("⚠️ Nome deve conter apenas letras, números e hífens.")
        return False
    
    if len(clean) > 15:
        if cb: cb("⚠️ Nome deve ter no máximo 15 caracteres.")
        return False
    
    try:
        result = subprocess.run(
            ["wmic", "computersystem", "where", "name='%computername%'", "rename", clean],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, shell=True
        )
        
        # Fallback: PowerShell
        if result.returncode != 0:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Rename-Computer -NewName '{clean}' -Force"],
                creationflags=CREATE_NO_WINDOW, capture_output=True, text=True
            )
        
        if result.returncode == 0:
            if cb: cb(f"✅ Hostname alterado para {clean}. Reinicie para aplicar.")
            return True
        else:
            if cb: cb(f"⚠️ Falha ao renomear: {result.stderr.strip()}")
            return False
    except Exception as e:
        if cb: cb(f"❌ Erro: {e}")
        return False
