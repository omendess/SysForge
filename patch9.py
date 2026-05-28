import os

with open('gear/software_installer.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_winget = '''                cmd = ["winget", "install", "--id", pkg_id, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements"]
                subprocess.run(cmd, creationflags=0x08000000, check=True)'''
new_winget = '''                cmd = ["winget", "install", "--id", pkg_id, "--exact", "--silent", "--accept-package-agreements", "--accept-source-agreements"]
                from gear.window_enforcer import enforce_window_rules
                p = subprocess.Popen(cmd, creationflags=0x08000000)
                enforce_window_rules(p.pid, duration=300)
                p.wait()'''

content = content.replace(old_winget, new_winget)

with open('gear/software_installer.py', 'w', encoding='utf-8') as f:
    f.write(content)
