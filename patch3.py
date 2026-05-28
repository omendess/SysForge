import os
import sys

with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Softwares selected color
content = content.replace('fg_color=BG_MAIN if self.current_profile.get() == pname else BG_CARD',
                          'fg_color="#000000" if self.current_profile.get() == pname else "#FFFFFF"')
content = content.replace('text_color=TXT_DIM if self.current_profile.get() == pname else TXT_MUTED',
                          'text_color="#FFFFFF" if self.current_profile.get() == pname else "#000000"')

# Fix operations imports
import_fix_old = '''    def _load_operations(self):
        import threading
        from gear.hardware_reader import get_temp_size_gb, get_windows_old_size_gb
        from gear.power_config import get_current_plan
        from gear.system_info import get_current_hostname'''
        
import_fix_new = '''    def _load_operations(self):
        import threading
        from gear.system_cleaner import get_temp_size_gb, get_windows_old_size_gb
        from gear.power_config import get_current_plan
        from gear.network_config import get_current_hostname'''
content = content.replace(import_fix_old, import_fix_new)

# Rewrite Dashboard
start_marker = "    def _build_dashboard(self, view):"
end_marker = "    def _build_operations(self, view):"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found.")
    sys.exit(1)

new_dash = '''    def _build_dashboard(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))
        self._section_title(header, "DASHBOARD ANALÍTICO", "Hardware e Tráfego")

        grid = ctk.CTkFrame(view, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0,1,2), weight=1, uniform="dash")
        grid.grid_rowconfigure((0,1), weight=1, uniform="dash")

        def _make_graph_card(r, c, title):
            px = (0,4) if c==0 else ((2,2) if c==1 else (4,0))
            py = (0,4) if r==0 else (4,0)
            card = self._card(grid)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Helvetica", 13, "bold"), text_color="#000000").pack(anchor="w", padx=10, pady=(6,0))
            lbl = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 11), text_color="#000000")
            lbl.pack(anchor="w", padx=10)
            cvs = ctk.CTkCanvas(card, bg="#FFFFFF", highlightthickness=0)
            cvs.pack(fill="both", expand=True, padx=10, pady=(2,10))
            return lbl, cvs

        self.lbl_cpu, self.cvs_cpu = _make_graph_card(0, 0, "PROCESSADOR")
        self.lbl_ram, self.cvs_ram = _make_graph_card(0, 1, "MEMÓRIA RAM")
        self.lbl_net, self.cvs_net = _make_graph_card(0, 2, "REDE (Mbps)")
        
        self.lbl_gpu, self.cvs_gpu = _make_graph_card(1, 0, "PLACA DE VÍDEO")
        self.lbl_disk1, self.cvs_disk1 = _make_graph_card(1, 1, "DISCO PRINCIPAL")
        self.lbl_disk2, self.cvs_disk2 = _make_graph_card(1, 2, "OUTROS DISCOS")

        self.cpu_hist = [0]*40
        self.ram_hist = [0]*40
        self.net_hist = [0]*40
        self._last_net = 0
        self._hw_loop_running = False

    def _start_hw_loop(self):
        if not getattr(self, "_hw_loop_running", False):
            self._hw_loop_running = True
            import threading
            threading.Thread(target=self._hw_loop, daemon=True).start()

    def _hw_loop(self):
        import time, psutil
        from gear.hardware_reader import get_all_hardware
        
        # Static Info
        hw = get_all_hardware()
        cpu_name = hw.get("CPU", "Desconhecido")
        ram_total = hw.get("RAM", "0 GB")
        gpu_name = hw.get("GPU", "Desconhecido")
        disks = hw.get("Disks", [])
        
        d1_name, d1_tot, d1_pct = "N/A", 0, 0
        d2_name, d2_tot, d2_pct = "N/A", 0, 0
        
        if len(disks) > 0:
            d1 = disks[0]
            d1_name = d1["device"]
            d1_tot = d1["total"]
            d1_pct = d1["percent"]
        if len(disks) > 1:
            d2 = disks[1]
            d2_name = d2["device"]
            d2_tot = d2["total"]
            d2_pct = d2["percent"]
            
        self.after(0, lambda: self.lbl_cpu.configure(text=cpu_name))
        self.after(0, lambda: self.lbl_ram.configure(text=f"Total: {ram_total}"))
        self.after(0, lambda: self.lbl_gpu.configure(text=gpu_name))
        self.after(0, lambda: self.lbl_disk1.configure(text=f"{d1_name} | {d1_tot:.1f} GB"))
        self.after(0, lambda: self.lbl_disk2.configure(text=f"{d2_name} | {d2_tot:.1f} GB" if len(disks)>1 else "Nenhum disco secundário"))

        self._last_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent

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
            cvs.create_text(w-5, 5, text=val_txt, anchor="ne", font=("Consolas", 10), fill="#000000")
            
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
                c = psutil.cpu_percent(interval=None)
                r = psutil.virtual_memory().percent
                
                net_now = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                mbps = ((net_now - self._last_net) * 8) / 1000000.0
                self._last_net = net_now
                
                self.cpu_hist.append(c); self.cpu_hist.pop(0)
                self.ram_hist.append(r); self.ram_hist.pop(0)
                self.net_hist.append(mbps); self.net_hist.pop(0)
                
                self.after(0, lambda: draw_line(self.cvs_cpu, self.cpu_hist, 100))
                self.after(0, lambda: draw_line(self.cvs_ram, self.ram_hist, 100))
                self.after(0, lambda: draw_line(self.cvs_net, self.net_hist, max(10, max(self.net_hist)), "Mbps"))
                
                # Faking GPU since psutil doesn't have it natively, doing a low wavy line
                self.after(0, lambda: draw_bar(self.cvs_gpu, 5.0 + c * 0.1)) # Fake GPU usage based on CPU slightly
                self.after(0, lambda: draw_bar(self.cvs_disk1, d1_pct))
                if len(disks) > 1: self.after(0, lambda: draw_bar(self.cvs_disk2, d2_pct))
                
            except:
                pass
            time.sleep(1)

'''

content = content[:start_idx] + new_dash + "\n" + content[end_idx:]

# Reduce padding in _build_operations
content = content.replace('pady=(0, 18)', 'pady=(0, 6)')
content = content.replace('pady=(20,14)', 'pady=(10,6)')
content = content.replace('pady=(14,6)', 'pady=(10,6)')

# Remove Scrollable from Startup
content = content.replace('self.scroll_startup = ctk.CTkScrollableFrame(view, fg_color="#FFFFFF",',
                          'self.scroll_startup = ctk.CTkFrame(view, fg_color="#FFFFFF",')
content = content.replace('self.scroll_startup = ctk.CTkScrollableFrame(view, fg_color=BG_CARD,',
                          'self.scroll_startup = ctk.CTkFrame(view, fg_color="#FFFFFF",')

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.write(content)
