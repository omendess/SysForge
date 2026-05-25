import subprocess
import os
import ctypes
import sys

CREATE_NO_WINDOW = 0x08000000

def set_wallpaper(image_path, cb=None):
    """Define o papel de parede a partir de um caminho de imagem."""
    if not image_path or not os.path.exists(image_path):
        if cb: cb("⚠️ Arquivo de imagem não encontrado.")
        return False
    
    try:
        abs_path = os.path.abspath(image_path)
        
        # Usa SystemParametersInfoW para mudar o wallpaper
        SPI_SETDESKWALLPAPER = 0x0014
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02
        
        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, abs_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        
        if result:
            if cb: cb(f"✅ Papel de parede definido: {os.path.basename(abs_path)}")
            return True
        else:
            if cb: cb("⚠️ Falha ao definir papel de parede.")
            return False
    except Exception as e:
        if cb: cb(f"❌ Erro: {e}")
        return False

def find_wallpapers_on_pendrive():
    """Busca imagens na pasta Wallpapers dentro do diretório do app."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Busca via PyInstaller
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    
    wall_dir = os.path.join(base, "Wallpapers")
    
    if not os.path.exists(wall_dir):
        return []
    
    valid_ext = ('.jpg', '.jpeg', '.png', '.bmp')
    images = []
    for f in os.listdir(wall_dir):
        if f.lower().endswith(valid_ext):
            images.append(os.path.join(wall_dir, f))
    
    return sorted(images)
