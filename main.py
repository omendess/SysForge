import sys
import os
import ctypes

try:
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        old_exe = exe_path + ".old"
        if os.path.exists(old_exe):
            os.remove(old_exe)
except Exception:
    pass
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == "__main__":
    # The current working directory might change during elevation, so we make sure it's the script dir.
    os.chdir(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)))

    from gui.app_window import AppWindow
    from gear.updater import check_for_updates
    
    app = AppWindow()
    # Chama a verificação silenciosa de atualizações após 1.5 segundos
    app.after(1500, lambda: check_for_updates(app))
    
    app.mainloop()
