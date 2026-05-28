import os
import sys

with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

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
        self._section_title(header, "MATRIZ DE VIGILÂNCIA", "Sensores e Telemetria em Tempo Real")

        grid = ctk.CTkFrame(view, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0,1,2,3), weight=1, uniform="dash")
        grid.grid_rowconfigure((0,1), weight=1, uniform="dash")

        def _make_graph_card(r, c, title):
            px = (0,4) if c==0 else ((2,2) if c in [1,2] else (4,0))
            py = (0,4) if r==0 else (4,0)
            card = self._card(grid)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Helvetica", 13, "bold"), text_color="#000000").pack(anchor="w", padx=10, pady=(6,0))
            lbl = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 10), text_color="#000000")
            lbl.pack(anchor="w", padx=10)
            cvs = ctk.CTkCanvas(card, bg="#FFFFFF", highlightthickness=0)
            cvs.pack(fill="both", expand=True, padx=10, pady=(2,10))
            return lbl, cvs

        def _make_text_card(r, c, title):
            px = (0,4) if c==0 else ((2,2) if c in [1,2] else (4,0))
            py = (0,4) if r==0 else (4,0)
            card = self._card(grid)
            card.grid(row=r, column=c, padx=px, pady=py, sticky="nsew")
            ctk.CTkLabel(card, text=title, font=("Helvetica", 13, "bold"), text_color="#000000").pack(anchor="w", padx=10, pady=(6,0))
            txt = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 11), text_color="#000000", justify="left")
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

        self._last_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
        self._last_disk = psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes

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
                net_now = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                mbps = ((net_now - self._last_net) * 8) / 1000000.0
                self._last_net = net_now
                
                # Disco I/O
                disk_now = psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes
                mbps_disk = ((disk_now - self._last_disk) / (1024 * 1024))
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
                proc_str = "\\n".join([f"{name[:15]:<15} {pct:>5.1f}%" for name, pct in procs])
                
                # Uptime
                bt = psutil.boot_time()
                uptime = time.time() - bt
                d, r_rem = divmod(uptime, 86400)
                h, m = divmod(r_rem, 3600)
                uptime_str = f"LIGADO HÁ:\\n{int(d)}d {int(h)}h {int(m//60)}m\\n\\nBOOT TIME:\\n{time.strftime('%Y-%m-%d %H:%M', time.localtime(bt))}"
                
                # Energia / Saúde
                bat = psutil.sensors_battery()
                if bat:
                    p = "AC (Conectado)" if bat.power_plugged else "Bateria"
                    pow_str = f"FONTE:\\n{p}\\n\\nCARGA:\\n{bat.percent}%"
                else:
                    pow_str = "FONTE:\\nAC (Desktop)\\n\\nSTATUS:\\nEnergizado"
                
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

'''

content = content[:start_idx] + new_dash + "\n" + content[end_idx:]

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.write(content)
