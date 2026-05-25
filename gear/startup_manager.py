import winreg
import os

STARTUP_PATHS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
]

def get_startup_items():
    """Retorna lista de programas que iniciam com o Windows."""
    items = []
    
    for hkey, path in STARTUP_PATHS:
        scope = "Usuário" if hkey == winreg.HKEY_CURRENT_USER else "Sistema"
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    items.append({
                        "name": name,
                        "command": value,
                        "scope": scope,
                        "hkey": hkey,
                        "reg_path": path,
                        "enabled": True
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            continue
    
    # Também verificar a pasta Startup do shell
    startup_folder = os.path.join(os.environ.get("APPDATA", ""), 
                                   r"Microsoft\Windows\Start Menu\Programs\Startup")
    if os.path.exists(startup_folder):
        for f in os.listdir(startup_folder):
            fp = os.path.join(startup_folder, f)
            if os.path.isfile(fp):
                items.append({
                    "name": f.replace(".lnk", ""),
                    "command": fp,
                    "scope": "Pasta Startup",
                    "hkey": None,
                    "reg_path": startup_folder,
                    "enabled": True
                })
    
    return sorted(items, key=lambda x: x["name"].lower())

def disable_startup_item(item, cb=None):
    """Remove um item da inicialização automática."""
    try:
        if item["hkey"] is not None:
            # É um registro
            key = winreg.OpenKey(item["hkey"], item["reg_path"], 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, item["name"])
            winreg.CloseKey(key)
            if cb: cb(f"✅ {item['name']} removido da inicialização")
            return True
        else:
            # É um atalho na pasta Startup
            fp = os.path.join(item["reg_path"], item["name"] + ".lnk")
            if not os.path.exists(fp):
                fp = os.path.join(item["reg_path"], item["name"])
            if os.path.exists(fp):
                os.remove(fp)
                if cb: cb(f"✅ {item['name']} removido da pasta Startup")
                return True
            else:
                if cb: cb(f"⚠️ Arquivo não encontrado: {item['name']}")
                return False
    except PermissionError:
        if cb: cb(f"⚠️ Sem permissão para remover {item['name']} (requer Admin)")
        return False
    except Exception as e:
        if cb: cb(f"❌ Erro: {e}")
        return False
