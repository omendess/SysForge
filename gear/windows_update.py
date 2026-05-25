import subprocess

CREATE_NO_WINDOW = 0x08000000

def check_and_install_updates(cb=None):
    """Força a checagem e instalação de atualizações do Windows."""
    steps = [
        ("Iniciando scan de atualizações...", ["usoclient", "StartScan"]),
        ("Baixando atualizações encontradas...", ["usoclient", "StartDownload"]),
        ("Instalando atualizações...", ["usoclient", "StartInstall"]),
    ]
    
    for desc, cmd in steps:
        if cb: cb(f"🔄 {desc}")
        try:
            subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, timeout=120)
        except subprocess.TimeoutExpired:
            if cb: cb(f"⏱️ Timeout em: {desc}")
        except Exception as e:
            if cb: cb(f"⚠️ {desc} — Erro: {e}")
    
    if cb: cb("✅ Processo de atualização disparado. O Windows continuará em background.")
