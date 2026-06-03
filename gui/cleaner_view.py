import customtkinter as ctk
import threading
from gear.cleaner_engine import obter_alvos_ativos, calcular_lixo, executar_limpeza, verificar_navegadores_abertos, encerrar_navegadores

def build_cleaner_view(view):
    # Header
    header = ctk.CTkFrame(view, fg_color="transparent")
    header.pack(fill="x", pady=(0, 6))
    
    ctk.CTkLabel(header, text="LIMPEZA PERSONALIZADA", font=("Helvetica", 24, "bold"), text_color="#000000").pack(anchor="w", padx=4)
    ctk.CTkLabel(header, text="SELEÇÃO AVANÇADA E EXPURGO PROFUNDO DE SISTEMA", font=("Consolas", 12), text_color="#000000").pack(anchor="w", padx=4, pady=(2, 0))

    # Main Area (Central)
    main_area = ctk.CTkFrame(view, fg_color="transparent")
    main_area.pack(fill="both", expand=True, pady=(10, 10))

    scroll = ctk.CTkScrollableFrame(main_area, fg_color="#FFFFFF", border_width=1, border_color="#000000", corner_radius=0)
    scroll.pack(fill="both", expand=True)

    checkbox_vars = {}
    alvos_ativos = obter_alvos_ativos()
    
    def toggle_accordion(btn, frame):
        if frame.winfo_ismapped():
            frame.pack_forget()
            btn.configure(text=btn.cget("text").replace("▼", "▶"))
        else:
            frame.pack(fill="x", padx=10, pady=(0, 10))
            btn.configure(text=btn.cget("text").replace("▶", "▼"))

    for category_name, sub_items in alvos_ativos.items():
        cat_container = ctk.CTkFrame(scroll, fg_color="transparent")
        cat_container.pack(fill="x", pady=(5, 5), padx=5)
        
        is_sistema = (category_name.lower() == "sistema")
        seta = "▼" if is_sistema else "▶"
        
        btn_header = ctk.CTkButton(
            cat_container, 
            text=f"{seta}  {category_name.upper()}", 
            font=("Helvetica", 14, "bold"), 
            text_color="#000000",
            fg_color="#F0F0F0",
            hover_color="#E0E0E0",
            anchor="w",
            corner_radius=0,
            border_width=1,
            border_color="#000000"
        )
        btn_header.pack(fill="x")
        
        items_frame = ctk.CTkFrame(cat_container, fg_color="transparent")
        
        btn_header.configure(command=lambda b=btn_header, f=items_frame: toggle_accordion(b, f))
        
        if is_sistema:
            items_frame.pack(fill="x", padx=10, pady=(0, 10))
            
        for item_name, target_dict in sub_items.items():
            chk = ctk.CTkCheckBox(
                items_frame, 
                text=item_name, 
                font=("Consolas", 12),
                corner_radius=0, 
                fg_color="#D50000", 
                border_color="#000000", 
                checkmark_color="#FFFFFF", 
                hover_color="#B71C1C",
                text_color="#000000"
            )
            chk.pack(anchor="w", pady=4, padx=5)
            
            # Regra de Segurança Dinâmica
            nome_lower = item_name.lower()
            if any(palavra in nome_lower for palavra in ["senha", "login", "cookie", "sessão", "sessao", "formulário", "formulario", "download"]):
                chk.deselect()
            else:
                chk.select()
                
            checkbox_vars[(category_name, item_name)] = (chk, target_dict)

    # Bottom Action Bar
    action_bar = ctk.CTkFrame(view, fg_color="#FFFFFF", border_width=1, border_color="#000000", corner_radius=0, height=60)
    action_bar.pack(fill="x", side="bottom")
    action_bar.pack_propagate(False)
    
    lbl_space = ctk.CTkLabel(action_bar, text="ESPAÇO RECUPERÁVEL: 0.00 MB", font=("Consolas", 14, "bold"), text_color="#000000")
    lbl_space.pack(side="left", padx=20)
    
    progress = ctk.CTkProgressBar(action_bar, width=150, height=10, corner_radius=0, fg_color="#E0E0E0", progress_color="#D50000")
    progress.pack(side="left", padx=20)
    progress.set(0)
    progress.pack_forget() # Oculto por padrão

    btn_frame = ctk.CTkFrame(action_bar, fg_color="transparent")
    btn_frame.pack(side="right", padx=10)

    def get_selected_targets():
        targets = []
        for key, (chk, target_dict) in checkbox_vars.items():
            if chk.get() == 1:
                targets.append(target_dict)
        return targets

    def run_analysis():
        btn_analyze.configure(state="disabled")
        btn_clean.configure(state="disabled")
        progress.pack(side="left", padx=20)
        progress.configure(mode="indeterminate")
        progress.start()
        
        def _task():
            targets = get_selected_targets()
            total_bytes = calcular_lixo(targets)
            mb = total_bytes / (1024 * 1024)
            view.after(0, lambda: lbl_space.configure(text=f"ESPAÇO RECUPERÁVEL: {mb:.2f} MB"))
            view.after(0, progress.stop)
            view.after(0, progress.pack_forget)
            view.after(0, lambda: btn_analyze.configure(state="normal"))
            view.after(0, lambda: btn_clean.configure(state="normal"))
            
        threading.Thread(target=_task, daemon=True).start()

    def run_clean():
        btn_analyze.configure(state="disabled")
        btn_clean.configure(state="disabled")
        
        abertos = verificar_navegadores_abertos()
        if abertos:
            import tkinter.messagebox as messagebox
            import time
            lista_str = ", ".join(abertos)
            msg = f"Os seguintes navegadores estão abertos: {lista_str}. Eles contêm arquivos bloqueados pelo sistema.\n\nDeseja fechá-los agora para realizar uma limpeza profunda? (Caso escolha Não, a limpeza ignorará os arquivos em uso)."
            
            res = messagebox.askyesno("Processos em Execução", msg, icon="warning")
            if res:
                encerrar_navegadores(abertos)
                time.sleep(1) # Aguarda o Kernel liberar as travas
                
        progress.pack(side="left", padx=20)
        progress.configure(mode="indeterminate")
        progress.start()
        
        def _task():
            targets = get_selected_targets()
            executar_limpeza(targets)
            view.after(0, lambda: lbl_space.configure(text="ESPAÇO RECUPERÁVEL: 0.00 MB"))
            view.after(0, progress.stop)
            view.after(0, progress.pack_forget)
            view.after(0, lambda: btn_analyze.configure(state="normal"))
            view.after(0, lambda: btn_clean.configure(state="normal"))
            
        threading.Thread(target=_task, daemon=True).start()

    btn_analyze = ctk.CTkButton(btn_frame, text="[ ANALISAR ]", font=("Helvetica", 12, "bold"), fg_color="#000000", hover_color="#333333", corner_radius=0, command=run_analysis)
    btn_analyze.pack(side="left", padx=(0, 5))
    
    btn_clean = ctk.CTkButton(btn_frame, text="[ LIMPAR E CORRIGIR ]", font=("Helvetica", 12, "bold"), fg_color="#D50000", hover_color="#B71C1C", corner_radius=0, command=run_clean)
    btn_clean.pack(side="left")
