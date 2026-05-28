import os
import sys

# FIX APP_WINDOW CARDS
with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('grid.grid_rowconfigure((0,1), weight=1, uniform="dash")',
                          'grid.grid_rowconfigure((0,1), weight=0)\n        grid.grid_rowconfigure(2, weight=1)')
content = content.replace('cvs = ctk.CTkCanvas(card, bg="#FFFFFF", highlightthickness=0)',
                          'cvs = ctk.CTkCanvas(card, bg="#FFFFFF", highlightthickness=0, height=130)')
content = content.replace('txt = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 11), text_color="#000000", justify="left")',
                          'txt = ctk.CTkLabel(card, text="Carregando...", font=("Consolas", 11), text_color="#000000", justify="left", height=130)')

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.write(content)

# FIX MAIN.PY DELAY
with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

preload_code = '''    # Pre-load heavy modules in background to make splash screen transition instant
    import threading
    def preload():
        import customtkinter
        from gui.app_window import AppWindow
        from gear.updater import check_for_updates
    threading.Thread(target=preload, daemon=True).start()

    def _launch_main():'''

main_content = main_content.replace('    def _launch_main():', preload_code)

with open('main.py', 'w', encoding='utf-8') as f:
    f.write(main_content)
