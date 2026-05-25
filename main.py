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
    if not is_admin():
        # Re-run the program with admin rights
        # We need to elevate privileges to run winget, access Windows.old, and install office.
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    # The current working directory might change during elevation, so we make sure it's the script dir.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    from gui.app_window import AppWindow
    from gear.updater import check_for_updates
    
    app = AppWindow()
    # Chama a verificação silenciosa de atualizações após 1.5 segundos
    app.after(1500, lambda: check_for_updates(app))
    
    app.mainloop()
