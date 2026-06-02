import customtkinter as ctk
import threading
import time
from gear.uwp_manager import listar_uwp, remover_uwp, reparar_reinstalar_uwp
from worker.thread_manager import GenericWorker

class UWPView(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#FFFFFF", corner_radius=0)
        
        # Cabeçalho
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 10), padx=20)
        ctk.CTkLabel(header, text="GERENCIAMENTO UWP", font=("Helvetica", 24, "bold"), text_color="#000000").pack(anchor="w")
        ctk.CTkLabel(header, text="MICROSOFT STORE APPS - CONTROLE CIRÚRGICO", font=("Consolas", 12), text_color="#000000").pack(anchor="w", pady=(2, 0))

        # Layout Principal (Split List / Terminal)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=3) # Lista
        self.grid_columnconfigure(1, weight=2) # Terminal

        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=2)
        main_frame.grid_rowconfigure(0, weight=1)

        # Lado Esquerdo (Lista de Pacotes e Botões)
        left_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # ScrollableFrame para a lista (Regra 1: bg branco, borda preta fina, corner 0)
        self.scroll = ctk.CTkScrollableFrame(left_panel, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#000000")
        self.scroll.pack(fill="both", expand=True)

        # Contêiner de Botões (Regra 1: Botões agressivos)
        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        btn_frame.grid_columnconfigure((0, 1), weight=1, uniform="btns")
        
        # Botão DESTRUIR SELECIONADOS (Regra 1: Vermelho com borda preta)
        self.btn_destroy = ctk.CTkButton(
            btn_frame, text="DESTRUIR SELECIONADOS", height=42,
            font=("Helvetica", 14, "bold"), fg_color="#D50000", hover_color="#B71C1C", text_color="#FFFFFF",
            corner_radius=0, border_width=1, border_color="#000000", command=self._on_destroy
        )
        self.btn_destroy.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Botão REPARAR / REINSTALAR SELECIONADOS (Regra 1: Fundo preto)
        self.btn_repair = ctk.CTkButton(
            btn_frame, text="REPARAR / REINSTALAR", height=42,
            font=("Helvetica", 14, "bold"), fg_color="#000000", hover_color="#333333", text_color="#FFFFFF",
            corner_radius=0, border_width=1, border_color="#000000", command=self._on_repair
        )
        self.btn_repair.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # Lado Direito (Terminal de Log)
        right_panel = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew")

        ctk.CTkLabel(right_panel, text="LOG DE OPERAÇÕES", font=("Consolas", 12, "bold"), text_color="#000000").pack(anchor="w", pady=(0, 5))
        
        self.terminal = ctk.CTkTextbox(
            right_panel, fg_color="#FFFFFF", text_color="#000000", font=("Consolas", 11),
            corner_radius=0, border_width=1, border_color="#000000"
        )
        self.terminal.pack(fill="both", expand=True)
        self.terminal.configure(state="disabled")

        self.uwp_vars = {}
        self.uwp_data = []

        self._log_msg("Aguardando carregamento de pacotes UWP...")
        threading.Thread(target=self._load_data, daemon=True).start()

    def _log_msg(self, msg):
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"> {msg}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def _load_data(self):
        self.uwp_data = listar_uwp()
        self.after(0, self._render_list)
        self.after(0, lambda: self._log_msg(f"Total de pacotes carregados: {len(self.uwp_data)}"))

    def _render_list(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        
        self.uwp_vars.clear()
        
        if not self.uwp_data:
            ctk.CTkLabel(self.scroll, text="Nenhum pacote UWP encontrado.", font=("Consolas", 12), text_color="#000000").pack(pady=20)
            return

        for app in self.uwp_data:
            app_name = app.get("Name", "Desconhecido")
            pkg_name = app.get("PackageFullName", "Desconhecido")
            
            var = ctk.BooleanVar(value=False)
            cb = ctk.CTkCheckBox(
                self.scroll, text=app_name, variable=var,
                font=("Consolas", 12), text_color="#000000",
                corner_radius=0, border_color="#000000", border_width=1,
                fg_color="#D50000", hover_color="#B71C1C", checkmark_color="#FFFFFF"
            )
            cb.pack(anchor="w", padx=10, pady=4)
            self.uwp_vars[pkg_name] = var

    def _get_selected(self):
        return [pkg for pkg, var in self.uwp_vars.items() if var.get()]
        
    def _lock_ui(self):
        self.btn_destroy.configure(state="disabled")
        self.btn_repair.configure(state="disabled")
        for cb in self.scroll.winfo_children():
            if isinstance(cb, ctk.CTkCheckBox):
                cb.configure(state="disabled")
                
    def _unlock_ui(self):
        self.btn_destroy.configure(state="normal")
        self.btn_repair.configure(state="normal")
        for cb in self.scroll.winfo_children():
            if isinstance(cb, ctk.CTkCheckBox):
                cb.configure(state="normal")

    def _on_destroy(self):
        selected = self._get_selected()
        if not selected:
            self._log_msg("Nenhum pacote selecionado.")
            return

        self._lock_ui()
        self._log_msg(f"Iniciando destruição de {len(selected)} pacotes...")

        def _generator():
            yield f"Operação em Lote ({len(selected)} itens)..."
            for pkg in selected:
                yield f"DESTRUINDO: {pkg}..."
                success = remover_uwp(pkg)
                if success:
                    yield f"[OK] {pkg} aniquilado."
                else:
                    yield f"[ERRO] Falha ao destruir {pkg}."
                time.sleep(0.1)
            yield "Operação de destruição finalizada."

        # REGRA 2 (Execução Silenciosa e Threading)
        GenericWorker(
            {"type": "custom_generator", "generator_func": _generator},
            lambda m: self.after(0, lambda: self._log_msg(m)),
            lambda: self.after(0, self._on_operation_done)
        ).start()

    def _on_repair(self):
        selected = self._get_selected()
        if not selected:
            self._log_msg("Nenhum pacote selecionado.")
            return

        self._lock_ui()
        self._log_msg(f"Iniciando reparo de {len(selected)} pacotes...")

        def _generator():
            yield f"Reinstalação em Lote ({len(selected)} itens)..."
            for pkg in selected:
                app_name_base = pkg.split('_')[0] 
                
                yield f"REPARANDO: {app_name_base}..."
                success = reparar_reinstalar_uwp(app_name_base)
                if success:
                    yield f"[OK] {app_name_base} restaurado."
                else:
                    yield f"[ERRO] Falha ao reparar {app_name_base}."
                time.sleep(0.1)
            yield "Operação de reparo finalizada."

        # REGRA 2 (Execução Silenciosa e Threading)
        GenericWorker(
            {"type": "custom_generator", "generator_func": _generator},
            lambda m: self.after(0, lambda: self._log_msg(m)),
            lambda: self.after(0, self._on_operation_done)
        ).start()
        
    def _on_operation_done(self):
        self._unlock_ui()
        self._log_msg("Atualizando lista de pacotes...")
        threading.Thread(target=self._load_data, daemon=True).start()
