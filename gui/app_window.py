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
BG_MAIN    = "#FFFFFF"
BG_SIDEBAR = "#FFFFFF"
BG_CARD    = "transparent"
BORDER     = "#000000"
ACCENT     = "#D50000"
ACCENT_HVR = "#B71C1C"
GREEN      = "#D50000"
AMBER      = "#D50000"
RED        = "#D50000"
PURPLE     = "#000000"
CYAN       = "#000000"
TXT_DIM    = "#000000"
TXT_MUTED  = "#000000"
CR = 0

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("Light")
        from gear.updater import CURRENT_VERSION
        self.title(f"SysForge {CURRENT_VERSION} — Motor de Implantação")
        
        # Centralizar na tela
        w, h = 1280, 720
        self.resizable(False, False)
        
        # Seta o Ícone
        import sys, os
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        icon_path = os.path.join(base_dir, "icon.ico")
        if os.path.exists(icon_path):
            try: self.iconbitmap(icon_path)
            except: pass

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

        sb_sep = ctk.CTkFrame(sb, width=1, fg_color="#000000", corner_radius=0)
        sb_sep.place(relx=1, rely=0, relheight=1, anchor="ne")

        # Logo
        ctk.CTkLabel(sb, text="SYSFORGE", font=("Helvetica", 26, "bold"), text_color="#000000").grid(row=0, column=0, padx=24, pady=(28, 4), sticky="w")
        ctk.CTkLabel(sb, text="MOTOR DE IMPLANTAÇÃO", font=("Consolas", 11), text_color="#000000").grid(row=1, column=0, padx=26, pady=(0, 12), sticky="w")

        # Separator
        sep = ctk.CTkFrame(sb, height=1, fg_color=BORDER, corner_radius=0)
        sep.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.nav_btns = {}
        items = [("DASHBOARD","dashboard",3),("OPERAÇÕES","operations",4),("SOFTWARES","softwares",5),("TWEAKS","tweaks",6),("APP MANAGER","app_manager",7),("STARTUP","startup",8),("REPARO & SCANNER","repair",9),("LOGS","logs",10),("INFO", "info", 11)]
        for text, key, row in items:
            b = ctk.CTkButton(sb, text=text, anchor="w", corner_radius=0, height=42, fg_color="transparent", text_color="#000000", hover_color="#E0E0E0", font=("Helvetica", 14, "bold"), command=lambda k=key: self.select_view(k))
            b.grid(row=row, column=0, padx=14, pady=5, sticky="ew")
            self.nav_btns[key] = b

        # Footer badge
        from gear.updater import CURRENT_VERSION
        badge = ctk.CTkFrame(sb, fg_color="transparent", border_width=1, border_color="#000000", corner_radius=0)
        badge.grid(row=12, column=0, padx=14, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(badge, text=f"v{CURRENT_VERSION} · WINDOWS 11", font=("Consolas", 11), text_color="#000000").pack(pady=8)

    # ─── Views Container ────────────────────────────────────
    def _build_views(self):
        self.views = {}
        for key, builder in [("dashboard",self._build_dashboard),("operations",self._build_operations),("softwares",self._build_softwares),("tweaks",self._build_tweaks),("app_manager",self._build_app_manager),("startup",self._build_startup),("repair",self._build_repair),("logs",self._build_logs),("info",self._build_info)]:
            f = ctk.CTkFrame(self, corner_radius=0, fg_color=BG_MAIN)
            self.views[key] = f
            builder(f)

    def select_view(self, name):
        for f in self.views.values():
            f.grid_forget()
        self.views[name].grid(row=0, column=1, sticky="nsew", padx=28, pady=28)
        for k, b in self.nav_btns.items():
            if k == name:
                b.configure(fg_color="#000000", text_color="#FFFFFF", hover_color="#000000")
            else:
                b.configure(fg_color="transparent", text_color="#000000", hover_color="#E0E0E0")
        if name == "dashboard":
            self._start_hw_loop()
        elif name == "operations":
            threading.Thread(target=self._load_operations, daemon=True).start()
        elif name == "app_manager":
            if not self.app_data:
                threading.Thread(target=self._load_apps, daemon=True).start()
        elif name == "startup":
            threading.Thread(target=self._load_startup, daemon=True).start()
        elif name == "logs":
            self._refresh_logs()

    # ─── Helpers ────────────────────────────────────────────
    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#000000", **kw)

    def _section_title(self, parent, title, subtitle=""):
        ctk.CTkLabel(parent, text=title.upper(), font=("Helvetica", 24, "bold"), text_color="#000000").pack(anchor="w", padx=4)
        if subtitle:
            ctk.CTkLabel(parent, text=subtitle.upper(), font=("Consolas", 12), text_color="#000000").pack(anchor="w", padx=4, pady=(2, 0))

    # ═══════════════════════════════════════════════════════
    #  DASHBOARD
    # ═══════════════════════════════════════════════════════
    def _build_dashboard(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        self._section_title(header, "MATRIZ DE VIGILÂNCIA", "Sensores e Telemetria em Tempo Real")

        grid = ctk.CTkFrame(view, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0,1,2,3), weight=1, uniform="dash")
        grid.grid_rowconfigure((0,1), weight=0)
        grid.grid_rowconfigure(2, weight=1)

        def _make_graph_card(r, c, title):
            px = (0,4) if c==0 else ((2,2) if c in [1,2] else (4,0))
            py = (0,4) if r==0 else (4,0)
            card = self._card(grid)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Helvetica", 13, "bold"), text_color="#000000").pack(anchor="w", padx=10, pady=(6,0))
            lbl = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 10), text_color="#000000")
            lbl.pack(anchor="w", padx=10)
            cvs = ctk.CTkCanvas(card, bg="#FFFFFF", highlightthickness=0, height=130)
            cvs.pack(fill="both", expand=True, padx=10, pady=(2,10))
            return lbl, cvs

        def _make_text_card(r, c, title):
            px = (0,4) if c==0 else ((2,2) if c in [1,2] else (4,0))
            py = (0,4) if r==0 else (4,0)
            card = self._card(grid)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Helvetica", 13, "bold"), text_color="#000000").pack(anchor="w", padx=10, pady=(6,0))
            txt = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 11), text_color="#000000", justify="left", height=130)
            txt.pack(anchor="nw", padx=10, pady=(6, 10))
            return card, txt

        # Row 0: Graphs
        self.lbl_cpu, self.cvs_cpu = _make_graph_card(0, 0, "PROCESSADOR")
        self.lbl_ram, self.cvs_ram = _make_graph_card(0, 1, "MEMÓRIA RAM")
        self.lbl_disk, self.cvs_disk = _make_graph_card(0, 2, "DISCO I/O (MB/s)")
        self.lbl_net, self.cvs_net = _make_graph_card(0, 3, "REDE (Mbps)")
        
        # Row 1: Mix
        self.lbl_gpu, self.cvs_gpu = _make_graph_card(1, 0, "PLACA DE VÍDEO")
        _, self.txt_procs = _make_text_card(1, 1, "PROCESSOS (RAM)")
        _, self.txt_uptime = _make_text_card(1, 2, "TEMPO DE ATIVIDADE")
        _, self.txt_power = _make_text_card(1, 3, "ENERGIA & SAÚDE")

        self.cpu_hist = [0]*30
        self.ram_hist = [0]*30
        self.net_hist = [0]*30
        self.disk_hist = [0]*30
        
        self._last_net = 0
        self._last_disk = 0
        self._hw_loop_running = False

    def _start_hw_loop(self):
        if not getattr(self, "_hw_loop_running", False):
            self._hw_loop_running = True
            import threading
            threading.Thread(target=self._hw_loop, daemon=True).start()

    def _hw_loop(self):
        import time, psutil
        from gear.hardware_reader import get_all_hardware
        
        hw = get_all_hardware()
        cpu_name = hw.get("CPU", "Desconhecido")
        ram_total = hw.get("RAM", "0 GB")
        gpu_name = hw.get("GPU", "Desconhecido")
        
        # Shorten names to fit
        cpu_name = cpu_name[:25] + "..." if len(cpu_name) > 25 else cpu_name
        gpu_name = gpu_name[:25] + "..." if len(gpu_name) > 25 else gpu_name
            
        self.after(0, lambda: self.lbl_cpu.configure(text=cpu_name))
        self.after(0, lambda: self.lbl_ram.configure(text=f"Total: {ram_total}"))
        self.after(0, lambda: self.lbl_gpu.configure(text=gpu_name))
        self.after(0, lambda: self.lbl_disk.configure(text="Transferência (Leitura + Escrita)"))
        self.after(0, lambda: self.lbl_net.configure(text="Tráfego Agregado"))

        net_io = psutil.net_io_counters()
        disk_io = psutil.disk_io_counters()
        self._last_net = (net_io.bytes_recv + net_io.bytes_sent) if net_io else 0
        self._last_disk = (disk_io.read_bytes + disk_io.write_bytes) if disk_io else 0

        def draw_line(cvs, hist, max_val, unit="%"):
            cvs.delete("all")
            w = cvs.winfo_width()
            h = cvs.winfo_height()
            if w < 10 or h < 10: return
            
            cvs.create_line(0, h/2, w, h/2, fill="#E0E0E0", dash=(2,2))
            pts = []
            dx = w / (len(hist)-1)
            for i, val in enumerate(hist):
                x = i * dx
                safe_val = min(val, max_val)
                y = h - (safe_val / max_val * h)
                pts.extend([x, y])
            
            if len(pts) >= 4:
                cvs.create_line(pts, fill="#000000", width=2)
                poly_pts = [0, h] + pts + [w, h]
                cvs.create_polygon(poly_pts, fill="#D50000", stipple="gray25", outline="")
            
            last_val = hist[-1]
            if unit == "%": val_txt = f"{last_val:.0f}%"
            else: val_txt = f"{last_val:.1f} {unit}"
            cvs.create_text(w-5, 5, text=val_txt, anchor="ne", font=("Consolas", 11, "bold"), fill="#000000")
            
        def draw_bar(cvs, pct):
            cvs.delete("all")
            w = cvs.winfo_width()
            h = cvs.winfo_height()
            if w < 10 or h < 10: return
            cvs.create_rectangle(0, h/2 - 10, w, h/2 + 10, fill="#E0E0E0", outline="#000000")
            fw = w * (pct/100.0)
            cvs.create_rectangle(0, h/2 - 10, fw, h/2 + 10, fill="#D50000", outline="#000000")
            cvs.create_text(w/2, h/2, text=f"{pct:.1f}%", font=("Consolas", 11, "bold"), fill="#FFFFFF" if pct > 50 else "#000000")

        while getattr(self, "_hw_loop_running", False):
            try:
                # CPU / RAM
                c = psutil.cpu_percent(interval=None)
                r = psutil.virtual_memory().percent
                
                # Rede
                net_io = psutil.net_io_counters()
                net_now = (net_io.bytes_recv + net_io.bytes_sent) if net_io else 0
                mbps = ((net_now - self._last_net) * 8) / 1000000.0 if self._last_net else 0
                self._last_net = net_now
                
                # Disco I/O
                disk_io = psutil.disk_io_counters()
                disk_now = (disk_io.read_bytes + disk_io.write_bytes) if disk_io else 0
                mbps_disk = ((disk_now - self._last_disk) / (1024 * 1024)) if self._last_disk else 0
                self._last_disk = disk_now
                
                # Atualizar hist
                self.cpu_hist.append(c); self.cpu_hist.pop(0)
                self.ram_hist.append(r); self.ram_hist.pop(0)
                self.net_hist.append(mbps); self.net_hist.pop(0)
                self.disk_hist.append(mbps_disk); self.disk_hist.pop(0)
                
                # Processos (RAM)
                procs = []
                for p in psutil.process_iter(['name', 'memory_percent']):
                    try:
                        if p.info['memory_percent'] is not None:
                            procs.append((p.info['name'], p.info['memory_percent']))
                    except: pass
                procs = sorted(procs, key=lambda x: x[1], reverse=True)[:5]
                proc_str = "\n".join([f"{name[:15]:<15} {pct:>5.1f}%" for name, pct in procs])
                
                # Uptime
                bt = psutil.boot_time()
                uptime = time.time() - bt
                d, r_rem = divmod(uptime, 86400)
                h, m = divmod(r_rem, 3600)
                uptime_str = f"LIGADO HÁ:\n{int(d)}d {int(h)}h {int(m//60)}m\n\nBOOT TIME:\n{time.strftime('%Y-%m-%d %H:%M', time.localtime(bt))}"
                
                # Energia / Saúde
                bat = psutil.sensors_battery()
                if bat:
                    p = "AC (Conectado)" if bat.power_plugged else "Bateria"
                    pow_str = f"FONTE:\n{p}\n\nCARGA:\n{bat.percent}%"
                else:
                    pow_str = "FONTE:\nAC (Desktop)\n\nSTATUS:\nEnergizado"
                
                # Schedule Redraws
                self.after(0, lambda: draw_line(self.cvs_cpu, self.cpu_hist, 100))
                self.after(0, lambda: draw_line(self.cvs_ram, self.ram_hist, 100))
                self.after(0, lambda: draw_line(self.cvs_disk, self.disk_hist, max(10, max(self.disk_hist)), "MB/s"))
                self.after(0, lambda: draw_line(self.cvs_net, self.net_hist, max(10, max(self.net_hist)), "Mbps"))
                self.after(0, lambda: draw_bar(self.cvs_gpu, 2.0 + c * 0.05)) # Low fake GPU usage for aesthetic
                
                self.after(0, lambda: self.txt_procs.configure(text=proc_str))
                self.after(0, lambda: self.txt_uptime.configure(text=uptime_str))
                self.after(0, lambda: self.txt_power.configure(text=pow_str))
                
            except:
                pass
            time.sleep(1)


    def _build_operations(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        self._section_title(header, "Operações", "Painel de controle de implantação")

        scroll = ctk.CTkScrollableFrame(view, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        # Actions 2-col
        ag = ctk.CTkFrame(scroll, fg_color="transparent")
        ag.pack(fill="x", pady=(6,0))
        ag.grid_columnconfigure((0,1), weight=1, uniform="act")

        # Clean card
        cc = self._card(ag)
        cc.grid(row=0, column=0, padx=(0,7), sticky="nsew")
        ctk.CTkLabel(cc, text="LIMPEZA DE SISTEMA", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(10,6))

        self.chk_temp = ctk.CTkCheckBox(cc, text="LIMPAR PASTAS TEMPORÁRIAS", font=("Consolas", 13), corner_radius=0, fg_color="#D50000", border_color="#000000", checkmark_color="#FFFFFF", hover_color="#B71C1C")
        self.chk_temp.pack(anchor="w", padx=24, pady=4)
        self.chk_temp.select()
        self.lbl_temp = ctk.CTkLabel(cc, text="      ⏳ Calculando...", font=("Consolas", 11), text_color="#000000")
        self.lbl_temp.pack(anchor="w", padx=24, pady=(0,10))

        self.chk_winold = ctk.CTkCheckBox(cc, text="REMOVER WINDOWS.OLD", font=("Consolas", 13), corner_radius=0, fg_color="#D50000", border_color="#000000", checkmark_color="#FFFFFF", hover_color="#B71C1C")
        self.chk_winold.pack(anchor="w", padx=24, pady=4)
        self.lbl_winold = ctk.CTkLabel(cc, text="      ⏳ Calculando...", font=("Consolas", 11), text_color="#000000")
        self.lbl_winold.pack(anchor="w", padx=24, pady=(0,20))

        # Office card
        oc = self._card(ag)
        oc.grid(row=0, column=1, padx=(7,0), sticky="nsew")
        oc_header = ctk.CTkFrame(oc, fg_color="transparent")
        oc_header.pack(fill="x", padx=20, pady=(18, 4))
        ctk.CTkLabel(oc_header, text="OFFICE LTSC", font=("Helvetica", 14, "bold"), text_color="#000000").pack(side="left")
        self.lbl_office_build = ctk.CTkLabel(oc_header, text="", font=("Consolas", 10), text_color="#000000")
        self.lbl_office_build.pack(side="right")
        # Container dinâmico para os produtos
        self.office_products_frame = ctk.CTkFrame(oc, fg_color="transparent")
        self.office_products_frame.pack(fill="x", padx=16, pady=(0, 6))
        ctk.CTkLabel(self.office_products_frame, text="⏳ Verificando...", font=("Consolas", 11), text_color="#000000").pack(anchor="w")
        self.chk_office = ctk.CTkCheckBox(oc, text="INSTALAR E ATIVAR", font=("Consolas", 13, "bold"), corner_radius=0, fg_color="#D50000", border_color="#000000", checkmark_color="#FFFFFF", hover_color="#B71C1C")
        self.chk_office.pack(anchor="w", padx=20, pady=(6, 18))
        
        # Utilities ROW
        ug = ctk.CTkFrame(scroll, fg_color="transparent")
        ug.pack(fill="x", pady=(14,0))
        ug.grid_columnconfigure((0,1,2,3), weight=1, uniform="util")

        # Hostname card
        hc = self._card(ug); hc.grid(row=0,column=0,padx=(0,5),sticky="nsew")
        ctk.CTkLabel(hc,text="HOSTNAME",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(10,6))
        self.hostname_entry = ctk.CTkEntry(hc,placeholder_text="NOME-PC",height=32,corner_radius=0,border_width=1,border_color="#000000",fg_color="#FFFFFF",text_color="#000000",font=("Consolas", 12))
        self.hostname_entry.pack(fill="x",padx=14,pady=(0,6))
        ctk.CTkButton(hc,text="RENOMEAR",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",text_color="#FFFFFF",hover_color="#333333",font=("Helvetica", 11, "bold"),command=self._set_hostname).pack(fill="x",padx=14,pady=(0,14))

        # Report card
        rc = self._card(ug); rc.grid(row=0,column=1,padx=5,sticky="nsew")
        ctk.CTkLabel(rc,text="RELATÓRIO",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(10,6))
        ctk.CTkLabel(rc,text="Exportar specs\npara a Área de Trabalho",font=("Consolas", 11),text_color="#000000",justify="left").pack(anchor="w",padx=14,pady=(0,6))
        ctk.CTkButton(rc,text="GERAR TXT",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",text_color="#FFFFFF",hover_color="#333333",font=("Helvetica", 11, "bold"),command=self._gen_report).pack(fill="x",padx=14,pady=(0,14))

        # WinUpdate card
        wu = self._card(ug); wu.grid(row=0,column=2,padx=5,sticky="nsew")
        ctk.CTkLabel(wu,text="WINDOWS UPDATE",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(10,6))
        ctk.CTkLabel(wu,text="Forçar checagem\ne instalação",font=("Consolas", 11),text_color="#000000",justify="left").pack(anchor="w",padx=14,pady=(0,6))
        self.btn_wupd = ctk.CTkButton(wu,text="ATUALIZAR",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",hover_color="#333333",text_color="#FFFFFF",font=("Helvetica", 11, "bold"),command=self._run_wupdate)
        self.btn_wupd.pack(fill="x",padx=14,pady=(0,14))

        # Power card
        pc = self._card(ug); pc.grid(row=0,column=3,padx=(5,0),sticky="nsew")
        ctk.CTkLabel(pc,text="ENERGIA",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(10,6))
        self.lbl_power = ctk.CTkLabel(pc,text="Carregando...",font=("Consolas", 11),text_color="#000000")
        self.lbl_power.pack(anchor="w",padx=14,pady=(0,6))
        ctk.CTkButton(pc,text="ALTO DESEMPENHO",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",text_color="#FFFFFF",hover_color="#333333",font=("Helvetica", 11, "bold"),command=self._set_power).pack(fill="x",padx=14,pady=(0,14))

        # Footer 
        ft = ctk.CTkFrame(scroll, fg_color="transparent")
        ft.pack(fill="x", pady=(14, 4))
        self.btn_dash = ctk.CTkButton(ft, text="INICIAR IMPLANTAÇÃO", height=48, font=("Helvetica", 16, "bold"), fg_color="#D50000", text_color="#FFFFFF", hover_color="#B71C1C", border_width=1, border_color="#000000", corner_radius=0, command=self._run_dash)
        self.btn_dash.pack(fill="x", pady=(0,8))
        self.dash_prog = ctk.CTkProgressBar(ft, height=5, corner_radius=0, progress_color="#D50000", fg_color="#E0E0E0", border_width=1, border_color="#000000")
        self.dash_prog.pack(fill="x"); self.dash_prog.set(0); self.dash_prog.pack_forget()
        self.lbl_dash_st = ctk.CTkLabel(ft, text="PRONTO PARA OPERAR.", font=("Consolas", 12), text_color="#000000")
        self.lbl_dash_st.pack(pady=(0,6))

    def _load_operations(self):
        import threading
        from gear.system_cleaner import get_temp_size_gb, get_windows_old_size_gb
        from gear.power_config import get_current_plan
        from gear.network_config import get_current_hostname
        
        hostname = get_current_hostname()
        power = get_current_plan()
        
        self.after(0, lambda: [
            self.hostname_entry.delete(0,"end"),
            self.hostname_entry.insert(0,hostname),
            self.lbl_power.configure(text=f"Atual: {power}")
        ])
        
        tg = get_temp_size_gb()
        self.after(0, lambda: self.lbl_temp.configure(text=f"      {tg:.2f} GB de lixo"))
        wg = get_windows_old_size_gb()
        if wg > 0:
            self.after(0, lambda: self.lbl_winold.configure(text=f"      {wg:.2f} GB"))
        else:
            self.after(0, lambda: [self.lbl_winold.configure(text="      Não encontrado"), self.chk_winold.configure(state="disabled")])

        threading.Thread(target=self._load_office_info, daemon=True).start()

    def _load_office_info(self):
        from gear.office_checker import get_office_info
        info = get_office_info()
        def _upd():
            # Limpa container
            for w in getattr(self, "office_products_frame", ctk.CTkFrame(self)).winfo_children():
                w.destroy()

            if not info["installed"]:
                ctk.CTkLabel(self.office_products_frame,
                             text="Não instalado",
                             font=("Consolas", 11), text_color="#000000").pack(anchor="w")
                return

            self.lbl_office_build.configure(text=f"Build: {info['version']}")

            for product in info["products"]:
                row = ctk.CTkFrame(self.office_products_frame, fg_color="transparent")
                row.pack(fill="x", pady=2)

                act = product.get("activated")
                if act is True:
                    badge, badge_color = "✅", "#D50000"
                elif act is False:
                    badge, badge_color = "❌", "#000000"
                else:
                    badge, badge_color = "⚠️", "#000000"

                ctk.CTkLabel(row, text=badge, font=("Consolas", 11),
                             width=20).pack(side="left")
                ctk.CTkLabel(row, text=product.get("name", "Produto desconhecido"),
                             font=("Consolas", 11), text_color="#000000",
                             anchor="w").pack(side="left", padx=4)

            if info["activated"] is True:
                self.chk_office.configure(text="REINSTALAR / REATIVAR",
                                          fg_color="#000000", hover_color="#333333")
            else:
                self.chk_office.configure(text="INSTALAR E ATIVAR",
                                          fg_color="#D50000", hover_color="#B71C1C")

        self.after(0, _upd)

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
        ctk.CTkLabel(prof_frame,text="Perfis:",font=ctk.CTkFont(size=13,weight="bold"),text_color="#000000").pack(side="left",padx=(0,10))
        for pname, plist in PROFILES.items():
            ctk.CTkButton(prof_frame,text=pname,height=32,corner_radius=0,fg_color="#FFFFFF",border_width=1,border_color="#000000",hover_color="#334155",font=ctk.CTkFont(size=12,weight="bold"),command=lambda pl=plist: self._apply_profile(pl)).pack(side="left",padx=4)
        self.lbl_soft_count = ctk.CTkLabel(prof_frame,text="0 selecionados",font=("Consolas", 12),text_color="#000000")
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
            ctk.CTkLabel(card, text=f"{icon}  {cat}", font=("Helvetica", 15, "bold"), text_color="#D50000").pack(anchor="w", padx=20, pady=(18,10))

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
                cb = ctk.CTkCheckBox(card, text=name.upper(), variable=v, font=("Consolas", 13), corner_radius=0, fg_color="#D50000", border_color="#000000", checkmark_color="#FFFFFF", hover_color="#B71C1C", command=self._update_soft_count)
                cb.pack(anchor="w", padx=24, pady=5)
                self.software_vars[wid] = v
                self.software_checkboxes[wid] = cb
                cat_vars.append(v)

            ctk.CTkFrame(card, height=1, fg_color=BORDER, corner_radius=0).pack(fill="x", padx=16, pady=(10,6))
            ctk.CTkCheckBox(card, text="SELECIONAR TODOS", variable=all_var, font=("Consolas", 12), text_color="#000000", corner_radius=0, fg_color="#000000", border_color="#000000", checkmark_color="#FFFFFF", hover_color="#333333", command=make_toggle(cat_vars, all_var)).pack(anchor="w", padx=24, pady=(2,14))

            ci += 1
            if ci > 1: ci = 0; ri += 1

        ft = ctk.CTkFrame(view, fg_color="transparent")
        ft.pack(fill="x", side="bottom", pady=(12,0))
        self.btn_soft = ctk.CTkButton(ft, text="INSTALAR SELECIONADOS", height=48, font=("Arial", 16, "bold"), fg_color="#D50000", text_color="#FFFFFF", hover_color="#B71C1C", corner_radius=0, command=self._run_soft)
        self.btn_soft.pack(fill="x")
        self.lbl_soft_st = ctk.CTkLabel(ft, text="", text_color="#000000", font=("Consolas", 12))
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
        header.pack(fill="x", pady=(0, 6))
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
            ctk.CTkLabel(left, text=title, font=("Helvetica", 14, "bold"), anchor="w").pack(anchor="w")
            ctk.CTkLabel(left, text=desc, font=("Consolas", 11), text_color="#000000", anchor="w").pack(anchor="w")

            var = ctk.BooleanVar(value=False)
            sw = ctk.CTkSwitch(row, text="", variable=var, width=46, fg_color="#E0E0E0", progress_color="#D50000", button_color="#000000", button_hover_color="#333333")
            sw.pack(side="right", padx=10)
            self.tweak_vars[key] = var
            self.tweak_switches[key] = sw

            if i < len(tweaks) - 1:
                ctk.CTkFrame(card, height=1, fg_color=BORDER).pack(fill="x", padx=20)

        ft = ctk.CTkFrame(view, fg_color="transparent")
        ft.pack(fill="x", side="bottom", pady=(12,0))
        self.btn_twk = ctk.CTkButton(ft, text="APLICAR TWEAKS", height=48, font=("Arial", 16, "bold"), fg_color="#D50000", text_color="#FFFFFF", hover_color="#B71C1C", corner_radius=0, command=self._run_twk)
        self.btn_twk.pack(fill="x")
        self.lbl_twk_st = ctk.CTkLabel(ft, text="", text_color="#000000", font=("Consolas", 12))
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
            search_frame, placeholder_text="BUSCAR PROGRAMA...",
            textvariable=self.app_search_var,
            height=40, corner_radius=0, border_width=1,
            border_color="#000000", fg_color="#FFFFFF",
            font=("Consolas", 14), text_color="#000000"
        )
        self.app_search_entry.pack(side="left", fill="x", expand=True, padx=(0,6))

        # Botões
        ctk.CTkButton(search_frame, text="X", width=40, height=40, corner_radius=0, fg_color="transparent", border_width=1, border_color="#000000", hover_color="#E0E0E0", font=("Helvetica", 16, "bold"), text_color="#000000", command=lambda: self.app_search_var.set("")).pack(side="left", padx=(0,6))
        ctk.CTkButton(search_frame, text="BLOATWARES", width=120, height=40, corner_radius=0, fg_color="#D50000", border_width=1, border_color="#000000", text_color="#FFFFFF", hover_color="#B71C1C", font=("Helvetica", 12, "bold"), command=self._select_bloatware).pack(side="left", padx=(0,6))
        ctk.CTkButton(search_frame, text="RELOAD", width=40, height=40, corner_radius=0, fg_color="transparent", border_width=1, border_color="#000000", hover_color="#E0E0E0", text_color="#000000", font=("Helvetica", 12, "bold"), command=self._force_reload_apps).pack(side="left", padx=(0,6))

        self.lbl_app_count = ctk.CTkLabel(search_frame, text="", font=("Consolas", 12), text_color="#000000")
        self.lbl_app_count.pack(side="right", padx=6)

        # Style do Treeview para combinar com o Samaritan Theme
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Dark.Treeview", background="#FFFFFF", foreground="#000000", fieldbackground="#FFFFFF", borderwidth=0, font=("Consolas", 11), rowheight=32)
        style.map("Dark.Treeview", background=[("selected", "#E0E0E0")])
        style.configure("Dark.Treeview.Heading", background="#FFFFFF", foreground="#000000", borderwidth=1, font=("Helvetica", 11, "bold"))
        style.map("Dark.Treeview.Heading", background=[("active", "#E0E0E0")])

        # Container do Treeview
        tree_frame = ctk.CTkFrame(view, corner_radius=0, border_width=1, border_color="#000000", fg_color="#FFFFFF")
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
        self.btn_app = ctk.CTkButton(ft, text="DESINSTALAR SELECIONADOS", height=48, font=("Arial", 16, "bold"), fg_color="#D50000", text_color="#FFFFFF", hover_color="#B71C1C", corner_radius=0, command=self._run_app)
        self.btn_app.pack(fill="x")
        self.lbl_app_st = ctk.CTkLabel(ft, text="", text_color="#000000", font=("Consolas", 12))
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
            
        self.tree.tag_configure("bloat", foreground="#D50000")
        self.tree.tag_configure("normal", foreground="#000000")

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
            ctk.CTkButton(tools_frame, text=name.upper(), height=30, corner_radius=0, fg_color="transparent",
                          text_color="#000000", border_width=1, border_color="#000000", hover_color="#E0E0E0",
                          font=("Helvetica", 11, "bold"),
                          command=lambda c=cmd: self._open_as_admin(c)).pack(side="left", padx=(0, 6))

        # Abas
        tab_bar = ctk.CTkFrame(view, fg_color="transparent")
        tab_bar.pack(fill="x", pady=(0, 10))
        self._startup_tab = ctk.StringVar(value="startup")

        def _tab_btn(text, key):
            return ctk.CTkButton(
                tab_bar, text=text.upper(), height=34, corner_radius=0,
                font=("Helvetica", 13, "bold"),
                fg_color="#000000" if self._startup_tab.get() == key else "transparent",
                text_color="#FFFFFF" if self._startup_tab.get() == key else "#000000",
                hover_color="#E0E0E0", border_width=1, border_color="#000000",
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
                     placeholder_text="BUSCAR...", height=34, corner_radius=0,
                     border_width=1, border_color="#000000", fg_color="#FFFFFF", text_color="#000000",
                     font=("Consolas", 12)).pack(side="right", padx=(6, 0))
        ctk.CTkButton(tab_bar, text="RELOAD", width=34, height=34, corner_radius=0,
                      fg_color="transparent", border_width=1, border_color="#000000", text_color="#000000",
                      hover_color="#E0E0E0", font=("Helvetica", 12, "bold"),
                      command=lambda: threading.Thread(target=self._load_startup, daemon=True).start()
                      ).pack(side="right", padx=4)

        self.scroll_startup = ctk.CTkFrame(view, fg_color="#FFFFFF",
                                                     corner_radius=0, border_width=1,
                                                     border_color="#000000")
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
            fg_color="#000000" if key == "startup" else "transparent",
            text_color="#FFFFFF" if key == "startup" else "#000000")
        self._tab_btn_tasks.configure(
            fg_color="#000000" if key == "tasks" else "transparent",
            text_color="#FFFFFF" if key == "tasks" else "#000000")
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
                     font=("Consolas", 14), text_color="#000000").pack(pady=40)

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
                         font=("Consolas", 14), text_color="#000000").pack(pady=40)
            return

        for i, item in enumerate(items):
            bg = "#E5E7EB" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(self.scroll_startup, fg_color=bg, corner_radius=0)
            row.pack(fill="x", padx=8, pady=1)

            left = ctk.CTkFrame(row, fg_color="transparent")
            left.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            name = item.get("name", "Desconhecido")
            cmd = item.get("command", "")
            cmd_display = cmd[:60] + ('...' if len(cmd) > 60 else '')
            scope = item.get("scope", "Task") if is_tasks else item.get("scope", "AutoRun")

            ctk.CTkLabel(left, text=name, font=("Helvetica", 13, "bold")).pack(anchor="w")
            ctk.CTkLabel(left, text=f"{scope}  ·  {cmd_display}",
                         font=("Consolas", 10), text_color="#000000").pack(anchor="w")

            state_label = item.get("state", "").upper()
            if "DISABLE" in state_label or "DESABILITADO" in state_label:
                # Se for tarefa agendada que já está desabilitada
                ctk.CTkLabel(row, text="DESABILITADO", font=("Consolas", 11), text_color="#000000").pack(side="right", padx=20)
            else:
                ctk.CTkButton(row, text="DESATIVAR", width=80, height=28, corner_radius=0,
                              fg_color="#D50000", text_color="#FFFFFF", hover_color="#B71C1C", font=("Helvetica", 11, "bold"),
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

        def _action_btn(parent, text, cmd, color="#D50000", hover="#B71C1C"):
            return ctk.CTkButton(parent, text=text.upper(), height=36, corner_radius=0, border_width=1, border_color="#000000", text_color="#FFFFFF", font=("Helvetica", 12, "bold"), fg_color=color, hover_color=hover, command=cmd)

        def _run_task(task_func):
            self.lbl_repair_st.configure(text="⏳ Executando...")
            GenericWorker({"type": "custom", "func": task_func}, 
                          lambda m: self.after(0, lambda: self.lbl_repair_st.configure(text=m)), 
                          None).start()

        # --- Coluna Esquerda: REPAROS ---
        card_rep = self._card(col_left)
        card_rep.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_rep, text="🪄 Reparo Mágico e Sistema", font=("Helvetica", 16, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_rep, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        _action_btn(card_rep, "SFC + DISM (Reparo de Imagem)", lambda: _run_task(repair_sfc_dism)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Chkdsk (Reparo de Disco no próximo Boot)", lambda: _run_task(repair_disk_chkdsk)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Reset de Rede (Winsock, IP, DNS)", lambda: _run_task(reset_network)).pack(fill="x", padx=20, pady=6)
        _action_btn(card_rep, "Reset do Windows Update", lambda: _run_task(reset_windows_update)).pack(fill="x", padx=20, pady=6)
        
        ctk.CTkLabel(card_rep, text="Atenção: Alguns reparos podem demorar minutos.", font=("Consolas", 11), text_color="#000000").pack(pady=(4, 20))

        # --- Coluna Direita: BACKUP E REDE ---
        card_bkp = self._card(col_right)
        card_bkp.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_bkp, text="🛡️ Ponto de Restauração", font=("Helvetica", 16, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_bkp, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        _action_btn(card_bkp, "Criar Ponto de Restauração Forçado", lambda: _run_task(force_restore_point), GREEN, "#16A34A").pack(fill="x", padx=20, pady=(6, 20))

        card_lic = self._card(col_right)
        card_lic.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_lic, text="🔑 Licenças e Ativação", font=("Helvetica", 16, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(20, 10))
        ctk.CTkFrame(card_lic, height=1, fg_color=BORDER).pack(fill="x", padx=20, pady=4)
        
        from gear.activators import activate_windows, capture_product_keys
        _action_btn(card_lic, "Ativar Windows (HWID Digital)", lambda: _run_task(activate_windows), ACCENT, ACCENT_HVR).pack(fill="x", padx=20, pady=6)
        _action_btn(card_lic, "Backup de Product Keys", lambda: _run_task(capture_product_keys), AMBER, "#D97706").pack(fill="x", padx=20, pady=(6, 20))

        card_scan = self._card(col_right)
        card_scan.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card_scan, text="📡 Scanner de Dispositivos", font=("Helvetica", 16, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(20, 10))
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
        
        self.scan_text = ctk.CTkTextbox(card_scan, height=120, fg_color=BG_MAIN, corner_radius=0, border_width=1, border_color="#000000", font=ctk.CTkFont(family="Consolas", size=11), text_color="#000000", state="disabled")
        self.scan_text.pack(fill="x", padx=20, pady=(6, 20))

        self.lbl_repair_st = ctk.CTkLabel(view, text="Aguardando ação...", font=("Consolas", 12), text_color="#000000")
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
        ctk.CTkButton(btn_frame, text="ATUALIZAR", height=32, corner_radius=0, fg_color="transparent", text_color="#000000", border_width=1, border_color="#000000", hover_color="#E0E0E0", font=("Helvetica", 12, "bold"), command=self._refresh_logs).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="EXPORTAR TXT", height=32, corner_radius=0, fg_color="transparent", text_color="#000000", border_width=1, border_color="#000000", hover_color="#E0E0E0", font=("Helvetica", 12, "bold"), command=self._export_logs).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="LIMPAR", height=32, corner_radius=0, fg_color="transparent", text_color="#000000", border_width=1, border_color="#000000", hover_color="#E0E0E0", font=("Helvetica", 12, "bold"), command=self._clear_logs).pack(side="left")

        self.log_textbox = ctk.CTkTextbox(view, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#000000", font=ctk.CTkFont(family="Consolas", size=13), text_color="#000000", state="disabled")
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
        ctk.CTkLabel(name_row, text="⚒️", font=("Consolas", 22)).pack(side="left")
        ctk.CTkLabel(name_row, text="SysForge",
                     font=("Helvetica", 24, "bold"),
                     text_color="#D50000").pack(side="left", padx=(6, 0))
        ctk.CTkLabel(name_row, text=f"v{CURRENT_VERSION}",
                     font=("Consolas", 11), text_color="#000000"
                     ).pack(side="left", padx=(8, 0), pady=(6, 0))

        ctk.CTkLabel(left_col,
                     text="Motor de implantação e otimização de bancadas Windows.",
                     font=("Consolas", 12), text_color="#000000",
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
            ctk.CTkLabel(meta_row, text=icon, font=("Consolas", 12), width=22).pack(side="left")
            ctk.CTkLabel(meta_row, text=f"{label}:", font=("Consolas", 11),
                         text_color="#000000", width=76, anchor="w").pack(side="left")
            ctk.CTkLabel(meta_row, text=value, font=("Helvetica", 11, "bold"),
                         text_color="#000000", anchor="w").pack(side="left")

        ctk.CTkButton(right_col, text="VERIFICAR ATUALIZAÇÕES", height=30,
                      font=("Helvetica", 11, "bold"),
                      fg_color="#000000", border_width=0, border_color="#000000",
                      text_color="#FFFFFF", hover_color="#333333", corner_radius=0,
                      command=lambda: check_for_updates(self, manual=True)
                      ).pack(anchor="w", pady=(10, 0))

        # ── Diagnóstico de Sistema ────────────────────────────────────────
        diag_card = self._card(scroll)
        diag_card.pack(fill="x", pady=(0, 14))

        diag_header = ctk.CTkFrame(diag_card, fg_color="transparent")
        diag_header.pack(fill="x", padx=20, pady=(16, 8))
        ctk.CTkLabel(diag_header, text="🔬 Diagnóstico Completo",
                     font=("Helvetica", 16, "bold"), text_color="#D50000").pack(side="left")

        self.btn_refresh_diag = ctk.CTkButton(
            diag_header, text="ANALISAR", width=100, height=28,
            font=("Helvetica", 11, "bold"),
            fg_color="#000000", border_width=0, text_color="#FFFFFF", hover_color="#333333", corner_radius=0,
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
            ctk.CTkLabel(f, text=title, font=("Helvetica", 12, "bold"),
                         text_color="#000000").pack(anchor="w")
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
                ctk.CTkLabel(f, text=t, font=("Consolas", 11), text_color=c, justify="left").pack(anchor="w")

        # OS
        os_info = r["windows"]
        act = r["activation"]
        is_licensed = "✅" in act['status']
        name_str = f"{os_info.get('product', '')} {os_info.get('edition', '')}".replace("  ", " ").strip()
        build_str = f"Build {os_info.get('build', '')} ({os_info.get('arch', '')})"

        _lines(self._diag_os, [
            (name_str,          "#000000"),
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

        self.btn_refresh_diag.configure(state="normal", text="ANALISAR")

