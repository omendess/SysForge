import os

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if "import tkinter as tk" in line:
        skip = True
        new_lines.append('''    import customtkinter
    from gui.app_window import AppWindow
    from gui.splash_screen import SplashScreen
    from gear.updater import check_for_updates

    # Constrói o aplicativo pesado primeiro, mas mantém invisível
    app = AppWindow()
    app.withdraw()

    def _launch_main():
        """Chamado pela SplashScreen quando o vídeo termina."""
        app.deiconify()
        app.after(1500, lambda: check_for_updates(app))

    # A Splash roda por cima do app invisível
    SplashScreen(app, _launch_main)
    app.mainloop()
''')
    if not skip:
        new_lines.append(line)

with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
