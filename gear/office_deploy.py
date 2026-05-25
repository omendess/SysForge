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
            status_callback("Instalando Office LTSC silenciosamente...")
        try:
            # Executa a instalação a partir do diretório OfficeInstall
            # Passando stdout/stderr para DEVNULL para evitar crash em modo windowed do PyInstaller
            subprocess.run([setup_exe, "/configure", config_xml], cwd=office_dir, creationflags=CREATE_NO_WINDOW, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
        
        cmd = ["powershell.exe", "-WindowStyle", "Hidden", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "& ([ScriptBlock]::Create((irm https://get.activated.win))) /Ohook /S"]
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, startupinfo=startupinfo, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if status_callback:
            status_callback("Office instalado e ativado com sucesso.")
    except subprocess.CalledProcessError as e:
        if status_callback:
            status_callback(f"Erro ao ativar o Office (Código {e.returncode}).")
