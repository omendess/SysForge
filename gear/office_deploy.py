import subprocess
import os
import sys

CREATE_NO_WINDOW = 0x08000000

def obter_caminho_base():
    """
    Retorna o caminho do diretório base do aplicativo.
    Funciona tanto ao rodar via script (.py) quanto via executável (PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        # Quando compilado com PyInstaller --add-data, os arquivos ficam na pasta temporária _MEIPASS
        return sys._MEIPASS
    else:
        # Se rodando via script .py, usa o caminho deste arquivo subindo até a raiz SysForge
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def install_and_activate_office(status_callback=None):
    base_dir = obter_caminho_base()
    office_dir = os.path.join(base_dir, "OfficeInstall")
    setup_exe = os.path.join(office_dir, "setup.exe")
    config_xml = os.path.join(office_dir, "config.xml")
    
    # 1. Install
    if os.path.exists(setup_exe) and os.path.exists(config_xml):
        if status_callback:
            status_callback("Instalando Office LTSC... A janela do instalador aparecerá em breve.")
        try:
            # Força o Display Level="Full" para que o usuário veja o progresso
            import tempfile
            with open(config_xml, "r", encoding="utf-8") as f:
                xml_data = f.read()
            xml_data = xml_data.replace('Level="None"', 'Level="Full"')
            
            run_config = os.path.join(tempfile.gettempdir(), "config_run.xml")
            with open(run_config, "w", encoding="utf-8") as f:
                f.write(xml_data)

            from gear.window_enforcer import enforce_window_rules
            # Rodar setup.exe
            p = subprocess.Popen([setup_exe, "/configure", run_config], cwd=office_dir, creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            enforce_window_rules(p.pid, duration=1800) # Office can take a while
            p.wait()
            
            # Cleanup temp
            try: os.remove(run_config)
            except: pass

            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, "setup.exe")
        except subprocess.CalledProcessError as e:
            if status_callback:
                status_callback(f"Erro na instalação do Office (Código {e.returncode}).")
            return
        except Exception as e:
            if status_callback:
                status_callback(f"Falha ao iniciar o Office: {str(e)}")
            return
    else:
        if status_callback:
            status_callback(f"Falta setup.exe em: {setup_exe}")
        return
        
    # 2. Activate
    if status_callback:
        status_callback("Ativando Office LTSC (MAS)...")
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0 # SW_HIDE
        
        cmd = ["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; & ([ScriptBlock]::Create((irm https://get.activated.win))) /Ohook /S"]
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if status_callback:
            status_callback("Office instalado e ativado com sucesso.")
    except subprocess.CalledProcessError as e:
        if status_callback:
            status_callback(f"Erro ao ativar o Office (Código {e.returncode}).")
