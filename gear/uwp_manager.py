import subprocess
import json
import logging

def listar_uwp():
    """
    Lista os aplicativos UWP instalados no sistema.
    Retorna uma lista de dicionários com 'Name' e 'PackageFullName'.
    """
    try:
        # Usando PowerShell para pegar a lista em formato JSON
        cmd = [
            "powershell", "-NoProfile", "-Command",
            "Get-AppxPackage | Select-Object Name, PackageFullName | ConvertTo-Json -Compress"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode == 0 and result.stdout.strip():
            # Pode retornar dict ou list dependendo da quantidade de pacotes, tratamos isso
            data = json.loads(result.stdout)
            if isinstance(data, dict):
                data = [data]
            return data
        return []
    except Exception as e:
        logging.error(f"Erro ao listar UWP: {e}")
        return []

def remover_uwp(package_full_name):
    """
    Remove um aplicativo UWP específico pelo PackageFullName de forma silenciosa.
    """
    try:
        cmd = [
            "powershell", "-NoProfile", "-Command",
            f"Remove-AppxPackage -Package '{package_full_name}'"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Erro ao remover {package_full_name}: {e}")
        return False

def reparar_reinstalar_uwp(nome_app):
    """
    Repara ou reinstala um aplicativo UWP pelo nome.
    Tratamento especial para GamingServices, limpando chaves corrompidas antes.
    """
    try:
        if 'GamingServices' in nome_app:
            cmds_reg = [
                r'Remove-Item -Path "HKLM:\System\CurrentControlSet\Services\GamingServices" -Recurse -Force -ErrorAction SilentlyContinue',
                r'Remove-Item -Path "HKLM:\System\CurrentControlSet\Services\GamingServicesNet" -Recurse -Force -ErrorAction SilentlyContinue'
            ]
            for cmd_reg in cmds_reg:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", cmd_reg],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
        
        ps_cmd = f'Get-AppxPackage -allusers *{nome_app}* | Foreach {{Add-AppxPackage -DisableDevelopmentMode -Register "$($_.InstallLocation)\\AppXManifest.xml"}}'
        cmd = ["powershell", "-NoProfile", "-Command", ps_cmd]
        result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return result.returncode == 0
    except Exception as e:
        logging.error(f"Erro ao reparar {nome_app}: {e}")
        return False
