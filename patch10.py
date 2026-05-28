import os

with open('gear/software_installer.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_code = '''    try:
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, check=True, timeout=300)
        if status_callback:'''

new_code = '''    try:
        from gear.window_enforcer import enforce_window_rules
        p = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)
        enforce_window_rules(p.pid, duration=300)
        p.wait(timeout=300)
        if p.returncode != 0:
            raise subprocess.CalledProcessError(p.returncode, cmd)
            
        if status_callback:'''

content = content.replace(old_code, new_code)

with open('gear/software_installer.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('gear/office_deploy.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_off = '''            subprocess.run([setup_exe, "/configure", config_xml], cwd=office_dir, creationflags=CREATE_NO_WINDOW, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:'''

new_off = '''            from gear.window_enforcer import enforce_window_rules
            p = subprocess.Popen([setup_exe, "/configure", config_xml], cwd=office_dir, creationflags=CREATE_NO_WINDOW, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            enforce_window_rules(p.pid, duration=1800) # Office can take a while
            p.wait()
            if p.returncode != 0:
                raise subprocess.CalledProcessError(p.returncode, "setup.exe")
        except subprocess.CalledProcessError as e:'''

content = content.replace(old_off, new_off)

with open('gear/office_deploy.py', 'w', encoding='utf-8') as f:
    f.write(content)
