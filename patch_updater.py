import os

with open('gear/updater.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir _start_update_process e execute_update_mode por completo
old_block_start = "def _start_update_process(download_url, root_window):"

idx = content.find(old_block_start)
if idx != -1:
    content = content[:idx]

new_update_logic = '''def _start_update_process(download_url, root_window):
    import sys, os, subprocess
    import customtkinter as ctk
    
    loading_frame = ctk.CTkFrame(root_window, fg_color="#0F172A", corner_radius=0)
    loading_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
    ctk.CTkLabel(loading_frame, text="Atualização do SysForge", font=("Inter", 24, "bold"), text_color="#F8FAFC").place(relx=0.5, rely=0.35, anchor="center")
    status_label = ctk.CTkLabel(loading_frame, text="Baixando atualização...", font=("Inter", 14), text_color="#94A3B8")
    status_label.place(relx=0.5, rely=0.45, anchor="center")
    root_window.update()
    
    is_compiled = getattr(sys, 'frozen', False)
    
    if is_compiled:
        exe_path = sys.executable
        exe_dir = os.path.dirname(exe_path)
        
        ps_script = os.path.join(os.environ.get("TEMP", exe_dir), "sysforge_updater.ps1")
        
        # PowerShell script que aguarda o SysForge fechar, baixa o zip, extrai e o reinicia
        ps_code = f\"\"\"
        Start-Sleep -Seconds 3
        \\ = "\\C:\Users\o_men\AppData\Local\Temp\\\\sysforge_update.zip"
        Invoke-WebRequest -Uri '{download_url}' -OutFile \\
        Expand-Archive -Path \\ -DestinationPath '{exe_dir}' -Force
        Remove-Item -Path \\ -Force
        Start-Process -FilePath '{exe_path}'
        Remove-Item -Path '{ps_script}' -Force
        \"\"\"
        
        try:
            with open(ps_script, "w", encoding="utf-8") as f:
                f.write(ps_code)
                
            # Executa o script PS no modo invisivel de forma independente
            subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", ps_script], creationflags=0x08000000)
            
            # Encerra o App
            os._exit(0)
        except Exception as e:
            status_label.configure(text=f"Erro fatal: {e}")
            root_window.update()
    else:
        status_label.configure(text="Atualização automática só funciona na versão compilada (.exe)")
        root_window.update()

def execute_update_mode(download_url, target_dir):
    # Função obsoleta. Mantida apenas para compatibilidade caso o entrypoint chame, mas não será mais usada.
    pass
'''

content += new_update_logic

with open('gear/updater.py', 'w', encoding='utf-8') as f:
    f.write(content)
