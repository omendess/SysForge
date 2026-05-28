import customtkinter as ctk
from tkinter import ttk
import threading
import os
import psutil
from gear.hardware_reader import get_all_hardware
from gear.system_cleaner import get_temp_size_gb, get_windows_old_size_gb
from gear.software_installer import SOFTWARE_DICT, PROFILES
from gear.app_manager import get_installed_apps, open_location
from gear.network_config import get_current_hostname
from gear.power_config import get_current_plan
from gear.wallpaper import find_wallpapers_on_pendrive
from gear.startup_manager import get_startup_items, get_scheduled_tasks, disable_startup_item, disable_scheduled_task
from gear.windows_tweaks import get_current_tweak_states
from gear.office_checker import get_office_info
from gear.system_info import get_full_system_report
from gear.system_repair import force_restore_point, repair_sfc_dism, repair_disk_chkdsk, reset_network, reset_windows_update, scan_network_devices
from worker.thread_manager import GenericWorker, LOG

# --- Design Tokens ---
BG_MAIN    = "#0F172A"
BG_SIDEBAR = "#1E293B"
BG_CARD    = "#1E293B"
BORDER     = "#334155"
ACCENT     = "#3B82F6"
ACCENT_HVR = "#2563EB"
GREEN      = "#22C55E"
AMBER      = "#F59E0B"
RED        = "#EF4444"
PURPLE     = "#A855F7"
CYAN       = "#06B6D4"
TXT_DIM    = "#94A3B8"
TXT_MUTED  = "#64748B"
CR = 12

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        from gear.updater import CURRENT_VERSION
        self.title(f"SysForge {CURRENT_VERSION} — Motor de Implantação")
        self.minsize(1000, 700)
        
        # Centralizar na tela
        w, h = 1200, 820
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
        
        try:
            import sys
            import os
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "icon.ico")
            # Caso _MEIPASS não resolva, tenta na raiz do projeto (cwd)
            if not os.path.exists(icon_path):
                icon_path = "icon.ico"
            self.iconbitmap(icon_path)
        except Exception:
            pass
            
        self.configure(fg_color=BG_MAIN)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self._build_sidebar()
        self._build_views()
        self.select_view("dashboard")

    # ─── Sidebar ────────────────────────────────────────────
    def _build_sidebar(self):
        sb = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=BG_SIDEBAR, border_width=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_rowconfigure(11, weight=1)
        self.sidebar = sb

        # Logo
        ctk.CTkLabel(sb, text="⚒️ SysForge", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, padx=24, pady=(28, 4), sticky="w")
        ctk.CTkLabel(sb, text="Motor de Implantação", font=ctk.CTkFont(size=11), text_color=TXT_MUTED).grid(row=1, column=0, padx=26, pady=(0, 12), sticky="w")

        # Separator
        sep = ctk.CTkFrame(sb, height=1, fg_color=BORDER)
        sep.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.nav_btns = {}
        items = [("📊  Dashboard","dashboard",3),("📦  Softwares","softwares",4),("⚙️  Tweaks","tweaks",5),("🗑️  App Manager","app_manager",6),("🚀  Startup","startup",7),("🛠️  Reparo & Scanner","repair",8),("📋  Logs","logs",9),("ℹ️  Info", "info", 10)]
        for text, key, row in items:
            b = ctk.CTkButton(sb, text=text, anchor="w", corner_radius=10, height=42, fg_color="transparent", text_color=TXT_DIM, hover_color="#334155", font=ctk.CTkFont(size=14, weight="bold"), command=lambda k=key: self.select_view(k))
            b.grid(row=row, column=0, padx=14, pady=5, sticky="ew")
            self.nav_btns[key] = b

        # Footer badge
        from gear.updater import CURRENT_VERSION
        badge = ctk.CTkFrame(sb, fg_color="#0F172A", corner_radius=8)
        badge.grid(row=12, column=0, padx=14, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(badge, text=f"v{CURRENT_VERSION}  ·  Windows 11", font=ctk.CTkFont(size=11), text_color=TXT_MUTED).pack(pady=8)

    # ─── Views Container ────────────────────────────────────
    def _build_views(self):
        self.views = {}
        for key, builder in [("dashboard",self._build_dashboard),("softwares",self._build_softwares),("tweaks",self._build_tweaks),("app_manager",self._build_app_manager),("startup",self._build_startup),("repair",self._build_repair),("logs",self._build_logs),("info",self._build_info)]:
            f = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_MAIN)
            self.views[key] = f
            builder(f)

    def select_view(self, name):
        for f in self.views.values():
            f.grid_forget()
        self.views[name].grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        for k, b in self.nav_btns.items():
            if k == name:
                b.configure(fg_color=ACCENT, text_color="white", hover_color=ACCENT_HVR)
            else:
                b.configure(fg_color="transparent", text_color=TXT_DIM, hover_color="#334155")
        if name == "dashboard":
            threading.Thread(target=self._load_hw, daemon=True).start()
        elif name == "app_manager":
            if not self.app_data:
                threading.Thread(target=self._load_apps, daemon=True).start()
        elif name == "startup":
            threading.Thread(target=self._load_startup, daemon=True).start()
        elif name == "logs":
            self._refresh_logs()

    # ─── Helpers ────────────────────────────────────────────
    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=CR, border_width=1, border_color=BORDER, **kw)

    def _section_title(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title, font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=4)
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle, font=ctk.CTkFont(size=13), text_color=TXT_MUTED).pack(anchor="w", padx=4, pady=(2, 0))

    # ═══════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════
    def _build_dashboard(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        self._section_title(header, "Dashboard", "Informações do sistema e ações rápidas")

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # HW Grid 2x2
        g = ctk.CTkFrame(scroll, fg_color="transparent")
        g.pack(fill="x", pady=(0, 14))
        g.grid_columnconfigure((0,1), weight=1, uniform="hw")

        hw_meta = [
            ("💻", "Processador", ACCENT,  0, 0),
            ("🧠", "Memória RAM", GREEN,   0, 1),
            ("🎮", "Placa de Vídeo", PURPLE, 1, 0),
            ("🔌", "Placa Mãe", CYAN, 1, 1),
        ]
        self.hw_labels = {}
        for icon, label, color, r, c in hw_meta:
            card = self._card(g)
            px = (0,7) if c==0 else (7,0)
            py = (0,7) if r==0 else (7,0)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=20, pady=(18,6))
            ctk.CTkLabel(top, text=icon, font=ctk.CTkFont(size=22)).pack(side="left")
            ctk.CTkLabel(top, text=label, font=ctk.CTkFont(size=13, weight="bold"), text_color=color).pack(side="left", padx=8)
            lbl = ctk.CTkLabel(card, text="Carregando...", font=ctk.CTkFont(size=15), text_color=TXT_DIM, justify="left", anchor="w")
            lbl.pack(anchor="w", padx=20, pady=(0, 20), fill="x")
            self.hw_labels[label] = {"lbl": lbl, "card": card}

        # Container de Discos (Dinâmico)
        self.disks_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self.disks_frame.pack(fill="x", pady=(0, 14))

        # Actions 2-col
        ag = ctk.CTkFrame(scroll, fg_color="transparent")
        ag.pack(fill="x", pady=(6,0))
        ag.grid_columnconfigure((0,1), weight=1, uniform="act")

        # Clean card
        cc = self._card(ag)
        cc.grid(row=0, column=0, padx=(0,7), sticky="nsew")
        ctk.CTkLabel(cc, text="🧹 Limpeza do Sistema", font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=20, pady=(20,14))

        self.chk_temp = ctk.CTkCheckBox(cc, text="Limpar Pastas Temporárias", font=ctk.CTkFont(size=13), corner_radius=6, fg_color=ACCENT, hover_color=ACCENT_HVR)
        self.chk_temp.pack(anchor="w", padx=24, pady=4)
        self.chk_temp.select()
        self.lbl_temp = ctk.CTkLabel(cc, text="      ⏳ Calculando...", font=ctk.CTkFont(size=11), text_color=TXT_MUTED)
        self.lbl_temp.pack(anchor="w", padx=24, pady=(0,10))

        self.chk_winold = ctk.CTkCheckBox(cc, text="Remover Windows.old", font=ctk.CTkFont(size=13), corner_radius=6, fg_color=ACCENT, hover_color=ACCENT_HVR)
        self.chk_winold.pack(anchor="w", padx=24, pady=4)
        self.lbl_winold = ctk.CTkLabel(cc, text="      ⏳ Calculando...", font=ctk.CTkFont(size=11), text_color=TXT_MUTED)
        self.lbl_winold.pack(anchor="w", padx=24, pady=(0,20))

        # Office card
        oc = self._card(ag)
        oc.grid(row=0, column=1, padx=(7,0), sticky="nsew")
        oc_header = ctk.CTkFrame(oc, fg_color="transparent")
        oc_header.pack(fill="x", padx=20, pady=(18, 4))
        ctk.CTkLabel(oc_header, text="🏢 Microsoft Office",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
        self.lbl_office_build = ctk.CTkLabel(oc_header, text="",
                     font=ctk.CTkFont(size=10), text_color=TXT_MUTED)
        self.lbl_office_build.pack(side="right")
        # Container dinâmico para os produtos
        self.office_products_frame = ctk.CTkFrame(oc, fg_color="transparent")
        self.office_products_frame.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(self.office_products_frame, text="⏳ Verificando...",
                     font=ctk.CTkFont(size=11), text_color=TXT_MUTED).pack(anchor="w")
        self.chk_office = ctk.CTkCheckBox(oc, text="Instalar e Ativar",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     corner_radius=6, fg_color=GREEN, hover_color="#16A34A")
        self.chk_office.pack(anchor="w", padx=20, pady=(6, 18))
        # ROW 3: Utilities
        ug = ctk.CTkFrame(scroll, fg_color="transparent")
        ug.pack(fill="x", pady=(6,0))
        ug.grid_columnconfigure((0,1,2,3), weight=1, uniform="util")

        # Hostname card
        hc = self._card(ug); hc.grid(row=0,column=0,padx=(0,5),sticky="nsew")
        ctk.CTkLabel(hc,text="🖥️ Hostname",font=ctk.CTkFont(size=13,weight="bold"),text_color=CYAN).pack(anchor="w",padx=14,pady=(14,6))
        self.hostname_entry = ctk.CTkEntry(hc,placeholder_text="NOME-PC",height=32,corner_radius=8,border_width=1,border_color=BORDER,fg_color=BG_MAIN,font=ctk.CTkFont(size=12))
        self.hostname_entry.pack(fill="x",padx=14,pady=(0,6))
        ctk.CTkButton(hc,text="Renomear",height=30,corner_radius=8,fg_color=CYAN,hover_color="#0891B2",font=ctk.CTkFont(size=11,weight="bold"),command=self._set_hostname).pack(fill="x",padx=14,pady=(0,14))

        # Report card
        rc = self._card(ug); rc.grid(row=0,column=1,padx=5,sticky="nsew")
        ctk.CTkLabel(rc,text="📄 Relatório",font=ctk.CTkFont(size=13,weight="bold"),text_color=GREEN).pack(anchor="w",padx=14,pady=(14,6))
        ctk.CTkLabel(rc,text="Exportar specs\npara a Área de Trabalho",font=ctk.CTkFont(size=11),text_color=TXT_MUTED,justify="left").pack(anchor="w",padx=14,pady=(0,6))
        ctk.CTkButton(rc,text="Gerar TXT",height=30,corner_radius=8,fg_color=GREEN,hover_color="#16A34A",font=ctk.CTkFont(size=11,weight="bold"),command=self._gen_report).pack(fill="x",padx=14,pady=(0,14))

        # WinUpdate card
        wu = self._card(ug); wu.grid(row=0,column=2,padx=5,sticky="nsew")
        ctk.CTkLabel(wu,text="🔄 Windows Update",font=ctk.CTkFont(size=13,weight="bold"),text_color=AMBER).pack(anchor="w",padx=14,pady=(14,6))
        ctk.CTkLabel(wu,text="Forçar checagem\ne instalação",font=ctk.CTkFont(size=11),text_color=TXT_MUTED,justify="left").pack(anchor="w",padx=14,pady=(0,6))
        self.btn_wupd = ctk.CTkButton(wu,text="Atualizar",height=30,corner_radius=8,fg_color=AMBER,hover_color="#D97706",text_color="black",font=ctk.CTkFont(size=11,weight="bold"),command=self._run_wupdate)
        self.btn_wupd.pack(fill="x",padx=14,pady=(0,14))

        # Power card
        pc = self._card(ug); pc.grid(row=0,column=3,padx=(5,0),sticky="nsew")
        ctk.CTkLabel(pc,text="⚡ Energia",font=ctk.CTkFont(size=13,weight="bold"),text_color=PURPLE).pack(anchor="w",padx=14,pady=(14,6))
        self.lbl_power = ctk.CTkLabel(pc,text="Carregando...",font=ctk.CTkFont(size=11),text_color=TXT_MUTED)
        self.lbl_power.pack(anchor="w",padx=14,pady=(0,6))
        ctk.CTkButton(pc,text="Alto Desempenho",height=30,corner_radius=8,fg_color=PURPLE,hover_color="#7C3AED",font=ctk.CTkFont(size=11,weight="bold"),command=self._set_power).pack(fill="x",padx=14,pady=(0,14))

        # Footer — dentro do scroll para não ser cortado
        ft = ctk.CTkFrame(scroll, fg_color="transparent")
        ft.pack(fill="x", pady=(14, 4))
        self.btn_dash = ctk.CTkButton(ft, text="🚀  INICIAR IMPLANTAÇÃO DA BANCADA", height=48, font=ctk.CTkFont(size=15, weight="bold"), fg_color=ACCENT, hover_color=ACCENT_HVR, corner_radius=CR, command=self._run_dash)
        self.btn_dash.pack(fill="x", pady=(0,8))
        self.dash_prog = ctk.CTkProgressBar(ft, height=5, corner_radius=3, progress_color=ACCENT, fg_color="#1a1a2e")
        self.dash_prog.pack(fill="x"); self.dash_prog.set(0); self.dash_prog.pack_forget()
        self.lbl_dash_st = ctk.CTkLabel(ft, text="Pronto para operar.", font=ctk.CTkFont(size=12), text_color=TXT_MUTED)
        self.lbl_dash_st.pack(pady=(0,6))

    def _load_hw(self):
        hw = get_all_hardware()
        hostname = get_current_hostname()
        power = get_current_plan()
        
        self.after(0, lambda: [
            self.hw_labels["Processador"]["lbl"].configure(text=hw["CPU"]),
            self.hw_labels["Memória RAM"]["lbl"].configure(text=hw["RAM"]),
            self.hw_labels["Placa de Vídeo"]["lbl"].configure(text=hw["GPU"]),
            self.hw_labels["Placa Mãe"]["lbl"].configure(text=hw["Placa Mãe"]),
            self.hostname_entry.delete(0,"end"),
            self.hostname_entry.insert(0,hostname),
            self.lbl_power.configure(text=f"Atual: {power}"),
            self._render_disks(hw.get("Disks", []))
        ])
        
        tg = get_temp_size_gb()
        self.after(0, lambda: self.lbl_temp.configure(text=f"      {tg:.2f} GB de lixo"))
        wg = get_windows_old_size_gb()
        if wg > 0:
            self.after(0, lambda: self.lbl_winold.configure(text=f"      {wg:.2f} GB"))
        else:
            self.after(0, lambda: [self.lbl_winold.configure(text="      Não encontrado"), self.chk_winold.configure(state="disabled")])

        # Office detection
        threading.Thread(target=self._load_office_info, daemon=True).start()

    def _load_office_info(self):
        info = get_office_info()
        def _upd():
            # Limpa container
            for w in self.office_products_frame.winfo_children():
                w.destroy()

            if not info["installed"]:
                ctk.CTkLabel(self.office_products_frame,
                             text="Não instalado",
                             font=ctk.CTkFont(size=11), text_color=TXT_MUTED).pack(anchor="w")
                return

            # Build / versão
            self.lbl_office_build.configure(text=f"Build: {info['version']}")

            # Linha por produto
            for product in info["products"]:
                row = ctk.CTkFrame(self.office_products_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                act = product.get("activated")
                if act is True:
                    badge, badge_color = "✅", GREEN
                elif act is False:
                    badge, badge_color = "❌", RED
                else:
                    badge, badge_color = "⚠️", AMBER

                ctk.CTkLabel(row, text=badge, font=ctk.CTkFont(size=11),
                             width=20).pack(side="left")
                ctk.CTkLabel(row, text=product.get("name", "Produto desconhecido"),
                             font=ctk.CTkFont(size=11), text_color="white",
                             anchor="w").pack(side="left", padx=4)

            # Ajusta botão de instalar
            if info["activated"] is True:
                self.chk_office.configure(text="Reinstalar / Reativar",
                                          fg_color=TXT_MUTED, hover_color="#475569")
            else:
                self.chk_office.configure(text="Instalar e Ativar",
                                          fg_color=GREEN, hover_color="#16A34A")

        self.after(0, _upd)

    def _render_disks(self, disks):
        for w in self.disks_frame.winfo_children(): w.destroy()
        
        # Grid para os discos
        cols = 2
        self.disks_frame.grid_columnconfigure(tuple(range(cols)), weight=1, uniform="disk")
        
        for i, disk in enumerate(disks):
            r = i // cols
            c = i % cols
            px = (0,7) if c==0 else (7,0)
            py = (0,7) if r==0 else (7,0)
            
            card = self._card(self.disks_frame)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            
            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=20, pady=(18,6))
            ctk.CTkLabel(top, text="💾", font=ctk.CTkFont(size=22)).pack(side="left")
            ctk.CTkLabel(top, text=f"Unidade ({disk['device']})", font=ctk.CTkFont(size=13, weight="bold"), text_color=AMBER).pack(side="left", padx=8)
            
            pct = disk["percent"] / 100.0
            disk_color = GREEN if pct < 0.7 else (AMBER if pct < 0.9 else RED)
            
            info_str = f"Total: {disk['total']:.2f} GB | Livre: {disk['free']:.2f} GB"
            ctk.CTkLabel(card, text=info_str, font=ctk.CTkFont(size=13), text_color=TXT_DIM, justify="left", anchor="w").pack(anchor="w", padx=20, pady=(0, 10), fill="x")
            
            prog = ctk.CTkProgressBar(card, height=6, corner_radius=3, progress_color=disk_color, fg_color="#1a1a2e")
            prog.pack(fill="x", padx=20, pady=(0,18))
            prog.set(pct)

    def _run_dash(self):
        t = {"type":"dashboard","clean_temp":self.chk_temp.get(),"clean_win_old":self.chk_winold.get(),"install_office":self.chk_office.get()}
        self.btn_dash.configure(state="disabled"); self.dash_prog.pack(fill="x"); self.dash_prog.start()
        GenericWorker(t, lambda m: self.after(0, lambda: self.lbl_dash_st.configure(text=m)), lambda: self.after(0, self._done_dash)).start()

    def _done_dash(self):
        self.dash_prog.stop(); self.dash_prog.pack_forget(); self.btn_dash.configure(state="normal")
        self.lbl_dash_st.configure(text="✅ Processo finalizado com sucesso!")

    def _set_hostname(self):
        name = self.hostname_entry.get().strip()
        if name:
            GenericWorker({"type":"hostname","name":name}, lambda m: self.after(0,lambda: self.lbl_dash_st.configure(text=m)), None).start()

    def _gen_report(self):
        GenericWorker({"type":"report"}, lambda m: self.after(0,lambda: self.lbl_dash_st.configure(text=m)), None).start()

    def _run_wupdate(self):
        self.btn_wupd.configure(state="disabled")
        GenericWorker({"type":"winupdate"}, lambda m: self.after(0,lambda: self.lbl_dash_st.configure(text=m)), lambda: self.after(0,lambda: self.btn_wupd.configure(state="normal"))).start()

    def _set_power(self):
        GenericWorker({"type":"power"}, lambda m: self.after(0,lambda: self.lbl_dash_st.configure(text=m)), lambda: self.after(0,lambda: self.lbl_power.configure(text="Atual: Alto Desempenho"))).start()

    # ═══════════════════════════════════════════════════════
    #  SOFTWARES
    # ═══════════════════════════════════════════════════════
    def _build_softwares(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        self._section_title(header, "Softwares", "Instalação em massa via Winget")

        # Perfis de implantação
        prof_frame = ctk.CTkFrame(view, fg_color="transparent")
        prof_frame.pack(fill="x", pady=(0,10))
        ctk.CTkLabel(prof_frame,text="Perfis:",font=ctk.CTkFont(size=13,weight="bold"),text_color=TXT_MUTED).pack(side="left",padx=(0,10))
        for pname, plist in PROFILES.items():
            ctk.CTkButton(prof_frame,text=pname,height=32,corner_radius=8,fg_color=BG_CARD,border_width=1,border_color=BORDER,hover_color="#334155",font=ctk.CTkFont(size=12,weight="bold"),command=lambda pl=plist: self._apply_profile(pl)).pack(side="left",padx=4)
        self.lbl_soft_count = ctk.CTkLabel(prof_frame,text="0 selecionados",font=ctk.CTkFont(size=12),text_color=TXT_MUTED)
        self.lbl_soft_count.pack(side="right",padx=10)

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        sg = ctk.CTkFrame(scroll, fg_color="transparent")
        sg.pack(fill="x")
        sg.grid_columnconfigure((0,1), weight=1, uniform="s")

        self.software_vars = {}
        self.software_checkboxes = {}
        ri, ci = 0, 0
        cat_icons = {"Navegadores": "🌐", "Comunicação": "💬", "Utilitários": "🔧", "Desenvolvimento": "🛠️", "Bancos de Dados": "🗄️", "Design / Mídia": "🎨"}

        for cat, softs in SOFTWARE_DICT.items():
            card = self._card(sg)
            px = (0,7) if ci==0 else (7,0)
            card.grid(row=ri, column=ci, padx=px, pady=8, sticky="nsew")

            icon = cat_icons.get(cat, "📦")
            ctk.CTkLabel(card, text=f"{icon}  {cat}", font=ctk.CTkFont(size=15, weight="bold"), text_color=ACCENT).pack(anchor="w", padx=20, pady=(18,10))

            # Select all per category
            all_var = ctk.BooleanVar(value=False)
            cat_vars = []
            def make_toggle(cv, av):
                def toggle():
                    for v in cv: v.set(av.get())
                    self._update_soft_count()
                return toggle

            for name, wid in softs.items():
                v = ctk.BooleanVar(value=False)
                cb = ctk.CTkCheckBox(card, text=name, variable=v, font=ctk.CTkFont(size=13), corner_radius=6, fg_color=ACCENT, hover_color=ACCENT_HVR, command=self._update_soft_count)
                cb.pack(anchor="w", padx=24, pady=5)
                self.software_vars[wid] = v
                self.software_checkboxes[wid] = cb
                cat_vars.append(v)

            ctk.CTkFrame(card, height=1, fg_color=BORDER).pack(fill="x", padx=16, pady=(10,6))
            ctk.CTkCheckBox(card, text="Selecionar todos", variable=all_var, font=ctk.CTkFont(size=12), text_color=TXT_MUTED, corner_radius=6, fg_color=TXT_MUTED, hover_color="#475569", command=make_toggle(cat_vars, all_var)).pack(anchor="w", padx=24, pady=(2,14))

            ci += 1
            if ci > 1: ci = 0; ri += 1

        ft = ctk.CTkFrame(view, fg_color="transparent")
        ft.pack(fill="x", side="bottom", pady=(12,0))
        self.btn_soft = ctk.CTkButton(ft, text="📦  INSTALAR SELECIONADOS", height=48, font=ctk.CTkFont(size=15, weight="bold"), fg_color=ACCENT, hover_color=ACCENT_HVR, corner_radius=CR, command=self._run_soft)
        self.btn_soft.pack(fill="x")
        self.lbl_soft_st = ctk.CTkLabel(ft, text="", text_color=TXT_MUTED)
        self.lbl_soft_st.pack(pady=4)

        # Inicia checagem de programas instalados em background
        threading.Thread(target=self._check_installed_softwares, daemon=True).start()

    def _check_installed_softwares(self):
        apps = get_installed_apps()
        installed_names = [app["name"].lower() for app in apps]
        
        for cat, softs in SOFTWARE_DICT.items():
            for name, wid in softs.items():
                # Tenta casar o nome amigável com o nome do registro
                is_installed = any(name.lower() in inst_name for inst_name in installed_names)
                
                if is_installed and wid in self.software_checkboxes:
                    def update_cb(w=wid, n=name):
                        self.software_checkboxes[w].configure(text=f"{n}  ✅", text_color="#16A34A")
                    self.after(0, update_cb)

    def _run_soft(self):
        sel = [w for w, v in self.software_vars.items() if v.get()]
        if not sel: self.lbl_soft_st.configure(text="Nenhum software selecionado."); return
        self.btn_soft.configure(state="disabled")
        GenericWorker({"type":"software","list":sel}, lambda m: self.after(0, lambda: self.lbl_soft_st.configure(text=m)), lambda: self.after(0, lambda: self.btn_soft.configure(state="normal"))).start()

    # ═══════════════════════════════════════════════════════
    #  TWEAKS (com Switches)
    # ═══════════════════════════════════════════════════════
    def _build_tweaks(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        self._section_title(header, "Windows Tweaks", "Otimizações de privacidade e visual")

        card = self._card(view)
        card.pack(fill="x")

        self.tweak_vars = {}
        self.tweak_switches = {}
        tweaks = [
            ("disable_telemetry",       "🛡️  Desativar Telemetria",                    "Impede coleta de dados de uso pela Microsoft"),
            ("show_hidden_extensions",  "📂  Exibir Extensões e Itens Ocultos",         "Mostra arquivos ocultos e extensões no Explorer"),
            ("disable_bing_search",     "🔍  Desativar Pesquisa Web no Iniciar",        "Remove resultados do Bing no menu Iniciar"),
            ("enable_dark_mode",        "🌙  Forçar Modo Escuro",                       "Aplica tema escuro em todo o sistema"),
            ("classic_context_menu",    "🖱️  Menu de Contexto Clássico",               "Restaura o menu de botão direito antigo (Win 11)"),
            ("disable_hibernation",     "💤  Desativar Hibernação",                    "Libera gigabytes apagando o hiberfil.sys"),
            ("disable_lock_screen",     "🔓  Pular Tela de Bloqueio",                  "Vai direto para a tela de senha ao ligar"),
            ("disable_sticky_keys",     "⌨️  Desativar Teclas de Aderência",           "Impede o popup ao apertar Shift 5 vezes"),
            ("hide_taskbar_chat",       "💬  Ocultar Chat da Barra",                   "Remove o ícone inútil do Teams/Meet Now"),
        ]

        for i, (key, title, desc) in enumerate(tweaks):
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=(16 if i==0 else 8, 8 if i < len(tweaks)-1 else 20))

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True)
            ctk.CTkLabel(left, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(left, text=desc, font=ctk.CTkFont(size=11), text_color=TXT_MUTED, anchor="w").pack(anchor="w")

            var = ctk.BooleanVar(value=False)
            sw = ctk.CTkSwitch(row, text="", variable=var, width=46, fg_color="#334155", progress_color=GREEN, button_color="white", button_hover_color="#E2E8F0")
            sw.pack(side="right", padx=10)
            self.tweak_vars[key] = var
            self.tweak_switches[key] = sw

            if i < len(tweaks) - 1:
                ctk.CTkFrame(card, height=1, fg_color=BORDER).pack(fill="x", padx=20)

        ft = ctk.CTkFrame(view, fg_color="transparent")
        ft.pack(fill="x", side="bottom", pady=(12,0))
        self.btn_twk = ctk.CTkButton(ft, text="⚙️  APLICAR TWEAKS", height=48, font=ctk.CTkFont(size=15, weight="bold"), fg_color=ACCENT, hover_color=ACCENT_HVR, corner_radius=CR, command=self._run_twk)
        self.btn_twk.pack(fill="x")
        self.lbl_twk_st = ctk.CTkLabel(ft, text="", text_color=TXT_MUTED)
        self.lbl_twk_st.pack(pady=4)

        # Inicia leitura após tudo renderizado
        threading.Thread(target=self._load_tweak_states, daemon=True).start()

    def _load_tweak_states(self):
        states = get_current_tweak_states()
        for key, val in states.items():
            if key in self.tweak_vars:
                def update_sw(k=key, v=val):
                    self.tweak_vars[k].set(v)
                    if v:
                        self.tweak_switches[k].select()
                    else:
                        self.tweak_switches[k].deselect()
                self.after(0, update_sw)

    def _run_twk(self):
        t = {k: v.get() for k,v in self.tweak_vars.items()}
        self.btn_twk.configure(state="disabled")
        GenericWorker({"type":"tweaks","tweaks_dict":t}, lambda m: self.after(0, lambda: self.lbl_twk_st.configure(text=m)), lambda: self.after(0, lambda: self.btn_twk.configure(state="normal"))).start()

    # ═══════════════════════════════════════════════════════
    #  APP MANAGER (Otimizado com Treeview Nativo)
    # ═══════════════════════════════════════════════════════
    def _build_app_manager(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        self._section_title(header, "App Manager", "Desinstale bloatwares e programas indesejados")

        # Barra de pesquisa
        search_frame = ctk.CTkFrame(view, fg_color="transparent")
        search_frame.pack(fill="x", pady=(0, 10))

        self._search_debounce_id = None
        self.app_search_var = ctk.StringVar()
        self.app_search_var.trace_add("write", lambda *_: self._debounce_filter())

        self.app_search_entry = ctk.CTkEntry(
            search_frame, placeholder_text="🔍  Buscar programa...",
            textvariable=self.app_search_var,
            height=40, corner_radius=CR, border_width=1,
            border_color=BORDER, fg_color=BG_CARD,
            font=ctk.CTkFont(size=14)
        )
        self.app_search_entry.pack(side="left", fill="x", expand=True, padx=(0,6))

        # Botões
        ctk.CTkButton(search_frame, text="✕", width=40, height=40, corner_radius=CR, fg_color=BG_CARD, border_width=1, border_color=BORDER, hover_color="#334155", font=ctk.CTkFont(size=16, weight="bold"), text_color=TXT_MUTED, command=lambda: self.app_search_var.set("")).pack(side="left", padx=(0,6))
        ctk.CTkButton(search_frame, text="⚠️ Bloatwares", width=120, height=40, corner_radius=CR, fg_color="#7F1D1D", border_width=1, border_color=RED, hover_color=RED, font=ctk.CTkFont(size=12, weight="bold"), command=self._select_bloatware).pack(side="left", padx=(0,6))
        ctk.CTkButton(search_frame, text="🔄", width=40, height=40, corner_radius=CR, fg_color=BG_CARD, border_width=1, border_color=BORDER, hover_color="#334155", font=ctk.CTkFont(size=16), command=self._force_reload_apps).pack(side="left", padx=(0,6))

        self.lbl_app_count = ctk.CTkLabel(search_frame, text="", font=ctk.CTkFont(size=12), text_color=TXT_MUTED)
        self.lbl_app_count.pack(side="right", padx=6)

        # Style do Treeview para combinar com o Dark Mode
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview", background=BG_CARD, foreground="white", fieldbackground=BG_CARD, borderwidth=0, font=("Consolas" if os.name == "nt" else "Courier", 11), rowheight=32)
        style.map("Dark.Treeview", background=[("selected", "#334155")])
        style.configure("Dark.Treeview.Heading", background="#162032", foreground="white", borderwidth=0, font=("Arial", 11, "bold"))
        style.map("Dark.Treeview.Heading", background=[("active", "#1E293B")])

        # Container do Treeview
        tree_frame = ctk.CTkFrame(view, corner_radius=CR, border_width=1, border_color=BORDER, fg_color=BG_CARD)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, style="Dark.Treeview", columns=("Sel", "App", "Tamanho"), show="headings")
        self.tree.heading("Sel", text="✔")
        self.tree.heading("App", text="Programa", anchor="w")
        self.tree.heading("Tamanho", text="Tamanho")

        self.tree.column("Sel", width=40, minwidth=40, stretch=False, anchor="center")
        self.tree.column("App", width=600, minwidth=200, stretch=True, anchor="w")
        self.tree.column("Tamanho", width=100, minwidth=80, stretch=False, anchor="e")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y", pady=2)

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        ft = ctk.CTkFrame(view, fg_color="transparent")
        ft.pack(fill="x", side="bottom", pady=(12,0))
        self.btn_app = ctk.CTkButton(ft, text="🗑️  DESINSTALAR SELECIONADOS", height=48, font=ctk.CTkFont(size=15, weight="bold"), fg_color=RED, hover_color="#DC2626", corner_radius=CR, command=self._run_app)
        self.btn_app.pack(fill="x")
        self.lbl_app_st = ctk.CTkLabel(ft, text="", text_color=TXT_MUTED)
        self.lbl_app_st.pack(pady=4)

        # Dados internos
        self.app_data = []      # Lista original de dicts
        self.app_selected = {}  # {nome_do_app: booleano}

    def _load_apps(self):
        self.after(0, lambda: self.tree.delete(*self.tree.get_children()))
        self.after(0, lambda: self.lbl_app_st.configure(text="⏳ Carregando programas instalados..."))
        apps = get_installed_apps()
        self.app_data = apps
        self.app_selected = {app["name"]: False for app in apps}
        self.after(0, lambda: self.lbl_app_st.configure(text=""))
        self.after(0, lambda: self.app_search_var.set(""))
        self.after(0, lambda: self._apply_filter(""))

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell" or region == "tree":
            item = self.tree.focus()
            if not item: return
            vals = self.tree.item(item, "values")
            if not vals: return
            
            app_name = self.tree.item(item, "text")
            current_state = self.app_selected.get(app_name, False)
            new_state = not current_state
            self.app_selected[app_name] = new_state
            
            new_sel_str = "[X]" if new_state else "[ ]"
            self.tree.item(item, values=(new_sel_str, vals[1], vals[2]))

    def _debounce_filter(self):
        if self._search_debounce_id is not None:
            self.after_cancel(self._search_debounce_id)
        self._search_debounce_id = self.after(100, self._filter_apps)

    def _filter_apps(self):
        self._search_debounce_id = None
        query = self.app_search_var.get().strip().lower()
        self._apply_filter(query)

    def _apply_filter(self, query):
        self.tree.delete(*self.tree.get_children())
        
        filtered = [app for app in self.app_data if not query or query in app["name"].lower()]
        
        if query:
            self.lbl_app_count.configure(text=f"{len(filtered)} de {len(self.app_data)} programas")
        else:
            self.lbl_app_count.configure(text=f"{len(self.app_data)} programas")

        for app in filtered:
            is_bl = app["is_bloatware"]
            prefix = "⚠️ " if is_bl else ""
            app_name = app["name"]
            disp_name = f"{prefix}{app_name}"
            
            is_sel = self.app_selected.get(app_name, False)
            sel_str = "[X]" if is_sel else "[ ]"
            
            size_str = f"{app['size_mb']:.0f} MB" if app['size_mb'] > 0 else "-"
            
            tag = "bloat" if is_bl else "normal"
            self.tree.insert("", "end", text=app_name, values=(sel_str, disp_name, size_str), tags=(tag,))
            
        self.tree.tag_configure("bloat", foreground="#EF4444")
        self.tree.tag_configure("normal", foreground="white")

    def _run_app(self):
        sel_names = [name for name, is_sel in self.app_selected.items() if is_sel]
        if not sel_names: 
            self.lbl_app_st.configure(text="Nenhum app selecionado.")
            return
            
        sel_apps = [app for app in self.app_data if app["name"] in sel_names]
        self.btn_app.configure(state="disabled")
        GenericWorker({"type":"uninstall","app_list":sel_apps}, lambda m: self.after(0, lambda: self.lbl_app_st.configure(text=m)), lambda: self.after(0, self._done_app)).start()

    def _done_app(self):
        self.btn_app.configure(state="normal")
        self._force_reload_apps()

    def _force_reload_apps(self):
        self.app_data = []
        threading.Thread(target=self._load_apps, daemon=True).start()

    def _select_bloatware(self):
        """Marca apenas os itens bloatware na lista e atualiza a view."""
        for app in self.app_data:
            self.app_selected[app["name"]] = app["is_bloatware"]
        self._filter_apps()

    def _apply_profile(self, id_list):
        for wid, var in self.software_vars.items():
            var.set(wid in id_list)
        self._update_soft_count()

    def _update_soft_count(self):
        n = sum(1 for v in self.software_vars.values() if v.get())
        self.lbl_soft_count.configure(text=f"{n} selecionados")

    # ═══════════════════════════════════════════════════════
    #  STARTUP MANAGER
    # ═══════════════════════════════════════════════════════
    def _build_startup(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        self._section_title(header, "Gerenciador de Sistema", "Controle de inicialização e ferramentas administrativas")

        # Ferramentas Administrativas
        tools_frame = ctk.CTkFrame(view, fg_color="transparent")
        tools_frame.pack(fill="x", pady=(0, 10))
        tools = [
            ("Gerenciador de Tarefas", "taskmgr"),
            ("Disp. e Impressoras", "devmgmt.msc"),
            ("Gerenciador de Disco", "diskmgmt.msc"),
            ("Painel de Controle", "control"),
            ("Firewall", "wf.msc"),
        ]
        for name, cmd in tools:
            ctk.CTkButton(tools_frame, text=name, height=30, fg_color=BG_CARD,
                          border_width=1, border_color=BORDER, hover_color="#334155",
                          font=ctk.CTkFont(size=11, weight="bold"),
                          command=lambda c=cmd: self._open_as_admin(c)).pack(side="left", padx=(0, 6))

        # Abas
        tab_bar = ctk.CTkFrame(view, fg_color="transparent")
        tab_bar.pack(fill="x", pady=(0, 10))
        self._startup_tab = ctk.StringVar(value="startup")

        def _tab_btn(text, key):
            return ctk.CTkButton(
                tab_bar, text=text, height=34, corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=ACCENT if self._startup_tab.get() == key else BG_CARD,
                text_color="white" if self._startup_tab.get() == key else TXT_DIM,
                hover_color=ACCENT_HVR,
                command=lambda k=key: self._switch_startup_tab(k)
            )

        self._tab_btn_startup = _tab_btn("🚀 Inicialização", "startup")
        self._tab_btn_startup.pack(side="left", padx=(0, 6))
        self._tab_btn_tasks   = _tab_btn("📆 Tarefas Agendadas", "tasks")
        self._tab_btn_tasks.pack(side="left", padx=(0, 6))

        # Busca
        self._startup_search = ctk.StringVar()
        self._startup_search.trace_add("write", lambda *_: self._filter_startup())
        ctk.CTkEntry(tab_bar, textvariable=self._startup_search,
                     placeholder_text="🔍  Buscar...", height=34, corner_radius=8,
                     border_width=1, border_color=BORDER, fg_color=BG_CARD,
                     font=ctk.CTkFont(size=12)).pack(side="right", padx=(6, 0))
        ctk.CTkButton(tab_bar, text="🔄", width=34, height=34, corner_radius=8,
                      fg_color=BG_CARD, border_width=1, border_color=BORDER,
                      hover_color="#334155", font=ctk.CTkFont(size=14),
                      command=lambda: threading.Thread(target=self._load_startup, daemon=True).start()
                      ).pack(side="right", padx=4)

        self.scroll_startup = ctk.CTkScrollableFrame(view, fg_color=BG_CARD,
                                                     corner_radius=CR, border_width=1,
                                                     border_color=BORDER)
        self.scroll_startup.pack(fill="both", expand=True)
        self.startup_data = []
        self.tasks_data   = []

    def _open_as_admin(self, cmd):
        import ctypes
        try:
            ctypes.windll.shell32.ShellExecuteW(None, "runas", cmd, None, None, 1)
        except Exception:
            pass

    def _switch_startup_tab(self, key):
        self._startup_tab.set(key)
        self._tab_btn_startup.configure(
            fg_color=ACCENT if key == "startup" else BG_CARD,
            text_color="white" if key == "startup" else TXT_DIM)
        self._tab_btn_tasks.configure(
            fg_color=ACCENT if key == "tasks" else BG_CARD,
            text_color="white" if key == "tasks" else TXT_DIM)
        self._filter_startup()

    def _load_startup(self):
        self.after(0, self._render_startup_loading)
        st_items = get_startup_items()
        ts_items = get_scheduled_tasks()
        self.startup_data = st_items
        self.tasks_data = ts_items
        self.after(0, self._filter_startup)

    def _render_startup_loading(self):
        for w in self.scroll_startup.winfo_children(): w.destroy()
        ctk.CTkLabel(self.scroll_startup, text="⏳ Carregando sistema...",
                     font=ctk.CTkFont(size=14), text_color=TXT_MUTED).pack(pady=40)

    def _filter_startup(self):
        q = self._startup_search.get().lower().strip()
        is_tasks = self._startup_tab.get() == "tasks"
        src = self.tasks_data if is_tasks else self.startup_data
        filtered = [x for x in src if q in x["name"].lower() or (q in x.get("command", "").lower())]
        self._render_startup(filtered, is_tasks)

    def _render_startup(self, items, is_tasks):
        for w in self.scroll_startup.winfo_children(): w.destroy()
        if not items:
            ctk.CTkLabel(self.scroll_startup, text="Nenhum item encontrado.",
                         font=ctk.CTkFont(size=14), text_color=TXT_MUTED).pack(pady=40)
            return

        for i, item in enumerate(items):
            bg = "#162032" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self.scroll_startup, fg_color=bg, corner_radius=0)
            row.pack(fill="x", padx=8, pady=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            name = item.get("name", "Desconhecido")
            cmd = item.get("command", "")
            cmd_display = cmd[:60] + ('...' if len(cmd) > 60 else '')
            scope = item.get("scope", "Task") if is_tasks else item.get("scope", "AutoRun")

            ctk.CTkLabel(left, text=name, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{scope}  ·  {cmd_display}",
                         font=ctk.CTkFont(size=10), text_color=TXT_MUTED).pack(anchor="w")

            state_label = item.get("state", "").upper()
            if "DISABLE" in state_label or "DESABILITADO" in state_label:
                # Se for tarefa agendada que já está desabilitada
                ctk.CTkLabel(row, text="Desabilitado", font=ctk.CTkFont(size=11), text_color=TXT_MUTED).pack(side="right", padx=20)
            else:
                ctk.CTkButton(row, text="Desativar", width=80, height=28, corner_radius=6,
                              fg_color=RED, hover_color="#DC2626", font=ctk.CTkFont(size=11, weight="bold"),
                              command=lambda it=item, t=is_tasks: self._disable_startup(it, t)).pack(side="right", padx=10, pady=8)

    def _disable_startup(self, item, is_tasks):
        typ = "task_disable" if is_tasks else "startup_disable"
        GenericWorker({"type": typ, "item": item},
                      lambda m: None,
                      lambda: self.after(0, lambda: threading.Thread(target=self._load_startup, daemon=True).start())
                      ).start()

    # ═══════════════════════════════════════════════════════
    #  REPARO MAGICO E SCANNER
    # ═══════════════════════════════════════════════════════
    def _build_repair(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        self._section_title(header, "Reparo & Scanner", "Ferramentas de diagnóstico e correção do Windows")

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        body = ctk.CTkFrame(scroll, fg_color="transparent")
        body.pack(fill="x", padx=10)
        
        col_left = ctk.CTkFrame(body, fg_color="transparent")
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10), anchor="n")
        
        col_right = ctk.CTkFrame(body, fg_color="transparent")
        col_right.pack(side="left", fill="both", expand=True, padx=(10, 0), anchor="n")

        def _action_btn(parent, text, cmd, color=ACCENT, hover=ACCENT_HVR):
            return ctk.CTkButton(parent, text=text, height=36, corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"), fg_color=color, hover_color=hover, command=cmd)

        def _run_task(task_func):
            self.lbl_repair_st.configure(text="⏳ Executando...")
            GenericWorker({"type": "custom", "func": task_func}, 
                          lambda m: self.after(0, lambda: self.lbl_repair_st.configure(text=m)), 
                          None).start()

        # --- Coluna Esquerda: REPAROS ---
        card_rep = self._card(col_left)
        card_rep.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_rep, text="🪄 Reparo Mágico e Sistema", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_rep, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        _action_btn(card_rep, "SFC + DISM (Reparo de Imagem)", lambda: _run_task(repair_sfc_dism)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Chkdsk (Reparo de Disco no próximo Boot)", lambda: _run_task(repair_disk_chkdsk)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Reset de Rede (Winsock, IP, DNS)", lambda: _run_task(reset_network)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Reset do Windows Update", lambda: _run_task(reset_windows_update)).pack(fill="x", padx=20, pady=6)
        
        ctk.CTkLabel(card_rep, text="Atenção: Alguns reparos podem demorar minutos.", font=ctk.CTkFont(size=11), text_color=TXT_MUTED).pack(pady=(4, 20))

        # --- Coluna Direita: BACKUP E REDE ---
        card_bkp = self._card(col_right)
        card_bkp.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_bkp, text="🛡️ Ponto de Restauração", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_bkp, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        _action_btn(card_bkp, "Criar Ponto de Restauração Forçado", lambda: _run_task(force_restore_point), GREEN, "#16A34A").pack(fill="x", padx=20, pady=(6, 20))

        card_lic = self._card(col_right)
        card_lic.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_lic, text="🔑 Licenças e Ativação", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_lic, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        from gear.activators import activate_windows, capture_product_keys
        _action_btn(card_lic, "Ativar Windows (HWID Digital)", lambda: _run_task(activate_windows), ACCENT, ACCENT_HVR).pack(fill="x", padx=20, pady=6)
        _action_btn(card_lic, "Backup de Product Keys", lambda: _run_task(capture_product_keys), AMBER, "#D97706").pack(fill="x", padx=20, pady=(6, 20))

        card_scan = self._card(col_right)
        card_scan.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_scan, text="📡 Scanner de Dispositivos", font=ctk.CTkFont(size=16, weight="bold"), text_color="white").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_scan, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        def _do_scan():
            self.lbl_repair_st.configure(text="⏳ Escaneando rede e bluetooth...")
            self.scan_text.configure(state="normal")
            self.scan_text.delete("1.0", "end")
            self.scan_text.insert("end", "Iniciando scan...\n")
            self.scan_text.configure(state="disabled")
            
            def _bg():
                devs = scan_network_devices()
                self.after(0, lambda: _upd_scan(devs))
            import threading
            threading.Thread(target=_bg, daemon=True).start()
            
        def _upd_scan(devs):
            self.scan_text.configure(state="normal")
            self.scan_text.delete("1.0", "end")
            self.scan_text.insert("end", "\n".join(devs))
            self.scan_text.configure(state="disabled")
            self.lbl_repair_st.configure(text="✅ Scan concluído.")

        _action_btn(card_scan, "Verificar Wi-Fi, Cabo e Bluetooth", _do_scan, PURPLE, "#9333EA").pack(fill="x", padx=20, pady=6)
        
        self.scan_text = ctk.CTkTextbox(card_scan, height=120, fg_color=BG_MAIN, corner_radius=CR, border_width=1, border_color=BORDER, font=ctk.CTkFont(family="Consolas", size=11), text_color=TXT_DIM, state="disabled")
        self.scan_text.pack(fill="x", padx=20, pady=(6, 20))

        self.lbl_repair_st = ctk.CTkLabel(view, text="Aguardando ação...", font=ctk.CTkFont(size=12), text_color=TXT_MUTED)
        self.lbl_repair_st.pack(side="bottom", pady=10)

    # ═══════════════════════════════════════════════════════
    #  LOGS
    # ═══════════════════════════════════════════════════════
    def _build_logs(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))
        self._section_title(header, "Logs de Operações", "Histórico completo de ações realizadas")

        btn_frame = ctk.CTkFrame(view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(btn_frame, text="🔄 Atualizar", height=32, corner_radius=8, fg_color=BG_CARD, border_width=1, border_color=BORDER, hover_color="#334155", font=ctk.CTkFont(size=12, weight="bold"), command=self._refresh_logs).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="📄 Exportar TXT", height=32, corner_radius=8, fg_color=BG_CARD, border_width=1, border_color=BORDER, hover_color="#334155", font=ctk.CTkFont(size=12, weight="bold"), command=self._export_logs).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="🗑️ Limpar", height=32, corner_radius=8, fg_color=BG_CARD, border_width=1, border_color=BORDER, hover_color="#334155", font=ctk.CTkFont(size=12, weight="bold"), command=self._clear_logs).pack(side="left")

        self.log_textbox = ctk.CTkTextbox(view, fg_color=BG_CARD, corner_radius=CR, border_width=1, border_color=BORDER, font=ctk.CTkFont(family="Consolas", size=13), text_color=TXT_DIM, state="disabled")
        self.log_textbox.pack(fill="both", expand=True)

    def _refresh_logs(self):
        entries = LOG.get_all()
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        if not entries:
            self.log_textbox.insert("end", "  Nenhum log registrado ainda.\n  Execute operações para gerar logs.")
        else:
            for e in entries:
                self.log_textbox.insert("end", f"[{e['time']}]  {e['msg']}\n")
        self.log_textbox.configure(state="disabled")
        self.log_textbox.see("end")

    def _export_logs(self):
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        path = LOG.export(os.path.join(desktop, "SysForge_Log.txt"))
        os.startfile(path)

    def _clear_logs(self):
        LOG.clear()
        self._refresh_logs()

    # ═══════════════════════════════════════════════════════
    #  INFO / SOBRE
    # ═══════════════════════════════════════════════════════
    def _build_info(self, view):
        from gear.updater import CURRENT_VERSION, check_for_updates

        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        self._section_title(header, "Sobre o SysForge", "Informações do sistema e diagnóstico")

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # ── Card: Sobre o App ──────────────────────────────────────────────
        about = self._card(scroll)
        about.pack(fill="x", pady=(0, 14))

        about_body = ctk.CTkFrame(about, fg_color="transparent")
        about_body.pack(fill="x", padx=24, pady=20)

        # Coluna esquerda — identidade
        left_col = ctk.CTkFrame(about_body, fg_color="transparent")
        left_col.pack(side="left", fill="x", expand=True)

        name_row = ctk.CTkFrame(left_col, fg_color="transparent")
        name_row.pack(anchor="w")
        ctk.CTkLabel(name_row, text="⚒️", font=ctk.CTkFont(size=22)).pack(side="left")
        ctk.CTkLabel(name_row, text="SysForge",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=ACCENT).pack(side="left", padx=(6, 0))
        ctk.CTkLabel(name_row, text=f"v{CURRENT_VERSION}",
                     font=ctk.CTkFont(size=11), text_color=TXT_MUTED
                     ).pack(side="left", padx=(8, 0), pady=(6, 0))

        ctk.CTkLabel(left_col,
                     text="Motor de implantação e otimização de bancadas Windows.",
                     font=ctk.CTkFont(size=12), text_color=TXT_DIM,
                     anchor="w").pack(anchor="w", pady=(6, 0))

        # Divisor vertical sutil
        ctk.CTkFrame(about_body, width=1, fg_color=BORDER).pack(
            side="left", fill="y", padx=28, pady=4)

        # Coluna direita — metadados + botão
        right_col = ctk.CTkFrame(about_body, fg_color="transparent")
        right_col.pack(side="left", fill="y")

        for icon, label, value in [
            ("👤", "Autor",      "M labs"),
            ("📧", "Contato",    "o_mendes@outlook.com.br"),
            ("📅", "Lançamento", "Maio 2026"),
            ("🖥️", "Plataforma", "Windows 10 / 11"),
        ]:
            meta_row = ctk.CTkFrame(right_col, fg_color="transparent")
            meta_row.pack(anchor="w", pady=2)
            ctk.CTkLabel(meta_row, text=icon, font=ctk.CTkFont(size=12), width=22).pack(side="left")
            ctk.CTkLabel(meta_row, text=f"{label}:", font=ctk.CTkFont(size=11),
                         text_color=TXT_MUTED, width=76, anchor="w").pack(side="left")
            ctk.CTkLabel(meta_row, text=value, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=TXT_DIM, anchor="w").pack(side="left")

        ctk.CTkButton(right_col, text="🔄 Verificar Atualizações", height=30,
                      font=ctk.CTkFont(size=11, weight="bold"),
                      fg_color=BG_MAIN, border_width=1, border_color=ACCENT,
                      text_color=ACCENT, hover_color="#1e293b", corner_radius=8,
                      command=lambda: check_for_updates(self, manual=True)
                      ).pack(anchor="w", pady=(10, 0))

        # ── Diagnóstico de Sistema ────────────────────────────────────────
        diag_card = self._card(scroll)
        diag_card.pack(fill="x", pady=(0, 14))

        diag_header = ctk.CTkFrame(diag_card, fg_color="transparent")
        diag_header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(diag_header, text="🔬 Diagnóstico Completo",
                     font=ctk.CTkFont(size=16, weight="bold"), text_color=ACCENT).pack(side="left")

        self.btn_refresh_diag = ctk.CTkButton(
            diag_header, text="🔄 Analisar", width=100, height=28,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=BG_MAIN, border_width=1, border_color=BORDER, hover_color="#334155",
            command=self._load_diagnostics
        )
        self.btn_refresh_diag.pack(side="right")

        # Container para colunas
        diag_body = ctk.CTkFrame(diag_card, fg_color="transparent")
        diag_body.pack(fill="x", padx=20, pady=(0, 20))
        
        col_left = ctk.CTkFrame(diag_body, fg_color="transparent")
        col_left.pack(side="left", fill="both", expand=True, padx=(0, 10), anchor="n")
        
        col_right = ctk.CTkFrame(diag_body, fg_color="transparent")
        col_right.pack(side="left", fill="both", expand=True, padx=(10, 0), anchor="n")

        # Helper UI
        def _section(parent, title):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(fill="x", pady=(0, 20))
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="white").pack(anchor="w")
            ctk.CTkFrame(f, height=1, fg_color=BORDER).pack(fill="x", pady=4)
            content_frame = ctk.CTkFrame(f, fg_color="transparent")
            content_frame.pack(anchor="w", fill="x")
            return content_frame

        self._diag_os     = _section(col_left, "Sistema Operacional")
        self._diag_disks  = _section(col_left, "Armazenamento Físico")
        self._diag_fw     = _section(col_left, "Segurança (Firewall)")
        self._diag_java   = _section(col_left, "Java Runtime")
        
        self._diag_av     = _section(col_right, "Segurança (Antivírus)")
        self._diag_soft   = _section(col_right, "Dependências de Software")
        self._diag_dev    = _section(col_right, "Ferramentas de Desenvolvimento")

        # Inicia a leitura do diagnóstico
        threading.Thread(target=self._load_diagnostics, daemon=True).start()

    def _load_diagnostics(self):
        self.after(0, lambda: self.btn_refresh_diag.configure(state="disabled", text="⏳ Aguarde..."))

        def _clear(f):
            for w in f.winfo_children(): w.destroy()
        for f in [self._diag_os, self._diag_disks, self._diag_av, self._diag_fw, self._diag_soft, self._diag_java, self._diag_dev]:
            self.after(0, lambda frame=f: _clear(frame))

        # Roda o script de info pesada
        r = get_full_system_report()

        self.after(0, lambda: self._render_diagnostics(r))

    def _render_diagnostics(self, r):
        def _lines(f, items):
            for t, c in items:
                ctk.CTkLabel(f, text=t, font=ctk.CTkFont(size=11), text_color=c, justify="left").pack(anchor="w")

        # OS
        os_info = r["windows"]
        act = r["activation"]
        is_licensed = "✅" in act['status']
        name_str = f"{os_info.get('product', '')} {os_info.get('edition', '')}".replace("  ", " ").strip()
        build_str = f"Build {os_info.get('build', '')} ({os_info.get('arch', '')})"

        _lines(self._diag_os, [
            (name_str,          "white"),
            (build_str,         TXT_DIM),
            (f"Ativação: {act['status']}", GREEN if is_licensed else RED),
            (f"Tipo: {act['type']}",     TXT_DIM),
        ])

        # Discos Físicos
        disks = r.get("disks", [])
        if disks and "Nenhum" not in disks[0] and "Erro" not in disks[0]:
            d_lines = []
            for d in disks:
                color = CYAN if "[SSD]" in d else (TXT_MUTED if "[HDD]" in d else TXT_DIM)
                d_lines.append((f"💿 {d}", color))
        else:
            d_lines = [("⚠️ Não foi possível listar", AMBER)]
        _lines(self._diag_disks, d_lines)

        # Antivírus
        av_lines = []
        for av in r["antivirus"]:
            status_icon = "✅" if av["enabled"] else "❌"
            upd_icon    = "🟢" if av["updated"]  else "🔴"
            av_lines.append((f"{status_icon} {av['name']}", GREEN if av["enabled"] else RED))
            av_lines.append((f"   Definições: {upd_icon}",    TXT_DIM))
        _lines(self._diag_av, av_lines or [("⚠️ Nenhum detectado", AMBER)])

        # Firewall
        fw = r["firewall"]
        fw_lines = [(f"{prof}: {'ON ✅' if st == 'ON' else 'OFF ❌'}",
                     GREEN if st == "ON" else RED) for prof, st in fw.items()]
        _lines(self._diag_fw, fw_lines or [("⚠️ Não verificado", AMBER)])

        # Software (.NET, DirectX, VC++)
        dn = r["dotnet"]
        soft_lines = [
            (f".NET Framework: {dn['framework']}", TXT_DIM),
            (f".NET Core/5+:   {dn['core']}",      TXT_DIM),
            (f"DirectX: {r['directx']}",           TXT_DIM),
        ]
        vc = r["vcredist"]
        soft_lines.append((f"VC++ Redist: {len([v for v in vc if 'Nenhum' not in v])} versões", TXT_DIM))
        _lines(self._diag_soft, soft_lines)

        # Java
        java = r["java"]
        jre_color = GREEN if java["jre"] != "Não encontrado" else TXT_MUTED
        jdk_color = GREEN if java["jdk"] != "Não encontrado" else TXT_MUTED
        _lines(self._diag_java, [
            (f"JRE: {java['jre']}", jre_color),
            (f"JDK: {java['jdk']}", jdk_color),
        ])

        # Dev Tools / Bancos de Dados
        dev_tools = r.get("dev_tools", [])
        if dev_tools and dev_tools[0] != "Nenhum detectado":
            dev_lines = [(d, TXT_DIM) for d in dev_tools]
        else:
            dev_lines = [("⚠️ Nenhuma ferramenta detectada", AMBER)]
        _lines(self._diag_dev, dev_lines)

        self.btn_refresh_diag.configure(state="normal", text="🔄 Analisar")
