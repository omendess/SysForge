"""
system_info.py
Coleta informações detalhadas do sistema operacional, segurança e software
usando apenas winreg e subprocess (sem libs externas).
"""
import subprocess
import winreg
import re
import json
import concurrent.futures

CREATE_NO_WINDOW = 0x08000000


def _run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW,
                           capture_output=True, text=True, timeout=timeout)
        return (r.stdout + r.stderr).strip()
    except Exception:
        return ""


def _read_reg(hive, path, key, default="—"):
    try:
        k = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(k, key)
        winreg.CloseKey(k)
        return str(val).strip() or default
    except OSError:
        return default


# ═══════════════════════════════════════════════════════════
#  WINDOWS — VERSÃO E EDIÇÃO
# ═══════════════════════════════════════════════════════════
def get_windows_info():
    base = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    product  = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "ProductName")
    build    = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "CurrentBuildNumber")
    ubr      = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "UBR", "0")
    edition  = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "EditionID")
    arch     = _read_reg(winreg.HKEY_LOCAL_MACHINE,
                         r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                         "PROCESSOR_ARCHITECTURE", "x64")
                         
    try:
        build_num = int(build)
        if build_num >= 22000 and "Windows 10" in product:
            product = product.replace("Windows 10", "Windows 11")
    except ValueError:
        pass
        
    return {
        "product": product,
        "edition": edition,
        "build":   f"{build}.{ubr}",
        "arch":    arch,
    }


# ═══════════════════════════════════════════════════════════
#  ATIVAÇÃO DO WINDOWS
# ═══════════════════════════════════════════════════════════
def get_windows_activation():
    # Usa PowerShell WMI para ser imune a idiomas (pt-BR, en-US)
    cmd = ["powershell", "-NoProfile", "-Command", 
           "Get-WmiObject -query 'select LicenseStatus, Description from SoftwareLicensingProduct where LicenseStatus = 1 and PartialProductKey is not null' | Select-Object LicenseStatus, Description | ConvertTo-Json"]
    out = _run(cmd, timeout=15)
    
    status = "⚠️ Não verificado"
    lic_type = "—"
    
    try:
        if out.strip():
            data = json.loads(out)
            if isinstance(data, list):
                data = data[0]
                
            if data.get("LicenseStatus") == 1:
                status = "✅ Ativado"
                
            desc = data.get("Description", "").upper()
            if "VOLUME" in desc: lic_type = "Volume"
            elif "RETAIL" in desc: lic_type = "Retail"
            elif "OEM" in desc: lic_type = "OEM"
            elif "TIMEBASED" in desc: lic_type = "KMS"
    except:
        pass
        
    # Fallback para slmgr caso WMI falhe
    if status == "⚠️ Não verificado":
        slmgr = r"C:\Windows\System32\slmgr.vbs"
        out_sl = _run(["cscript", "//NoLogo", slmgr, "/dstatus"], timeout=20)
        out_sl_lower = out_sl.lower()
        if "licensed" in out_sl_lower or "licenciado" in out_sl_lower:
            status = "✅ Ativado"
        elif "grace" in out_sl_lower or "graça" in out_sl_lower:
            status = "⏳ Período de graça"
            
        if "oem" in out_sl_lower: lic_type = "OEM"
        elif "retail" in out_sl_lower: lic_type = "Retail"
        elif "volume" in out_sl_lower: lic_type = "Volume"

    return {"status": status, "type": lic_type}


# ═══════════════════════════════════════════════════════════
#  ANTIVÍRUS (SecurityCenter2 e Defender Fallback)
# ═══════════════════════════════════════════════════════════
def get_antivirus_info():
    results = []
    # 1. Tentar ler todos os AVs registrados no WMI (Pode falhar no Win 11 para o Defender nativo)
    out = _run(["powershell", "-NoProfile", "-Command", 
                "Get-WmiObject -Namespace root\\SecurityCenter2 -Class AntiVirusProduct | Select-Object displayName, productState | ConvertTo-Json"], timeout=10)
    try:
        if out.strip():
            data = json.loads(out)
            if isinstance(data, dict): data = [data]
            for item in data:
                if not item: continue
                name = item.get("displayName", "Desconhecido")
                state = item.get("productState", 0)
                try:
                    enabled = (int(state) & 0x1000) != 0
                    updated = (int(state) & 0x10) == 0
                except ValueError:
                    enabled, updated = False, False
                results.append({"name": name, "enabled": enabled, "updated": updated})
    except:
        pass

    # 2. Se a lista estiver vazia, verifica o Defender diretamente
    if not results:
        def_out = _run(["powershell", "-NoProfile", "-Command", 
                        "Get-MpComputerStatus | Select-Object AMServiceEnabled, AntivirusSignatureAge | ConvertTo-Json"], timeout=10)
        try:
            if def_out.strip():
                d_data = json.loads(def_out)
                enabled = d_data.get("AMServiceEnabled", False)
                age = d_data.get("AntivirusSignatureAge", 99)
                updated = age < 7 # Assumimos atualizado se a assinatura tiver menos de 7 dias
                results.append({"name": "Windows Defender", "enabled": enabled, "updated": updated})
        except:
            pass

    return results if results else [{"name": "Nenhum detectado", "enabled": False, "updated": False}]


