import winreg
import os
import subprocess

CREATE_NO_WINDOW = 0x08000000
BLOATWARES = ["mcafee", "candy crush", "tiktok", "disney", "netflix", "spotify", "norton", "avast"]

def get_installed_apps():
    apps = []
    keys_to_check = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hkey, subkey in keys_to_check:
        try:
            key = winreg.OpenKey(hkey, subkey)
            for i in range(winreg.QueryInfoKey(key)[0]):
                try:
                    sub_key_name = winreg.EnumKey(key, i)
                    sub_key = winreg.OpenKey(key, sub_key_name)
                    
                    try:
                        display_name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                    except OSError:
                        continue
                        
                    try:
                        uninstall_string, _ = winreg.QueryValueEx(sub_key, "UninstallString")
                    except OSError:
                        uninstall_string = ""
                        
                    try:
                        install_location, _ = winreg.QueryValueEx(sub_key, "InstallLocation")
                    except OSError:
                        install_location = ""
                        
                    try:
                        estimated_size, _ = winreg.QueryValueEx(sub_key, "EstimatedSize")
                        size_mb = estimated_size / 1024
                    except OSError:
                        size_mb = 0
                        
                    if display_name and uninstall_string:
                        is_bloat = any(b.lower() in display_name.lower() for b in BLOATWARES)
                        apps.append({
                            "name": display_name,
                            "size_mb": size_mb,
                            "uninstall_string": uninstall_string,
                            "install_location": install_location,
                            "is_bloatware": is_bloat
                        })
                except OSError:
                    continue
        except OSError:
            continue
            
    # Remove duplicates
    unique_apps = {}
    for app in apps:
        if app["name"] not in unique_apps:
            unique_apps[app["name"]] = app
            
    return sorted(list(unique_apps.values()), key=lambda x: x["name"].lower())

def open_location(path):
    if path and os.path.exists(path):
        os.startfile(path)

def run_uninstall(uninstall_string, status_callback=None):
    if not uninstall_string:
        return
    try:
        # Prevent UI prompts from msi strings when possible
        if "msiexec" in uninstall_string.lower() and "/q" not in uninstall_string.lower() and "/x" in uninstall_string.lower():
            uninstall_string += " /quiet /norestart"
        
        # Execute silently
        subprocess.run(uninstall_string, creationflags=CREATE_NO_WINDOW, check=False, shell=True)
    except Exception as e:
        if status_callback:
            status_callback(f"Erro: {str(e)}")

def uninstall_multiple(app_list, status_callback=None):
    for app in app_list:
        if status_callback:
            status_callback(f"Desinstalando {app['name']}...")
        run_uninstall(app['uninstall_string'], status_callback)
    if status_callback:
        status_callback("Processo de desinstalação finalizado!")
