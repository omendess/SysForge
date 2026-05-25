import os
import sys
import threading
import subprocess
import urllib.request
import json
import zipfile

CURRENT_VERSION = "2.0.0"

# Exemplo de URL. Para funcionar, crie um arquivo version.json no repositório do GitHub e substitua essa URL pela URL *RAW* do arquivo.
# O version.json deve ter: {"version": "2.0.1", "download_url": "https://github.com/USER/SysForge/archive/refs/heads/main.zip", "changelog": "Novas correções."}
UPDATE_URL = "https://raw.githubusercontent.com/SEU_USUARIO/SysForge/main/version.json"

def check_for_updates(root_window):
    """Verifica se há atualizações no GitHub e notifica o usuário."""
    def _check():
        try:
            req = urllib.request.Request(UPDATE_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get("version", CURRENT_VERSION)
                download_url = data.get("download_url", "")
                changelog = data.get("changelog", "Melhorias de estabilidade e segurança.")
                
                if latest_version > CURRENT_VERSION:
                    root_window.after(2000, lambda: _show_update_dialog(root_window, latest_version, download_url, changelog))
        except Exception as e:
            print("Erro ao buscar atualizações (O GitHub pode estar inacessível ou URL não configurada).", e)

    threading.Thread(target=_check, daemon=True).start()

def _show_update_dialog(root_window, new_version, download_url, changelog):
    import customtkinter as ctk
    
    dialog = ctk.CTkToplevel(root_window)
    dialog.title("Atualização Disponível!")
    dialog.geometry("450x250")
    dialog.attributes("-topmost", True)
    dialog.resizable(False, False)
    
    # Centralizar Popup
    dialog.update_idletasks()
    x = root_window.winfo_x() + (root_window.winfo_width() // 2) - (450 // 2)
    y = root_window.winfo_y() + (root_window.winfo_height() // 2) - (250 // 2)
    dialog.geometry(f"+{x}+{y}")
    
    ctk.CTkLabel(dialog, text=f"SysForge {new_version} está disponível!", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5))
    ctk.CTkLabel(dialog, text=f"Versão atual: {CURRENT_VERSION}", font=ctk.CTkFont(size=12), text_color="gray").pack()
    
    ctk.CTkLabel(dialog, text=f"Novidades:\n{changelog}", font=ctk.CTkFont(size=13), justify="center").pack(pady=(15, 20))
    
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=40)
    
    def apply_update():
        dialog.destroy()
        _start_update_process(download_url, root_window)
        
    ctk.CTkButton(btn_frame, text="Atualizar Agora", fg_color="#16A34A", hover_color="#15803D", command=apply_update).pack(side="left", expand=True, padx=5)
    ctk.CTkButton(btn_frame, text="Lembrar Depois", fg_color="#334155", hover_color="#1E293B", command=dialog.destroy).pack(side="right", expand=True, padx=5)

def _start_update_process(download_url, root_window):
    # Cria o script temporário que fará a extração em background e o substitui
    updater_script = os.path.join(os.getcwd(), "update_runner.py")
    
    script_content = f'''import urllib.request
import zipfile
import os
import time
import subprocess
import sys

print("Aguardando o SysForge fechar...")
time.sleep(3)

print("Baixando atualização do SysForge...")
try:
    req = urllib.request.Request("{download_url}", headers={{'User-Agent': 'Mozilla/5.0'}})
    with urllib.request.urlopen(req) as response, open("update.zip", "wb") as out_file:
        out_file.write(response.read())

    print("Extraindo e substituindo os arquivos...")
    with zipfile.ZipFile("update.zip", 'r') as zip_ref:
        for member in zip_ref.namelist():
            # Ignora a pasta raiz gerada pelo ZIP do GitHub (ex: SysForge-main/)
            parts = member.split('/')
            if len(parts) > 1:
                target_path = os.path.join(os.getcwd(), *parts[1:])
                if member.endswith('/'):
                    os.makedirs(target_path, exist_ok=True)
                else:
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with zip_ref.open(member) as source, open(target_path, "wb") as target:
                        target.write(source.read())
    
    os.remove("update.zip")
    print("Atualização concluída com sucesso! Reiniciando SysForge...")
except Exception as e:
    print(f"Ocorreu um erro durante a atualização: {{e}}")
    input("Pressione Enter para sair...")

# Reinicia a versão nova do SysForge
subprocess.Popen([sys.executable, "main.py"], creationflags=0x08000000)

# Deleta esse próprio arquivo update_runner.py para manter a pasta limpa
try: os.remove(__file__)
except: pass
'''
    with open(updater_script, "w", encoding="utf-8") as f:
        f.write(script_content)
        
    # Inicia o updater como processo independente (abrindo console para ver progresso)
    subprocess.Popen([sys.executable, "update_runner.py"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    
    # Encerra completamente a UI
    root_window.quit()
    root_window.destroy()
    sys.exit(0)
