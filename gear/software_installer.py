import subprocess
import os

CREATE_NO_WINDOW = 0x08000000

SOFTWARE_DICT = {
    "Navegadores": {
        "Google Chrome": "Google.Chrome",
        "Opera": "Opera.Opera",
        "Opera GX": "Opera.OperaGX",
        "Brave": "Brave.Brave"
    },
    "Comunicação": {
        "WhatsApp": "WhatsApp.WhatsApp",
        "Telegram": "Telegram.TelegramDesktop",
        "Discord": "Discord.Discord",
        "Zoom": "Zoom.Zoom"
    },
    "Utilitários": {
        "WinRAR": "RARLab.WinRAR",
        "AnyDesk": "AnyDeskSoftwareGmbH.AnyDesk",
        "PowerToys": "Microsoft.PowerToys",
        "Notepad++": "Notepad++.Notepad++",
        "qBittorrent": "qBittorrent.qBittorrent"
    },
    "Desenvolvimento": {
        "Visual Studio Code": "Microsoft.VisualStudioCode",
        "Node.js": "OpenJS.NodeJS",
        "Python 3.12": "Python.Python.3.12",
        "Git": "Git.Git",
        "Docker Desktop": "Docker.DockerDesktop",
        "DBeaver": "dbeaver.dbeaver",
        "Postman": "Postman.Postman"
    },
    "Design / Mídia": {
        "K-Lite Codec Pack": "CodecGuide.K-LiteCodecPack.Standard",
        "VLC": "VideoLAN.VLC",
        "OBS Studio": "OBSProject.OBSStudio",
        "Figma": "Figma.Figma",
        "ShareX": "ShareX.ShareX"
    }
}

# Perfis de implantação pré-definidos
PROFILES = {
    "🏢 PC Escritório": [
        "Google.Chrome", "WhatsApp.WhatsApp", "RARLab.WinRAR",
        "AnyDeskSoftwareGmbH.AnyDesk", "VideoLAN.VLC",
        "CodecGuide.K-LiteCodecPack.Standard"
    ],
    "🎮 PC Gamer": [
        "Google.Chrome", "Discord.Discord", "Opera.OperaGX",
        "RARLab.WinRAR", "VideoLAN.VLC", "OBSProject.OBSStudio",
        "qBittorrent.qBittorrent", "ShareX.ShareX",
        "CodecGuide.K-LiteCodecPack.Standard"
    ],
    "💻 PC Dev": [
        "Google.Chrome", "Microsoft.VisualStudioCode", "OpenJS.NodeJS",
        "Python.Python.3.12", "Git.Git", "Docker.DockerDesktop",
        "dbeaver.dbeaver", "Postman.Postman", "Discord.Discord",
        "Notepad++.Notepad++", "RARLab.WinRAR", "ShareX.ShareX"
    ],
}

def install_software(winget_id, status_callback=None):
    if status_callback:
        # Busca o nome amigável
        friendly = winget_id
        for cat in SOFTWARE_DICT.values():
            for name, wid in cat.items():
                if wid == winget_id:
                    friendly = name
                    break
        status_callback(f"📦 Instalando {friendly}...")
    
    cmd = [
        "winget", "install", "-e", "--id", winget_id, 
        "--accept-source-agreements", "--accept-package-agreements",
        "--silent"
    ]
    try:
        subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, check=True, timeout=300)
        if status_callback:
            status_callback(f"✅ {winget_id} instalado com sucesso.")
    except subprocess.TimeoutExpired:
        if status_callback:
            status_callback(f"⏱️ Timeout ao instalar {winget_id}.")
    except subprocess.CalledProcessError:
        if status_callback:
            status_callback(f"⚠️ Falha ao instalar {winget_id}.")
