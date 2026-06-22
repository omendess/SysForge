import os
import subprocess
import time
import shutil
import psutil

UWP_PACKAGES = {
    "Clipchamp": "Clipchamp.Clipchamp",
    "Clima": "Microsoft.BingWeather",
    "Cortana": "Microsoft.549981C3F5F10",
    "Dicas": "Microsoft.Getstarted",
    "Hub de Comentários": "Microsoft.WindowsFeedbackHub",
    "Link do Telefone": "Microsoft.YourPhone",
    "Notícias": "Microsoft.BingNews",
    "Microsoft Teams": "MicrosoftTeams",
    "Microsoft Teams (Appx)": "Microsoft.Teams",
    "Microsoft To Do": "Microsoft.Todos",
    "Pacote do Office (Hub)": "Microsoft.MicrosoftOfficeHub",
    "Pessoas": "Microsoft.People",
    "Solitário": "Microsoft.MicrosoftSolitaireCollection",
    "Xbox App": "Microsoft.XboxApp",
    "Xbox Game Bar": "Microsoft.XboxGamingOverlay",
    "Xbox Speech": "Microsoft.XboxSpeechToTextOverlay",
    "Xbox Identity": "Microsoft.XboxIdentityProvider"
}

OFFICE_PROCESSES = [
    "WINWORD.EXE", "EXCEL.EXE", "POWERPNT.EXE", "OUTLOOK.EXE",
    "MSACCESS.EXE", "MSPUB.EXE", "OfficeClickToRun.exe", 
    "OfficeC2RClient.exe", "Teams.exe", "msteams.exe"
]

def _run_ps(cmd):
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], 
                       creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
    except:
        pass

def _run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
    except:
        pass

def executar_esterilizacao(status_callback, progress_callback=None):
    total_steps = len(UWP_PACKAGES) + 4 # 4 passos adicionais para o Office
    current_step = 0
    
    def update_progress(desc):
        nonlocal current_step
        current_step += 1
        pct = int((current_step / total_steps) * 100)
        msg = f"--------------{pct}% {desc}..."
        status_callback(msg)
        if progress_callback:
            progress_callback(pct / 100.0)

    # 1. Remover Bloatware UWP
    for name, pkg in UWP_PACKAGES.items():
        update_progress(f"removendo {name}")
        _run_ps(f"Get-AppxPackage -AllUsers *{pkg}* | Remove-AppxPackage -ErrorAction SilentlyContinue")
        _run_ps(f"Get-AppxProvisionedPackage -Online | Where-Object DisplayName -like *{pkg}* | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue")

    # 2. Finalizar Processos do Office
    update_progress("finalizando processos do Office e Serviços")
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].upper() in [p.upper() for p in OFFICE_PROCESSES]:
                proc.kill()
        except:
            pass
            
    _run_cmd("sc stop ClickToRunSvc")
    _run_cmd("sc delete ClickToRunSvc")
    _run_cmd("sc stop OfficeSvc")
    _run_cmd("sc delete OfficeSvc")
    
    time.sleep(1) # Espera processos morrerem

    # 3. Limpeza de Arquivos do Office
    update_progress("apagando rastros físicos do Office")
    pf = os.environ.get("ProgramFiles", "C:\\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    pd = os.environ.get("ProgramData", "C:\\ProgramData")
    
    paths_to_delete = [
        os.path.join(pf, "Microsoft Office"),
        os.path.join(pf86, "Microsoft Office"),
        os.path.join(pd, "Microsoft", "Office")
    ]
    
    for path in paths_to_delete:
        if os.path.exists(path):
            try:
                shutil.rmtree(path, ignore_errors=True)
            except:
                pass

    # 4. Limpeza de Registro do Office & Bloatware
    update_progress("expurgando chaves de registro (Licenças)")
    reg_cmds = [
        r'reg delete "HKLM\SOFTWARE\Microsoft\Office" /f',
        r'reg delete "HKCU\SOFTWARE\Microsoft\Office" /f',
        r'reg delete "HKLM\SOFTWARE\WOW6432Node\Microsoft\Office" /f',
        # Cortana block
        r'reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search" /v AllowCortana /t REG_DWORD /d 0 /f'
    ]
    for cmd in reg_cmds:
        _run_cmd(cmd)

    # Finalizado
    update_progress("finalizando esterilização")
    status_callback("✅ Esterilização Profunda Concluída.")
    if progress_callback:
        progress_callback(1.0)
