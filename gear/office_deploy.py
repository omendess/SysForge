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
        # Se rodando via PyInstaller, o executável real está em sys.executable
        # sys._MEIPASS é a pasta temporária. Queremos o diretório onde o .exe está
        # para encontrar a pasta OfficeInstall que está ao lado dele.
        return os.path.dirname(sys.executable)
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
            subprocess.run([setup_exe, "/configure", config_xml], cwd=office_dir, creationflags=CREATE_NO_WINDOW, check=True)
        except subprocess.CalledProcessError:
            if status_callback:
                status_callback("Erro na instalação do Office.")
            return
    else:
        if status_callback:
            status_callback("Arquivos de instalação do Office não encontrados. Pulando...")
        return
        
    # 2. Activate
    if status_callback:
        status_callback("Ativando Office LTSC (MAS)...")
    try:
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "irm https://get.activated.win | iex"]
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, check=True)
        if status_callback:
            status_callback("Office instalado e ativado com sucesso.")
    except subprocess.CalledProcessError:
        if status_callback:
            status_callback("Erro ao ativar o Office.")
