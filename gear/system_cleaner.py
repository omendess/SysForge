import os
import subprocess
import shutil

CREATE_NO_WINDOW = 0x08000000

def get_folder_size(folder_path):
    total_size = 0
    if not os.path.exists(folder_path):
        return 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
    return total_size

def get_temp_size_gb():
    user_temp = os.environ.get('TEMP', '')
    win_temp = 'C:\\Windows\\Temp'
    size = get_folder_size(user_temp) + get_folder_size(win_temp)
    return size / (1024**3)

def get_windows_old_size_gb():
    win_old = 'C:\\Windows.old'
    size = get_folder_size(win_old)
    return size / (1024**3)

def _force_delete(path):
    """Tenta deletar de forma forçada contornando bloqueios de permissão simples."""
    import stat
    if os.path.isfile(path) or os.path.islink(path):
        try:
            os.chmod(path, stat.S_IWRITE)
            os.unlink(path)
            return True
        except Exception:
            subprocess.run(["cmd.exe", "/c", "del", "/q", "/f", path], creationflags=CREATE_NO_WINDOW, check=False)
            return not os.path.exists(path)
    elif os.path.isdir(path):
        try:
            shutil.rmtree(path, ignore_errors=True)
            if not os.path.exists(path): return True
        except Exception:
            pass
        subprocess.run(["cmd.exe", "/c", "rd", "/s", "/q", path], creationflags=CREATE_NO_WINDOW, check=False)
        return not os.path.exists(path)
    return False

def clean_temp_folders():
    user_temp = os.environ.get('TEMP', '')
    win_temp = 'C:\\Windows\\Temp'
    
    for folder in [user_temp, win_temp]:
        if not folder or not os.path.exists(folder):
            continue
        for item in os.listdir(folder):
            if item.startswith("_MEI"):
                continue
            item_path = os.path.join(folder, item)
            _force_delete(item_path)

def remove_windows_old():
    win_old = 'C:\\Windows.old'
    if os.path.exists(win_old):
        try:
            subprocess.run(["takeown", "/F", win_old, "/A", "/R", "/D", "Y"], creationflags=CREATE_NO_WINDOW, check=False)
            subprocess.run(["icacls", win_old, "/grant", "*S-1-5-32-544:F", "/T", "/C", "/Q"], creationflags=CREATE_NO_WINDOW, check=False)
            subprocess.run(["cmd.exe", "/c", "rd", "/s", "/q", win_old], creationflags=CREATE_NO_WINDOW, check=False)
        except Exception as e:
            raise RuntimeError(f"Erro ao remover Windows.old: {e}")

def system_purge():
    """Gerador que executa limpeza profunda e yielda strings de log."""
    targets = [
        (os.environ.get('TEMP', ''), "%TEMP% (Local)"),
        ('C:\\Windows\\Temp', "Windows Temp"),
        ('C:\\Windows\\Prefetch', "Prefetch"),
        ('C:\\Windows\\SoftwareDistribution\\Download', "SoftwareDistribution\\Download")
    ]
    
    yield "🧹 INICIANDO EXPURGO DE SISTEMA (FORÇADO)..."
    
    for folder, name in targets:
        if not folder or not os.path.exists(folder):
            yield f"⏭️ SKIP: {name} não encontrado."
            continue
            
        yield f"⏳ Limpando {name}..."
        count = 0
        for item in os.listdir(folder):
            if item.startswith("_MEI"):
                continue
            item_path = os.path.join(folder, item)
            if _force_delete(item_path):
                count += 1
        yield f"✅ LIMPO: {name} ({count} itens removidos)"

    yield "⏳ Esvaziando Lixeira Global (Clear-RecycleBin)..."
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"], creationflags=CREATE_NO_WINDOW, check=False)
        yield "✅ LIMPO: Lixeiras Globais"
    except Exception as e:
        yield f"❌ ERRO na Lixeira: {e}"
    
    yield "🚀 EXPURGO CONCLUÍDO COM SUCESSO!"
