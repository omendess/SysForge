import subprocess
import os
import platform

CREATE_NO_WINDOW = 0x08000000

def activate_windows(status_callback=None):
    if status_callback:
        status_callback("Ativando Windows (HWID Digital License)...")
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE
        
        cmd = ["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; & ([ScriptBlock]::Create((irm https://get.activated.win))) /HWID /S"]
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if status_callback:
            status_callback("✅ Windows ativado com sucesso (Licença Digital).")
    except subprocess.CalledProcessError as e:
        if status_callback:
            status_callback(f"❌ Erro ao ativar o Windows (Código {e.returncode}).")

def capture_product_keys(status_callback=None):
    if status_callback:
        status_callback("Extraindo Product Keys do sistema...")
        
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    backup_file = os.path.join(desktop, "SysForge_ProductKeys.txt")
    
    keys_found = []
    
    # 1. Obter chave OEM do Windows via WMIC (Integrada na BIOS/Placa-mãe)
    try:
        wmic_cmd = ["wmic", "path", "softwarelicensingservice", "get", "OA3xOriginalProductKey"]
        result = subprocess.run(wmic_cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True)
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if len(lines) > 1 and lines[1] != "":
            keys_found.append(f"Windows (OEM BIOS/UEFI): {lines[1]}")
    except:
        pass
        
    # 2. Obter chave do Windows via Registro (Retail Key) via PowerShell
    decode_ps = r"""
    $path = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    try {
        $id = (Get-ItemProperty $path).DigitalProductId[52..66]
        $chars = 'BCDFGHJKMPQRTVWXY2346789'
        $key = ''
        for ($i = 24; $i -ge 0; $i--) {
            $k = 0
            for ($j = 14; $j -ge 0; $j--) {
                $k = ($k * 256) -bxor $id[$j]
                $id[$j] = [math]::truncate($k / 24)
                $k = $k % 24
            }
            $key = $chars[$k] + $key
            if (($i % 5) -eq 0 -and $i -ne 0) { $key = '-' + $key }
        }
        Write-Output $key
    } catch {}
    """
    try:
        ps_cmd = ["powershell", "-NoProfile", "-Command", decode_ps]
        result = subprocess.run(ps_cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True)
        val = result.stdout.strip()
        if val and len(val) == 29: # Formato 25 chars + 4 dashes
            keys_found.append(f"Windows (Registro/Retail): {val}")
    except:
        pass
        
    # 3. Tentar ler chaves do Office (últimos 5 dígitos ou chave local) via OSPP
    ospp_paths = [
        r"C:\Program Files\Microsoft Office\Office16\OSPP.VBS",
        r"C:\Program Files (x86)\Microsoft Office\Office16\OSPP.VBS"
    ]
    for path in ospp_paths:
        if os.path.exists(path):
            try:
                cmd = ["cscript", path, "/dstatus"]
                result = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True)
                office_data = []
                current_name = ""
                for line in result.stdout.splitlines():
                    if "LICENSE NAME:" in line:
                        current_name = line.split(":", 1)[1].strip()
                    if "Last 5 characters of installed product key:" in line:
                        last_5 = line.split(":", 1)[1].strip()
                        office_data.append(f"Office ({current_name}): *****-*****-*****-*****-{last_5}")
                keys_found.extend(office_data)
            except:
                pass
            break
            
    if not keys_found:
        if status_callback:
            status_callback("Nenhuma Product Key encontrada de forma legível.")
        return
        
    # Salvar no arquivo
    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write("=== BACKUP DE PRODUCT KEYS (SysForge) ===\n")
            f.write("Guarde este arquivo em um Pen Drive antes de formatar!\n\n")
            
            f.write("NOTA SOBRE O OFFICE: Nas versões modernas do Office (2013+), a Microsoft não armazena\n")
            f.write("a Product Key completa no computador por questões de segurança. Ela fica vinculada\n")
            f.write("à sua conta Microsoft (online) e o PC só guarda os últimos 5 dígitos para identificação.\n")
            f.write("Por isso, você só verá os últimos 5 caracteres do Office abaixo.\n\n")
            
            # Remover duplicatas mantendo a ordem
            seen = set()
            for k in keys_found:
                val = k.split(":", 1)[-1].strip()
                if val and val not in seen and val != "OA3xOriginalProductKey":
                    seen.add(val)
                    f.write(f"{k}\n")
        
        if status_callback:
            status_callback(f"✅ Keys salvas na Área de Trabalho (SysForge_ProductKeys.txt)")
    except Exception as e:
        if status_callback:
            status_callback(f"❌ Erro ao salvar chaves: {str(e)}")
