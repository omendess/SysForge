import os
import socket
import datetime
import json
import psutil
import threading

def run_blackbox_audit():
    def _audit():
        try:
            hostname = socket.gethostname()
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
            except Exception:
                local_ip = "127.0.0.1"

            now = datetime.datetime.now().isoformat()
            
            services_count = 0
            try:
                for _ in psutil.win_service_iter():
                    services_count += 1
            except Exception:
                pass
                
            data = {
                "hostname": hostname,
                "local_ip": local_ip,
                "timestamp": now,
                "running_services": services_count
            }
            
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            log_dir = os.path.join(base_dir, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            file_path = os.path.join(log_dir, f"SD-{hostname}-snapshot.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)
            except Exception:
                pass
        except Exception:
            pass

    threading.Thread(target=_audit, daemon=True).start()
