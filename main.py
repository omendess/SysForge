import sys
import os

try:
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        old_exe = exe_path + ".old"
        if os.path.exists(old_exe):
            os.remove(old_exe)
except Exception:
    pass

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--update-mode":
        from gear.updater import execute_update_mode
        execute_update_mode(sys.argv[2], sys.argv[3])
        sys.exit(0)

    # The current working directory might change during elevation, so we make sure it's the script dir.
    os.chdir(os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__)))

    import customtkinter
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
