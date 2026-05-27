import subprocess
import socket

CREATE_NO_WINDOW = 0x08000000

def get_current_hostname():
    """Retorna o hostname atual da máquina."""
    return socket.gethostname()

def set_hostname(new_name, cb=None):
    """Renomeia o hostname via PowerShell Rename-Computer (requer reinicialização)."""
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
        # PowerShell Rename-Computer (funciona em todas as versões modernas do Windows)
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
             f"Rename-Computer -NewName '{clean}' -Force"],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            if cb: cb(f"✅ Hostname alterado para '{clean}'. ⚠️ Reinicie o PC para a mudança ter efeito.")
            return True
        else:
            err = (result.stderr or result.stdout or "Erro desconhecido").strip()
            if cb: cb(f"⚠️ Falha ao renomear: {err}")
            return False
    except Exception as e:
        if cb: cb(f"❌ Erro ao renomear: {e}")
        return False

