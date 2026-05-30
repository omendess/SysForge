import winreg
import os
import subprocess
import json

CREATE_NO_WINDOW = 0x08000000
BLOATWARES = ["mcafee", "candy crush", "tiktok", "disney", "netflix", "spotify", "norton", "avast"]
APPX_BLOATWARES = ["Microsoft.BingNews", "Microsoft.GetHelp", "Microsoft.Getstarted", "Microsoft.Messaging", 
                   "Microsoft.Microsoft3DViewer", "Microsoft.MicrosoftSolitaireCollection", "Microsoft.NetworkSpeedTest", 
                   "Microsoft.News", "Microsoft.Office.OneNote", "Microsoft.Office.Sway", "Microsoft.Print3D", 
                   "Microsoft.SkypeApp", "Microsoft.Todos", "Microsoft.WindowsAlarms", "Microsoft.WindowsFeedbackHub", 
                   "Microsoft.WindowsMaps", "Microsoft.WindowsSoundRecorder", "Microsoft.XboxApp", 
                   "Microsoft.XboxGamingOverlay", "Microsoft.ZuneVideo", "Microsoft.YourPhone"]

def get_appx_packages():
    # Coleta todos os Appx que não são frameworks nem são fixos do sistema
    cmd = ["powershell", "-NoProfile", "-Command",
           "Get-AppxPackage | Where-Object { $_.IsFramework -eq $false -and $_.NonRemovable -eq $false } | Select-Object Name, PackageFullName | ConvertTo-Json -Compress"]
    try:
        p = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=15)
        if p.stdout.strip():
            data = json.loads(p.stdout)
            if isinstance(data, dict):
                data = [data]
            return data
    except Exception:
        pass
    return []

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
            
    # Appx Packages (Todos os pacotes não essenciais/removíveis)
    appx_list = get_appx_packages()
    for appx in appx_list:
        name = appx.get("Name", "")
        fullname = appx.get("PackageFullName", "")
        if name and fullname:
            is_bloat = any(b.lower() in name.lower() for b in APPX_BLOATWARES)
            apps.append({
                "name": f"[UWP] {name}",
                "size_mb": 0,
                "uninstall_string": f"APPX:{fullname}",
                "install_location": "",
                "is_bloatware": is_bloat
            })
            
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
        if uninstall_string.startswith("APPX:"):
            fullname = uninstall_string.split(":", 1)[1]
            cmd = ["powershell", "-NoProfile", "-Command", f"Remove-AppxPackage -Package '{fullname}'"]
            subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, check=False)
            return

        u_lower = uninstall_string.lower()
        # Prevent UI prompts from msi strings when possible
        if "msiexec" in u_lower and "/q" not in u_lower and "/x" in u_lower:
            uninstall_string += " /quiet /norestart"
        # Smart flags for .exe installers (InnoSetup, NSIS)
        elif ".exe" in u_lower and not any(f in u_lower for f in ["/s", "/quiet", "-s", "/verysilent"]):
            if "unins000" in u_lower or "unins001" in u_lower: # Usually InnoSetup
                uninstall_string += " /VERYSILENT /SUPPRESSMSGBOXES /NORESTART"
            elif "uninstall" in u_lower: # Usually NSIS
                uninstall_string += " /S"
        
        # Execute silently
        from gear.window_enforcer import enforce_window_rules
        p = subprocess.Popen(uninstall_string, creationflags=CREATE_NO_WINDOW, shell=True)
        enforce_window_rules(p.pid, duration=120)
        p.wait()
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

def nuke_bloatware():
    """Varre e remove silenciosamente bloatwares modernos."""
    yield "> 🚀 INICIANDO NUKE BLOATWARE..."
    apps = get_installed_apps()
    bloatwares = [app for app in apps if app.get('is_bloatware')]
    
    if not bloatwares:
        yield "> ✅ Nenhum bloatware detectado. Sistema limpo."
        return
        
    for app in bloatwares:
        name = app['name']
        yield f"> 🗑️ Removendo {name}..."
        run_uninstall(app['uninstall_string'], None)
        
    yield f"> ✅ NUKE FINALIZADO: {len(bloatwares)} itens removidos com sucesso."
