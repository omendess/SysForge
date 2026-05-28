import sys

with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "    def _build_dashboard(self, view):"
end_marker = "    # ═══════════════════════════════════════════════════════\n    #  SOFTWARES"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found.")
    sys.exit(1)

new_code = '''    def _build_dashboard(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
        self._section_title(header, "Dashboard de Implantação", "Operação Bancada")

        grid = ctk.CTkFrame(view, fg_color="transparent")
        grid.pack(fill="both", expand=True)
        grid.grid_columnconfigure((0,1), weight=1, uniform="dash")
        grid.grid_rowconfigure((0,1), weight=1, uniform="dash")

        # CPU Card
        c_cpu = self._card(grid)
        c_cpu.grid(row=0, column=0, padx=(0,7), pady=(0,7), sticky="nsew")
        ctk.CTkLabel(c_cpu, text="PROCESSADOR", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.lbl_cpu_name = ctk.CTkLabel(c_cpu, text="Carregando...", font=("Consolas", 12), text_color="#000000")
        self.lbl_cpu_name.pack(anchor="w", padx=20)
        
        self.cvs_cpu = ctk.CTkCanvas(c_cpu, bg="#FFFFFF", highlightthickness=0)
        self.cvs_cpu.pack(fill="both", expand=True, padx=20, pady=10)
        
        # RAM Card
        c_ram = self._card(grid)
        c_ram.grid(row=0, column=1, padx=(7,0), pady=(0,7), sticky="nsew")
        ctk.CTkLabel(c_ram, text="MEMÓRIA RAM", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.lbl_ram_name = ctk.CTkLabel(c_ram, text="Carregando...", font=("Consolas", 12), text_color="#000000")
        self.lbl_ram_name.pack(anchor="w", padx=20)
        
        self.cvs_ram = ctk.CTkCanvas(c_ram, bg="#FFFFFF", highlightthickness=0)
        self.cvs_ram.pack(fill="both", expand=True, padx=20, pady=10)

        # GPU Card
        c_gpu = self._card(grid)
        c_gpu.grid(row=1, column=0, padx=(0,7), pady=(7,0), sticky="nsew")
        ctk.CTkLabel(c_gpu, text="PLACA DE VÍDEO", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.lbl_gpu_name = ctk.CTkLabel(c_gpu, text="Carregando...", font=("Consolas", 12), text_color="#000000")
        self.lbl_gpu_name.pack(anchor="w", padx=20)
        
        ctk.CTkLabel(c_gpu, text="Status", font=("Consolas", 11), text_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.prog_gpu = ctk.CTkProgressBar(c_gpu, height=20, corner_radius=0, progress_color="#D50000", fg_color="#E0E0E0", border_width=1, border_color="#000000")
        self.prog_gpu.pack(fill="x", padx=20, pady=(5,20))
        self.prog_gpu.set(1.0) # Fake full for aesthetic

        # Disk Card
        c_disk = self._card(grid)
        c_disk.grid(row=1, column=1, padx=(7,0), pady=(7,0), sticky="nsew")
        ctk.CTkLabel(c_disk, text="ARMAZENAMENTO (C:)", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(10,0))
        self.lbl_disk_name = ctk.CTkLabel(c_disk, text="Carregando...", font=("Consolas", 12), text_color="#000000")
        self.lbl_disk_name.pack(anchor="w", padx=20)
        
        self.lbl_disk_info = ctk.CTkLabel(c_disk, text="Total: 0 GB | Livre: 0 GB", font=("Consolas", 11), text_color="#000000")
        self.lbl_disk_info.pack(anchor="w", padx=20, pady=(10,0))
        self.prog_disk = ctk.CTkProgressBar(c_disk, height=20, corner_radius=0, progress_color="#D50000", fg_color="#E0E0E0", border_width=1, border_color="#000000")
        self.prog_disk.pack(fill="x", padx=20, pady=(5,20))
        self.prog_disk.set(0)

        self.cpu_history = [0]*30
        self.ram_history = [0]*30
        self._hw_loop_running = False

    def _start_hw_loop(self):
        if not getattr(self, "_hw_loop_running", False):
            self._hw_loop_running = True
            import threading
            threading.Thread(target=self._hw_loop, daemon=True).start()

    def _hw_loop(self):
        import time, psutil
        from gear.hardware_reader import get_all_hardware
        # Pega os dados fixos
        hw = get_all_hardware()
        cpu_name = hw.get("CPU", "Desconhecido")
        ram_total = hw.get("RAM", "0 GB")
        gpu_name = hw.get("GPU", "Desconhecido")
        disks = hw.get("Disks", [])
        
        self.after(0, lambda: self.lbl_cpu_name.configure(text=cpu_name))
        self.after(0, lambda: self.lbl_ram_name.configure(text=ram_total))
        self.after(0, lambda: self.lbl_gpu_name.configure(text=gpu_name))
        
        if disks:
            c_disk = next((d for d in disks if 'C:' in d['device']), disks[0])
            pct = c_disk["percent"] / 100.0
            info = f"Total: {c_disk['total']:.1f} GB | Livre: {c_disk['free']:.1f} GB"
            self.after(0, lambda: self.lbl_disk_name.configure(text=f"{c_disk['device']}"))
            self.after(0, lambda: self.lbl_disk_info.configure(text=info))
            self.after(0, lambda: self.prog_disk.set(pct))
        
        while getattr(self, "_hw_loop_running", False):
            try:
                c = psutil.cpu_percent(interval=None)
                r = psutil.virtual_memory().percent
                self.cpu_history.append(c)
                self.cpu_history.pop(0)
                self.ram_history.append(r)
                self.ram_history.pop(0)
                
                self.after(0, self._draw_graphs)
            except:
                pass
            time.sleep(1)

    def _draw_graphs(self):
        try:
            # Desenha CPU
            self.cvs_cpu.delete("all")
            w = self.cvs_cpu.winfo_width()
            h = self.cvs_cpu.winfo_height()
            if w > 10 and h > 10:
                self.cvs_cpu.create_line(0, h/2, w, h/2, fill="#E0E0E0", dash=(2,2))
                pts = []
                dx = w / 29
                for i, val in enumerate(self.cpu_history):
                    x = i * dx
                    y = h - (val / 100.0 * h)
                    pts.extend([x, y])
                if len(pts) >= 4:
                    self.cvs_cpu.create_line(pts, fill="#000000", width=2)
                    poly_pts = [0, h] + pts + [w, h]
                    self.cvs_cpu.create_polygon(poly_pts, fill="#D50000", stipple="gray25", outline="")
                self.cvs_cpu.create_text(w-5, 5, text=f"{self.cpu_history[-1]:.0f}%", anchor="ne", font=("Consolas", 10), fill="#000000")

            # Desenha RAM
            self.cvs_ram.delete("all")
            w = self.cvs_ram.winfo_width()
            h = self.cvs_ram.winfo_height()
            if w > 10 and h > 10:
                dx = w / 30
                for i, val in enumerate(self.ram_history):
                    x0 = i * dx + 1
                    x1 = x0 + dx - 2
                    y0 = h - (val / 100.0 * h)
                    y1 = h
                    if val > 80: color = "#D50000"
                    elif val > 50: color = "#000000"
                    else: color = "#A0A0A0"
                    self.cvs_ram.create_rectangle(x0, y0, x1, y1, fill=color, outline="")
                self.cvs_ram.create_text(w-5, 5, text=f"{self.ram_history[-1]:.0f}%", anchor="ne", font=("Consolas", 10), fill="#000000")
        except Exception:
            pass

    def _build_operations(self, view):
        header = ctk.CTkFrame(view, fg_color="transparent")
        header.pack(fill="x", pady=(0, 18))
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
        ctk.CTkLabel(cc, text="LIMPEZA DE SISTEMA", font=("Helvetica", 14, "bold"), text_color="#000000").pack(anchor="w", padx=20, pady=(20,14))

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
        ctk.CTkLabel(hc,text="HOSTNAME",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(14,6))
        self.hostname_entry = ctk.CTkEntry(hc,placeholder_text="NOME-PC",height=32,corner_radius=0,border_width=1,border_color="#000000",fg_color="#FFFFFF",text_color="#000000",font=("Consolas", 12))
        self.hostname_entry.pack(fill="x",padx=14,pady=(0,6))
        ctk.CTkButton(hc,text="RENOMEAR",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",text_color="#FFFFFF",hover_color="#333333",font=("Helvetica", 11, "bold"),command=self._set_hostname).pack(fill="x",padx=14,pady=(0,14))

        # Report card
        rc = self._card(ug); rc.grid(row=0,column=1,padx=5,sticky="nsew")
        ctk.CTkLabel(rc,text="RELATÓRIO",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(14,6))
        ctk.CTkLabel(rc,text="Exportar specs\\npara a Área de Trabalho",font=("Consolas", 11),text_color="#000000",justify="left").pack(anchor="w",padx=14,pady=(0,6))
        ctk.CTkButton(rc,text="GERAR TXT",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",text_color="#FFFFFF",hover_color="#333333",font=("Helvetica", 11, "bold"),command=self._gen_report).pack(fill="x",padx=14,pady=(0,14))

        # WinUpdate card
        wu = self._card(ug); wu.grid(row=0,column=2,padx=5,sticky="nsew")
        ctk.CTkLabel(wu,text="WINDOWS UPDATE",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(14,6))
        ctk.CTkLabel(wu,text="Forçar checagem\\ne instalação",font=("Consolas", 11),text_color="#000000",justify="left").pack(anchor="w",padx=14,pady=(0,6))
        self.btn_wupd = ctk.CTkButton(wu,text="ATUALIZAR",height=30,corner_radius=0,border_width=1,border_color="#000000",fg_color="#000000",hover_color="#333333",text_color="#FFFFFF",font=("Helvetica", 11, "bold"),command=self._run_wupdate)
        self.btn_wupd.pack(fill="x",padx=14,pady=(0,14))

        # Power card
        pc = self._card(ug); pc.grid(row=0,column=3,padx=(5,0),sticky="nsew")
        ctk.CTkLabel(pc,text="ENERGIA",font=("Helvetica", 13, "bold"),text_color="#000000").pack(anchor="w",padx=14,pady=(14,6))
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
        from gear.hardware_reader import get_temp_size_gb, get_windows_old_size_gb
        from gear.power_config import get_current_plan
        from gear.system_info import get_current_hostname
        
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
        from gear.office_deploy import get_office_info
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

'''

new_content = content[:start_idx] + new_code + "\n" + content[end_idx:]

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.write(new_content)
