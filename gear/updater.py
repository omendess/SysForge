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
import sys
import threading
import subprocess
import urllib.request
import json
import zipfile

CURRENT_VERSION = "2.6.1.1"

# Exemplo de URL. Para funcionar, crie um arquivo version.json no repositório do GitHub e substitua essa URL pela URL *RAW* do arquivo.
# O version.json deve ter: {"version": "2.0.1", "download_url": "https://github.com/omendess/SysForge/archive/refs/heads/main.zip", "changelog": "Novas correções."}
UPDATE_URL = "https://raw.githubusercontent.com/omendess/SysForge/main/version.json"

def check_for_updates(root_window, manual=False):
    """Verifica se há atualizações no GitHub e notifica o usuário."""
    def _check():
        try:
            import time
            cache_buster_url = f"{UPDATE_URL}?t={int(time.time())}"
            req = urllib.request.Request(cache_buster_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                latest_version = data.get("version", CURRENT_VERSION)
                download_url = data.get("download_url", "")
                changelog = data.get("changelog", "Melhorias de estabilidade e segurança.")
                
                if latest_version > CURRENT_VERSION:
                    root_window.after(0, lambda: _show_update_dialog(root_window, latest_version, download_url, changelog))
                elif manual:
                    root_window.after(0, lambda: _show_no_update_dialog(root_window))
        except Exception as e:
            print("Erro ao buscar atualizações (O GitHub pode estar inacessível ou URL não configurada).", e)
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
    
    import sys, os
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
    
    def apply_update():
        dialog.destroy()
        _start_update_process(download_url, root_window)
        
    ctk.CTkButton(btn_frame, text="Atualizar Agora", fg_color="#16A34A", hover_color="#15803D", command=apply_update).pack(side="left", expand=True, padx=5)
    ctk.CTkButton(btn_frame, text="Lembrar Depois", fg_color="#334155", hover_color="#1E293B", command=dialog.destroy).pack(side="right", expand=True, padx=5)

def _start_update_process(download_url, root_window):
    import sys, os, subprocess
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
        exe_dir = os.path.dirname(exe_path)
        
        ps_script = os.path.join(os.environ.get("TEMP", exe_dir), "sysforge_updater.ps1")
        
        old_exe = exe_path + ".old"
        ps_code = f"""
        Start-Sleep -Seconds 3
        $procName = [System.IO.Path]::GetFileNameWithoutExtension('{exe_path}')
        Get-Process -Name $procName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        
        Rename-Item -Path '{exe_path}' -NewName '{os.path.basename(old_exe)}' -Force -ErrorAction SilentlyContinue
        Invoke-WebRequest -Uri '{download_url}' -OutFile '{exe_path}'
        Start-Process -FilePath '{exe_path}'
        Remove-Item -Path '{ps_script}' -Force
        """
        
        try:
            with open(ps_script, "w", encoding="utf-8") as f:
                f.write(ps_code)
                
            clean_env = os.environ.copy()
            clean_env.pop("_MEIPASS2", None)
            clean_env.pop("_MEIPASS", None)
                
            subprocess.Popen(
                ["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", ps_script],
                creationflags=0x08000000,
                env=clean_env
            )
            os._exit(0)
        except Exception as e:
            status_label.configure(text=f"Erro fatal: {e}")
            root_window.update()
    else:
        status_label.configure(text="Atualização automática só funciona na versão compilada (.exe)")
        root_window.update()

def execute_update_mode(download_url, target_dir):
    pass
