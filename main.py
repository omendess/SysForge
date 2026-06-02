import sys
if sys.stdout is None:
    class Dummy:
        def write(self, *a):
            pass
        def flush(self):
            pass
    sys.stdout = Dummy()
    sys.stderr = Dummy()
import os

try:
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        import glob
        for old_file in glob.glob(os.path.join(exe_dir, "*.old")):
            try:
                os.remove(old_file)
            except Exception:
                pass
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
    from gear.blackbox import run_blackbox_audit
    
    # Executa a auditoria forense silenciosa antes de qualquer GUI
    run_blackbox_audit()
    
    from gui.app_window import AppWindow
    from gui.splash_screen import SplashScreen
    from gear.updater import check_for_updates

    # Constrói o aplicativo pesado primeiro, mas mantém invisível
    app = AppWindow()
    app.withdraw()

    def _launch_main():
        """Chamado pela SplashScreen quando a animação termina."""
        app.deiconify()
        app.after(2000, lambda: check_for_updates(app))

    # A Splash roda por cima do app invisível
    SplashScreen(app, _launch_main)
    app.mainloop()
