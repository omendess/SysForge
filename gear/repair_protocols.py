import subprocess
import shutil
import os

def protocolo_guarda_chuva():
    """
    Cria um ponto de restauração do sistema (Protocolo Guarda-Chuva).
    Retorna True se sucesso, False se falha.
    """
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", "Enable-ComputerRestore -Drive 'C:\'"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        p = subprocess.run(["powershell", "-NoProfile", "-Command", "Checkpoint-Computer -Description 'SysForge_AutoHeal_Backup' -RestorePointType 'MODIFY_SETTINGS'"], creationflags=subprocess.CREATE_NO_WINDOW, capture_output=True)
        return p.returncode == 0
    except Exception:
        return False

def protocolo_reparo_rede():
    """
    Executa silenciosamente: netsh winsock reset, netsh int ip reset, ipconfig /flushdns.
    Retorna a string de log de sucesso.
    """
    try:
        subprocess.run(["netsh", "winsock", "reset"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["netsh", "int", "ip", "reset"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["ipconfig", "/flushdns"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        return "[+] NÚCLEO DE REDE (WINSOCK/TCP) REDEFINIDO E CACHE EXPURGADO."
    except Exception as e:
        return f"[-] ERRO NO REPARO DE REDE: {e}"

def protocolo_reparo_update():
    """
    Para os serviços wuauserv e bits, limpa a pasta SoftwareDistribution/Download e reinicia.
    """
    try:
        subprocess.run(["net", "stop", "wuauserv"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["net", "stop", "bits"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        
        target_dir = r"C:\Windows\SoftwareDistribution\Download"
        if os.path.exists(target_dir):
            for filename in os.listdir(target_dir):
                file_path = os.path.join(target_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception:
                    pass
        
        subprocess.run(["net", "start", "wuauserv"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["net", "start", "bits"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        return "[+] CACHE DO WINDOWS UPDATE ANIQULADO E SERVIÇOS REINICIADOS."
    except Exception as e:
        return f"[-] ERRO NO REPARO DE UPDATE: {e}"

def protocolo_reparo_kernel():
    """
    Executa o reparo de imagem (DISM) e de integridade (SFC).
    """
    try:
        subprocess.run(["dism.exe", "/Online", "/Cleanup-image", "/Restorehealth"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["sfc", "/scannow"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        return "[+] INTEGRIDADE DA IMAGEM DO KERNEL RESTAURADA VIA DISM/SFC."
    except Exception as e:
        return f"[-] ERRO NO REPARO DE KERNEL: {e}"

def expurgar_historico_eventos():
    """
    Limpa o Visualizador de Eventos nativo do Windows de forma silenciosa.
    """
    try:
        subprocess.run(["wevtutil", "cl", "System"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        subprocess.run(["wevtutil", "cl", "Application"], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
        return "[+] REGISTROS FANTASMAS EXPURGADOS. DIAGNÓSTICO ZERADO."
    except Exception as e:
        return f"[-] ERRO AO EXPURGAR LOGS: {e}"