# ═══════════════════════════════════════════════════════════
#  FIREWALL
# ═══════════════════════════════════════════════════════════
def get_firewall_status():
    out = _run(["netsh", "advfirewall", "show", "allprofiles", "state"])
    profiles = {}
    current = None
    for line in out.splitlines():
        line = line.strip()
        if "Profile Settings" in line:
            current = line.split("Profile")[0].strip()
        elif "State" in line and current:
            val = "ON" if "ON" in line.upper() else "OFF"
            profiles[current] = val
    return profiles  # ex: {"Domain": "ON", "Private": "ON", "Public": "ON"}


# ═══════════════════════════════════════════════════════════
#  .NET FRAMEWORK
# ═══════════════════════════════════════════════════════════
def get_dotnet_version():
    base = r"SOFTWARE\Microsoft\NET Framework Setup\NDP"
    best = "Não encontrado"
    try:
        root = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(root, i)
                if sub.startswith("v"):
                    try:
                        k = winreg.OpenKey(root, sub + r"\Full")
                        ver, _ = winreg.QueryValueEx(k, "Version")
                        best = str(ver)
                        winreg.CloseKey(k)
                    except OSError:
                        try:
                            k2 = winreg.OpenKey(root, sub)
                            ver, _ = winreg.QueryValueEx(k2, "Version")
                            if best == "Não encontrado" or sub > best:
                                best = str(ver)
                            winreg.CloseKey(k2)
                        except OSError:
                            pass
                i += 1
            except OSError:
                break
        winreg.CloseKey(root)
    except OSError:
        pass
    # .NET Core / .NET 5+ via dotnet CLI
    out = _run(["dotnet", "--version"], timeout=8)
    if out and re.match(r"\d+\.\d+", out):
        core_ver = out.splitlines()[0].strip()
        return {"framework": best, "core": core_ver}
    return {"framework": best, "core": "Não encontrado"}


# ═══════════════════════════════════════════════════════════
#  JAVA
# ═══════════════════════════════════════════════════════════
def get_java_version():
    # JRE
    jre_ver = "Não encontrado"
    out = _run(["java", "-version"], timeout=8)
    if out:
        m = re.search(r'"([^"]+)"', out)
        if m:
            jre_ver = m.group(1)

    # JDK (javac)
    jdk_ver = "Não encontrado"
    out2 = _run(["javac", "-version"], timeout=8)
    if out2:
        parts = out2.strip().split()
        if len(parts) >= 2:
            jdk_ver = parts[1]

    return {"jre": jre_ver, "jdk": jdk_ver}


