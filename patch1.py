import os

with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_dashboard = False
in_init = False
in_sidebar = False
in_build_views = False

for i, line in enumerate(lines):
    if 'def __init__(self):' in line:
        in_init = True
    elif in_init and 'w, h = ' in line:
        new_lines.append('        w, h = 1280, 720\n')
        new_lines.append('        self.resizable(False, False)\n')
        continue
    elif in_init and 'self.minsize' in line:
        continue
    
    if 'items = [("DASHBOARD","dashboard",3)' in line:
        new_lines.append('        items = [("DASHBOARD","dashboard",3),("OPERAÇÕES","operations",4),("SOFTWARES","softwares",5),("TWEAKS","tweaks",6),("APP MANAGER","app_manager",7),("STARTUP","startup",8),("REPARO & SCANNER","repair",9),("LOGS","logs",10),("INFO", "info", 11)]\n')
        continue
        
    if 'self.views = {}' in line:
        new_lines.append(line)
        new_lines.append('        for key, builder in [("dashboard",self._build_dashboard),("operations",self._build_operations),("softwares",self._build_softwares),("tweaks",self._build_tweaks),("app_manager",self._build_app_manager),("startup",self._build_startup),("repair",self._build_repair),("logs",self._build_logs),("info",self._build_info)]:\n')
        continue
    if 'for key, builder in [("dashboard",self._build_dashboard),' in line:
        continue
        
    if 'elif name == "app_manager":' in line:
        new_lines.append('        elif name == "dashboard":\n')
        new_lines.append('            self._start_hw_loop()\n')
        new_lines.append('        elif name == "operations":\n')
        new_lines.append('            threading.Thread(target=self._load_operations, daemon=True).start()\n')
        new_lines.append(line)
        continue
    if 'if name == "dashboard":' in line:
        # Ignore old block
        pass
    if 'threading.Thread(target=self._load_hw, daemon=True).start()' in line:
        continue
        
    new_lines.append(line)

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
