import customtkinter as ctk

class SplashScreen(ctk.CTkToplevel):
    def __init__(self, master, on_ready_callback):
        super().__init__(master)
        self._on_ready = on_ready_callback
        self._anim_step = 0
        
        # Estrutura: Janela sem bordas
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        # Tamanho e posição
        w, h = 500, 300
        from gui.utils import center_window
        center_window(self, w, h)
        
        self.configure(fg_color="#FFFFFF")
        
        # Frame preto de 1px ao redor de tudo para dar contraste
        self.border_frame = ctk.CTkFrame(self, fg_color="#FFFFFF", border_width=2, border_color="#000000", corner_radius=0)
        self.border_frame.pack(fill="both", expand=True)
        
        import os
        import sys
        
        # Resolve path do background splash
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        splash_path = os.path.join(base_dir, "gui", "Media", "splash.png")
        
        self.lbl_bg = ctk.CTkLabel(self.border_frame, text="")
        self.lbl_bg.place(x=0, y=0, relwidth=1, relheight=1)
        
        try:
            from PIL import Image
            if os.path.exists(splash_path):
                img = Image.open(splash_path).convert("RGBA")
                
                # Redimensionar para cobrir a janela exatamente (500x300)
                img_resized = img.resize((w, h), Image.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img_resized, dark_image=img_resized, size=(w, h))
                self.lbl_bg.configure(image=ctk_img)
            else:
                self.lbl_bg.configure(text="SYSFORGE // SINGULARITY DOT", font=("Arial", 28, "bold"), text_color="#000000")
        except Exception:
            self.lbl_bg.configure(text="SYSFORGE // SINGULARITY DOT", font=("Arial", 28, "bold"), text_color="#000000")

        
        # Barra de Progresso: No centro-inferior
        self.prog_bar = ctk.CTkProgressBar(self.border_frame, width=300, height=8, 
                                           corner_radius=0, border_width=1, border_color="#000000", 
                                           fg_color="#E0E0E0", progress_color="#D50000")
        self.prog_bar.place(relx=0.5, rely=0.65, anchor="center")
        self.prog_bar.set(0)
        self.prog_bar.lift()
        
        # Texto de Status
        self.lbl_status = ctk.CTkLabel(self.border_frame, text="Inicializando...", font=("Consolas", 10), text_color="#000000", bg_color="transparent")
        self.lbl_status.place(relx=0.5, rely=0.75, anchor="center")
        self.lbl_status.lift()
        
        # Version Badge
        from gear.updater import CURRENT_VERSION
        from gear.build_config import EDICAO_ATUAL
        self.lbl_version = ctk.CTkLabel(self.border_frame, text=f"v{CURRENT_VERSION} [{EDICAO_ATUAL}]", font=("Consolas", 9, "bold"), text_color="#808080", bg_color="transparent")
        self.lbl_version.place(relx=0.98, rely=0.98, anchor="se")
        self.lbl_version.lift()
        
        self.messages = [
            "Carregando módulos do sistema...",
            "Iniciando matriz de intervenção...",
            "Estabelecendo telemetria...",
            "Sincronizando ambiente de implantação..."
        ]
        
        self.update_idletasks()
        self.after(50, self._animate)

    def _animate(self):
        self._anim_step += 1
        
        # 3.5 segundos a 50ms = 70 steps
        progress = self._anim_step / 70.0
        
        if progress >= 1.0:
            self.prog_bar.set(1.0)
            self.lbl_status.configure(text="Concluído.")
            self.after(200, self._finish)
            return
            
        self.prog_bar.set(progress)
        
        # Atualiza a mensagem baseado no progresso
        idx = int(progress * len(self.messages))
        if idx >= len(self.messages):
            idx = len(self.messages) - 1
            
        self.lbl_status.configure(text=self.messages[idx])
        
        self.after(50, self._animate)

    def _finish(self):
        self.destroy()
        if self._on_ready:
            self._on_ready()