# ═══════════════════════════════════════════════════════════
#  DIRECTX
# ═══════════════════════════════════════════════════════════
def get_directx_version():
    ver = _read_reg(winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\DirectX", "Version", "")
    if ver:
        # converte formato 4.09.00.0904 → DirectX 9, etc.
        parts = ver.split(".")
        major = int(parts[1]) if len(parts) > 1 else 0
        names = {9: "DirectX 9", 10: "DirectX 10", 11: "DirectX 11",
                 12: "DirectX 12", 13: "DirectX 12 Ultimate"}
        return names.get(major, f"DirectX (build {ver})")
    return "Não detectado"


# ═══════════════════════════════════════════════════════════
#  VISUAL C++ REDISTRIBUTABLE
# ═══════════════════════════════════════════════════════════
def get_vcredist_versions():
    found = []
    for hive in [winreg.HKEY_LOCAL_MACHINE]:
        for base in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
            try:
                root = winreg.OpenKey(hive, base)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(root, i)
                        k = winreg.OpenKey(root, sub)
                        try:
                            name, _ = winreg.QueryValueEx(k, "DisplayName")
                            if "Visual C++" in str(name) and "Redistributable" in str(name):
                                ver_str, _ = winreg.QueryValueEx(k, "DisplayVersion")
                                entry = f"{name} ({ver_str})"
                                if entry not in found:
                                    found.append(entry)
                        except OSError:
                            pass
                        winreg.CloseKey(k)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(root)
            except OSError:
                pass
    return found if found else ["Nenhum detectado"]


# ═══════════════════════════════════════════════════════════
#  DEV SOFTWARE E BANCOS DE DADOS
# ═══════════════════════════════════════════════════════════
def get_dev_software():
    targets = [
        "Visual Studio", "Node.js", "Python", "Git ", "Git version",
        "Docker", "Postman", "DBeaver", "pgAdmin", "XAMPP", 
        "WAMP", "MySQL", "PostgreSQL", "SQL Server", "MongoDB", 
        "Redis", "Insomnia", "Android Studio", "IntelliJ", "Eclipse",
        "Sublime Text", "Wireshark", "VirtualBox", "VMware"
    ]
    found = []
    
    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        for base in [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                     r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"]:
            try:
                root = winreg.OpenKey(hive, base)
                i = 0
                while True:
                    try:
                        sub = winreg.EnumKey(root, i)
                        k = winreg.OpenKey(root, sub)
                        try:
                            name, _ = winreg.QueryValueEx(k, "DisplayName")
                            name_str = str(name)
                            
                            for t in targets:
                                if t.lower() in name_str.lower():
                                    # Normaliza o nome para o target conhecido
                                    t_clean = t.replace(" version", "").replace(" ", "").strip()
                                    if t_clean == "Git": t_clean = "Git" # Cleanup
                                    
                                    try:
                                        ver, _ = winreg.QueryValueEx(k, "DisplayVersion")
                                        entry = f"{t.replace(' version', '').strip()} ({ver})"
                                    except:
                                        entry = f"{t.replace(' version', '').strip()}"
                                    
                                    # Para SQL Server, vamos apenas registrar que existe, pois tem 50 pacotes.
                                    if "SQL Server" in t:
                                        entry = "Microsoft SQL Server"
                                    elif "Visual Studio" in t and "Code" not in name_str:
                                        if "Visual Studio 20" in name_str:
                                            entry = "Visual Studio (IDE)"
                                        else:
                                            # Skip redistributables being caught as Visual Studio
                                            continue
                                            
                                    if not any(e.startswith(entry.split(' (')[0]) for e in found):
                                        found.append(entry)
                        except OSError:
                            pass
                        winreg.CloseKey(k)
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(root)
            except OSError:
                pass
                
    found.sort()
    return found


# ═══════════════════════════════════════════════════════════
#  DISCOS FÍSICOS (SSD / HDD)
# ═══════════════════════════════════════════════════════════
def get_physical_disks():
    cmd = ["powershell", "-NoProfile", "-Command", 
           "Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size | ConvertTo-Json -Compress"]
    out = _run(cmd, timeout=10)
    if not out:
        return ["Nenhum disco detectado"]
    try:
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        disks = []
        for d in data:
            name = d.get("FriendlyName", "Desconhecido")
            media = str(d.get("MediaType", "Desconhecido")).upper()
            if media == "3": media = "HDD"
            elif media == "4": media = "SSD"
            elif media == "5": media = "SCM"
            elif media == "0" or media == "UNSPECIFIED": media = "Desconhecido"
            
            size_b = d.get("Size", 0)
            size_gb = size_b / (1024**3) if size_b else 0
            disks.append(f"[{media}] {name} ({size_gb:.0f} GB)")
        return disks
    except Exception:
        return ["Erro ao ler discos"]


# ═══════════════════════════════════════════════════════════
#  RELATÓRIO COMPLETO
# ═══════════════════════════════════════════════════════════
def get_full_system_report():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        f_windows    = executor.submit(get_windows_info)
        f_activation = executor.submit(get_windows_activation)
        f_antivirus  = executor.submit(get_antivirus_info)
        f_firewall   = executor.submit(get_firewall_status)
        f_dotnet     = executor.submit(get_dotnet_version)
        f_java       = executor.submit(get_java_version)
        f_directx    = executor.submit(get_directx_version)
        f_vcredist   = executor.submit(get_vcredist_versions)
        f_dev_tools  = executor.submit(get_dev_software)
        f_disks      = executor.submit(get_physical_disks)

    return {
        "windows":    f_windows.result(),
        "activation": f_activation.result(),
        "antivirus":  f_antivirus.result(),
        "firewall":   f_firewall.result(),
        "dotnet":     f_dotnet.result(),
        "java":       f_java.result(),
        "directx":    f_directx.result(),
        "vcredist":   f_vcredist.result(),
        "dev_tools":  f_dev_tools.result(),
        "disks":      f_disks.result(),
    }
