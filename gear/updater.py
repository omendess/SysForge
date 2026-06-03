import sys
if sys.stdout is None:
    class Dummy:
        def write(self, *a):
            pass
        def flush(self):
            pass
    sys.stdout = Dummy()
    sys.stderr = Dummy()
import os
import threading
import subprocess
import urllib.request
import json

CURRENT_VERSION = "1.0.1"

API_URL = "https://api.github.com/repos/omendess/SysForge/releases/latest"


def _compare_versions(v1, v2):
    """Comparação semântica de versões. Retorna True se v2 > v1."""
    try:
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        # Pad shorter list with zeros
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))
        return parts2 > parts1
    except (ValueError, AttributeError):
        return False


def check_for_updates(root_window, manual=False):
    """Verifica se há atualizações no GitHub e notifica o usuário."""
    def _check():
        try:
            import time
            cache_buster_url = f"{API_URL}?t={int(time.time())}"
            headers = {"User-Agent": "SysForge-Updater", "Accept": "application/vnd.github.v3+json"}
            req = urllib.request.Request(cache_buster_url, headers=headers)
            try:
                response = urllib.request.urlopen(req, timeout=8)
                if response.getcode() != 200:
                    print(f"Erro API: {response.getcode()}")
                data = json.loads(response.read().decode())
            except urllib.error.HTTPError as e:
                print(f"Erro API: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
                raise e
                from gear.build_config import IS_PORTABLE
                
                tag_name = data.get("tag_name", "")
                latest_version = tag_name.lstrip("v") if tag_name else CURRENT_VERSION
                
                download_url = ""
                if IS_PORTABLE:
                    assets = data.get("assets", [])
                    for asset in assets:
                        if "SysForge_Portable" in asset.get("name", ""):
                            download_url = asset.get("browser_download_url", "")
                            break
                else:
                    download_url = data.get("html_url", "https://github.com/omendess/SysForge/releases/latest")
                    
                changelog = data.get("body", "Melhorias de estabilidade e segurança.")
                
                if _compare_versions(CURRENT_VERSION, latest_version):
                    root_window.after(0, lambda: _show_update_dialog(root_window, latest_version, download_url, changelog))
                elif manual:
                    root_window.after(0, lambda: _show_no_update_dialog(root_window))
        except Exception as e:
            print("Erro ao buscar atualizações:", e)
            if manual:
                root_window.after(0, lambda: _show_error_dialog(root_window))

    threading.Thread(target=_check, daemon=True).start()

def _show_no_update_dialog(root_window):
    from tkinter import messagebox
    messagebox.showinfo("Atualização", f"O SysForge já está na última versão ({CURRENT_VERSION}).")

def _show_error_dialog(root_window):
    from tkinter import messagebox
    messagebox.showerror("Erro", "Não foi possível verificar atualizações. Verifique sua conexão com a internet ou configuração do GitHub.")

def _show_update_dialog(root_window, new_version, download_url, changelog):
    import customtkinter as ctk
    
    dialog = ctk.CTkToplevel(root_window)
    dialog.title("Atualização Disponível!")
    dialog.geometry("450x300")
    dialog.attributes("-topmost", True)
    dialog.resizable(False, False)
    
    base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    icon_path = os.path.join(base_dir, "icon.ico")
    if os.path.exists(icon_path):
        try: dialog.iconbitmap(icon_path)
        except: pass

    
    # Centralizar Popup
    dialog.update_idletasks()
    x = root_window.winfo_x() + (root_window.winfo_width() // 2) - (450 // 2)
    y = root_window.winfo_y() + (root_window.winfo_height() // 2) - (300 // 2)
    dialog.geometry(f"+{x}+{y}")
    
    ctk.CTkLabel(dialog, text=f"SysForge {new_version} está disponível!", font=ctk.CTkFont(size=18, weight="bold"), text_color="#3B82F6").pack(pady=(20, 5))
    ctk.CTkLabel(dialog, text=f"Versão atual: {CURRENT_VERSION}", font=ctk.CTkFont(size=12), text_color="gray").pack()
    
    ctk.CTkLabel(dialog, text=f"Novidades:\n{changelog}", font=ctk.CTkFont(size=13), justify="center", wraplength=400).pack(pady=(15, 20), padx=20)
    
    btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
    btn_frame.pack(fill="x", padx=40)
    
    from gear.build_config import IS_PORTABLE

    def apply_update():
        dialog.destroy()
        if IS_PORTABLE:
            _start_update_process(download_url, root_window)
        else:
            import webbrowser
            webbrowser.open(download_url)
            
    btn_text = "Atualizar Agora" if IS_PORTABLE else "Baixar Novo Instalador"
    ctk.CTkButton(btn_frame, text=btn_text, fg_color="#16A34A", hover_color="#15803D", command=apply_update).pack(side="left", expand=True, padx=5)
    ctk.CTkButton(btn_frame, text="Lembrar Depois", fg_color="#334155", hover_color="#1E293B", command=dialog.destroy).pack(side="right", expand=True, padx=5)

def _start_update_process(download_url, root_window):
    import customtkinter as ctk
    
    loading_frame = ctk.CTkFrame(root_window, fg_color="#0F172A", corner_radius=0)
    loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    ctk.CTkLabel(loading_frame, text="Atualização do SysForge", font=("Inter", 24, "bold"), text_color="#F8FAFC").place(relx=0.5, rely=0.35, anchor="center")
    status_label = ctk.CTkLabel(loading_frame, text="Baixando atualização em Background...", font=("Inter", 14), text_color="#94A3B8")
    status_label.place(relx=0.5, rely=0.45, anchor="center")
    root_window.update()
    
    is_compiled = getattr(sys, 'frozen', False)
    
    if is_compiled:
        exe_path = sys.executable
        exe_old = exe_path + ".old"
        exe_new = exe_path + ".new"
        
        try:
            # 1. Tentar deletar um arquivo .old residual
            if os.path.exists(exe_old):
                try:
                    os.remove(exe_old)
                except:
                    pass
            
            # 2. Baixar o novo executável temporariamente
            import urllib.request
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response, open(exe_new, 'wb') as out_file:
                out_file.write(response.read())
            
            # Validar se baixou algo razoável (> 1MB)
            if os.path.getsize(exe_new) < 1048576:
                raise Exception("Arquivo corrompido ou download incompleto.")
                
            # 3. Ghost Rename (Renomear o executável VIVO)
            os.rename(exe_path, exe_old)
            
            # 4. Mover o novo para o nome original
            os.rename(exe_new, exe_path)
            
            # 5. Limpar variáveis de ambiente e reiniciar
            if "_MEIPASS2" in os.environ:
                del os.environ["_MEIPASS2"]
            if "_MEIPASS" in os.environ:
                del os.environ["_MEIPASS"]
                
            subprocess.Popen([exe_path], creationflags=0x08000000)
            os._exit(0)
            
        except Exception as e:
            status_label.configure(text=f"Erro fatal: {e}")
            root_window.update()
            # Limpeza caso falhe
            if os.path.exists(exe_new):
                try: os.remove(exe_new)
                except: pass
    else:
        status_label.configure(text="Atualização automática só funciona na versão compilada (.exe)")
        root_window.update()

def execute_update_mode(download_url, target_dir):
    pass
