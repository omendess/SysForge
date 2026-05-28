import ctypes
from ctypes import wintypes
import psutil
import time
import threading

def enforce_window_rules(parent_pid, duration=10):

    user32 = ctypes.windll.user32
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    
    # Cache screen size
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)

    def _monitor():
        end_time = time.time() + duration
        processed_hwnds = set()
        
        while time.time() < end_time:
            try:
                parent = psutil.Process(parent_pid)
                pids = [parent_pid] + [c.pid for c in parent.children(recursive=True)]
            except psutil.NoSuchProcess:
                break # Processo principal já morreu
                
            def callback(hwnd, lParam):
                found_pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
                
                if found_pid.value in pids and hwnd not in processed_hwnds and user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        rect = wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        w = rect.right - rect.left
                        h = rect.bottom - rect.top
                        
                        # Ignorar janelas minúsculas invisíveis
                        if w > 100 and h > 100:
                            x = (screen_w - w) // 2
                            y = (screen_h - h) // 2
                            
                            # HWND_TOPMOST = -1, SWP_SHOWWINDOW = 0x0040
                            user32.SetWindowPos(hwnd, -1, x, y, w, h, 0x0040)
                            processed_hwnds.add(hwnd)
                return True
                
            try:
                user32.EnumWindows(WNDENUMPROC(callback), 0)
            except:
                pass
                
            time.sleep(0.5)

    threading.Thread(target=_monitor, daemon=True).start()

