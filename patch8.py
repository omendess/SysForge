import os

with open('gear/app_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_run = "        subprocess.run(uninstall_string, creationflags=CREATE_NO_WINDOW, check=False, shell=True)"
new_run = '''        from gear.window_enforcer import enforce_window_rules
        p = subprocess.Popen(uninstall_string, creationflags=CREATE_NO_WINDOW, shell=True)
        enforce_window_rules(p.pid, duration=120)
        p.wait()'''

content = content.replace(old_run, new_run)

with open('gear/app_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
