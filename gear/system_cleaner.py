import os
import subprocess
import shutil

CREATE_NO_WINDOW = 0x08000000

def get_folder_size(folder_path):
    total_size = 0
    if not os.path.exists(folder_path):
        return 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except OSError:
                    pass
    return total_size

def get_temp_size_gb():
    user_temp = os.environ.get('TEMP', '')
    win_temp = 'C:\\Windows\\Temp'
    size = get_folder_size(user_temp) + get_folder_size(win_temp)
    return size / (1024**3)

def get_windows_old_size_gb():
    win_old = 'C:\\Windows.old'
    size = get_folder_size(win_old)
    return size / (1024**3)

def clean_temp_folders():
    user_temp = os.environ.get('TEMP', '')
    win_temp = 'C:\\Windows\\Temp'
    
    for folder in [user_temp, win_temp]:
        if not folder or not os.path.exists(folder):
            continue
        for item in os.listdir(folder):
            item_path = os.path.join(folder, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
            except Exception:
                pass

def remove_windows_old():
    win_old = 'C:\\Windows.old'
    if os.path.exists(win_old):
        try:
            # takeown /F C:\Windows.old /A /R /D Y
            subprocess.run(["takeown", "/F", win_old, "/A", "/R", "/D", "Y"], creationflags=CREATE_NO_WINDOW, check=False)
            # icacls C:\Windows.old /grant *S-1-5-32-544:F /T /C /Q (Using SID for Administrators to avoid locale issues)
            subprocess.run(["icacls", win_old, "/grant", "*S-1-5-32-544:F", "/T", "/C", "/Q"], creationflags=CREATE_NO_WINDOW, check=False)
            # rd /s /q C:\Windows.old
            subprocess.run(["cmd.exe", "/c", "rd", "/s", "/q", win_old], creationflags=CREATE_NO_WINDOW, check=False)
        except Exception as e:
            raise RuntimeError(f"Erro ao remover Windows.old: {e}")
