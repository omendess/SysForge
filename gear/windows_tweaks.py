import subprocess
import time
import winreg
import ctypes
import os

CREATE_NO_WINDOW = 0x08000000

# ═══════════════════════════════════════════════════════════
#  MOTOR NATIVO DE REGISTRO (IDEMPOTÊNCIA)
# ═══════════════════════════════════════════════════════════

def _get_hive(hive_str):
    if hive_str.startswith("HKLM"): return winreg.HKEY_LOCAL_MACHINE
    if hive_str.startswith("HKCU"): return winreg.HKEY_CURRENT_USER
    return winreg.HKEY_CURRENT_USER

def verificar_estado_registro(hive_str, path, key, expected_value, value_type=winreg.REG_DWORD):
    """
    Lê o registro usando a API do Windows.
    Retorna True se o valor atual já for igual ao esperado.
    """
    hive = _get_hive(hive_str)
    try:
        with winreg.OpenKey(hive, path, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            current_val, _ = winreg.QueryValueEx(k, key)
        
        if value_type == winreg.REG_DWORD and isinstance(expected_value, str):
            exp_val = int(expected_value)
        else:
            exp_val = expected_value

        return current_val == exp_val
    except OSError:
        return False

def aplicar_registro_nativo(hive_str, path, key, value, value_type=winreg.REG_DWORD):
    """Aplica o tweak no registro sem chamar processos externos."""
    hive = _get_hive(hive_str)
    try:
        if value_type == winreg.REG_DWORD and isinstance(value, str):
            value = int(value)
            
        with winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k:
            winreg.SetValueEx(k, key, 0, value_type, value)
        return True
    except Exception:
        return False

def deletar_chave_nativa(hive_str, path):
    hive = _get_hive(hive_str)
    try:
        winreg.DeleteKeyEx(hive, path, winreg.KEY_WOW64_64KEY, 0)
        return True
    except OSError:
        try:
            winreg.DeleteKey(hive, path)
            return True
        except OSError:
            return False

def processar_tweak(hive_str, path, key, value, value_type, desc):
    """Gerencia a idempotência."""
    if verificar_estado_registro(hive_str, path, key, value, value_type):
        return f"⏭️ SKIP - Já Otimizado: {desc}"
    else:
        if aplicar_registro_nativo(hive_str, path, key, value, value_type):
            return f"✅ APLICADO: {desc}"
        else:
            return f"❌ ERRO: {desc}"

# ═══════════════════════════════════════════════════════════
#  TWEAKS ESPECÍFICOS (YIELDING STRINGS)
# ═══════════════════════════════════════════════════════════

def toggle_telemetry(enable):
    val = 0 if enable else 3
    desc = "Telemetria Desativada" if enable else "Telemetria Ativada"
    yield processar_tweak("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", val, winreg.REG_DWORD, desc)

    # Desativação dos serviços via registro nativo (Start=4 é disabled, Start=2 é Auto)
    svc_val = 4 if enable else 2
    yield processar_tweak("HKLM", r"SYSTEM\CurrentControlSet\Services\DiagTrack", "Start", svc_val, winreg.REG_DWORD, "Serviço DiagTrack")
    yield processar_tweak("HKLM", r"SYSTEM\CurrentControlSet\Services\dmwappushservice", "Start", svc_val, winreg.REG_DWORD, "Serviço dmwappushservice")


def toggle_hidden_extensions(enable):
    base = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    ext_val = 0 if enable else 1
    hid_val = 1 if enable else 2
    sup_val = 1 if enable else 0
    yield processar_tweak("HKCU", base, "HideFileExt", ext_val, winreg.REG_DWORD, "Extensões Visíveis" if enable else "Extensões Ocultas")
    yield processar_tweak("HKCU", base, "Hidden", hid_val, winreg.REG_DWORD, "Arquivos Ocultos")
    yield processar_tweak("HKCU", base, "ShowSuperHidden", sup_val, winreg.REG_DWORD, "Arquivos Protegidos")


def toggle_bing_search(enable):
    val1 = 1 if enable else 0
    val0 = 0 if enable else 1
    yield processar_tweak("HKCU", r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", val1, winreg.REG_DWORD, "Sugestões do Bing")
    yield processar_tweak("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "BingSearchEnabled", val0, winreg.REG_DWORD, "Bing Search")
    yield processar_tweak("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Search", "CortanaConsent", val0, winreg.REG_DWORD, "Cortana")


def toggle_dark_mode(enable):
    val = 0 if enable else 1
    desc = "Modo Escuro" if enable else "Modo Claro"
    yield processar_tweak("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", val, winreg.REG_DWORD, f"{desc} (Apps)")
    yield processar_tweak("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "SystemUsesLightTheme", val, winreg.REG_DWORD, f"{desc} (Sistema)")


def toggle_classic_context_menu(enable):
    clsid_path = r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
    if enable:
        if verificar_estado_registro("HKCU", clsid_path, "", "", winreg.REG_SZ):
            yield "⏭️ SKIP - Já Otimizado: Menu de Contexto Clássico"
        else:
            winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, clsid_path, 0, winreg.KEY_SET_VALUE)
            aplicar_registro_nativo("HKCU", clsid_path, "", "", winreg.REG_SZ)
            yield "✅ APLICADO: Menu de Contexto Clássico"
    else:
        if deletar_chave_nativa("HKCU", clsid_path):
            yield "✅ APLICADO: Menu de Contexto Moderno (Win 11)"
        else:
            yield "⏭️ SKIP - Já Otimizado: Menu de Contexto Moderno"


def toggle_hibernation(enable):
    action = "off" if enable else "on"
    desc = "Hibernação desativada" if enable else "Hibernação ativada"
    
    # Tentativa de checagem heurística via presença do hiberfil.sys
    hiberfil = "C:\\hiberfil.sys"
    if enable and not os.path.exists(hiberfil):
        yield f"⏭️ SKIP - Já Otimizado: {desc}"
        return
    elif not enable and os.path.exists(hiberfil):
        yield f"⏭️ SKIP - Já Otimizado: {desc}"
        return

    try:
        subprocess.run(["powercfg.exe", "/hibernate", action], creationflags=CREATE_NO_WINDOW, capture_output=True)
        yield f"✅ APLICADO: {desc}"
    except Exception as e:
        yield f"❌ ERRO: {desc} - {str(e)}"


def toggle_lock_screen(enable):
    val = 1 if enable else 0
    yield processar_tweak("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen", val, winreg.REG_DWORD, "Tela de Bloqueio")


def toggle_sticky_keys(enable):
    val = "506" if enable else "510"
    yield processar_tweak("HKCU", r"Control Panel\Accessibility\StickyKeys", "Flags", val, winreg.REG_SZ, "Teclas de Aderência")


def toggle_taskbar_chat(enable):
    val = 0 if enable else 1
    yield processar_tweak("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", val, winreg.REG_DWORD, "Chat na Barra de Tarefas")


def toggle_fast_dns(enable):
    desc = "DNS Cloudflare" if enable else "DNS DHCP"
    try:
        cmd_if = ["powershell", "-NoProfile", "-Command", "(Get-NetAdapter | Where-Object Status -eq 'Up')[0].Name"]
        res = subprocess.run(cmd_if, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True)
        iface = res.stdout.strip()
        if iface:
            if enable:
                subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", f'name="{iface}"', "static", "1.1.1.1", "primary"], creationflags=CREATE_NO_WINDOW)
                subprocess.run(["netsh", "interface", "ipv4", "add", "dnsservers", f'name="{iface}"', "1.0.0.1", "index=2"], creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.run(["netsh", "interface", "ipv4", "set", "dnsservers", f'name="{iface}"', "dhcp"], creationflags=CREATE_NO_WINDOW)
            subprocess.run(["ipconfig", "/flushdns"], creationflags=CREATE_NO_WINDOW)
            yield f"✅ APLICADO: {desc}"
        else:
            yield "⚠️ SKIP: Nenhuma interface de rede ativa"
    except Exception as e:
        yield f"❌ ERRO: DNS - {str(e)}"


def toggle_dev_sanctuary(enable):
    # Opções de pasta avançadas
    val = 1 if enable else 0
    yield processar_tweak("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", val, winreg.REG_DWORD, "Processos Isolados de Pasta" if enable else "Processo Único de Pasta")
    
    recent = 0 if enable else 1
    yield processar_tweak("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer", "ShowRecent", recent, winreg.REG_DWORD, "Ocultar Histórico Recente" if enable else "Mostrar Histórico Recente")
    yield processar_tweak("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer", "ShowFrequent", recent, winreg.REG_DWORD, "Ocultar Acesso Frequente" if enable else "Mostrar Acesso Frequente")
    
    if enable:
        yield "⏳ Instalando WSL (Windows Subsystem for Linux)... (pode demorar)"
        try:
            subprocess.run(["dism.exe", "/online", "/enable-feature", "/featurename:Microsoft-Windows-Subsystem-Linux", "/all", "/norestart"], creationflags=CREATE_NO_WINDOW, check=True)
            yield "✅ APLICADO: WSL Habilitado."
        except Exception as e:
            yield f"❌ ERRO: WSL - {str(e)}"
            
        yield "⏳ Instalando OpenSSH Client..."
        try:
            subprocess.run(["dism.exe", "/online", "/Add-Capability", "/CapabilityName:OpenSSH.Client~~~~0.0.1.0"], creationflags=CREATE_NO_WINDOW)
            yield "✅ APLICADO: OpenSSH Client Instalado."
        except Exception as e:
            yield f"❌ ERRO: OpenSSH - {str(e)}"


def toggle_qol_matrix(enable):
    # Mouse Acceleration
    ms = "0" if enable else "1"
    yield processar_tweak("HKCU", r"Control Panel\Mouse", "MouseSpeed", ms, winreg.REG_SZ, "Aceleração do Mouse Desativada" if enable else "Aceleração do Mouse Ativada")
    
    # Taskbar Alignment (0 = Left, 1 = Center)
    tb = 0 if enable else 1
    yield processar_tweak("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl", tb, winreg.REG_DWORD, "Menu Iniciar à Esquerda" if enable else "Menu Iniciar Centralizado")
    
    # Energia e Suspensão
    if enable:
        yield "⏳ Aplicando Plano de Energia (Desempenho Máximo)..."
        try:
            # Tenta duplicar e ativar o ultimate performance
            res = subprocess.run(["powercfg", "-duplicatescheme", "e9a42b02-d5df-448d-aa00-03f14749eb61"], capture_output=True, text=True, creationflags=CREATE_NO_WINDOW)
            import re
            match = re.search(r"GUID do Esquema de Energia: ([\w-]+)", res.stdout)
            if match:
                guid = match.group(1)
                subprocess.run(["powercfg", "-setactive", guid], creationflags=CREATE_NO_WINDOW)
                yield "✅ APLICADO: Desempenho Máximo"
        except:
            pass
            
        # Desativar senha ao voltar da suspensão
        try:
            subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_NONE", "CONSOLELOCK", "0"], creationflags=CREATE_NO_WINDOW)
            subprocess.run(["powercfg", "/setdcvalueindex", "SCHEME_CURRENT", "SUB_NONE", "CONSOLELOCK", "0"], creationflags=CREATE_NO_WINDOW)
            subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], creationflags=CREATE_NO_WINDOW)
            yield "✅ APLICADO: Sem Senha na Suspensão"
        except:
            pass

#  DISPATCHER PRINCIPAL
# ═══════════════════════════════════════════════════════════

TWEAKS_MAP = {
    "disable_telemetry":        ("Telemetria",                 toggle_telemetry),
    "show_hidden_extensions":   ("Extensões e Itens Ocultos",  toggle_hidden_extensions),
    "disable_bing_search":      ("Pesquisa Bing",              toggle_bing_search),
    "enable_dark_mode":         ("Modo Escuro",                toggle_dark_mode),
    "classic_context_menu":     ("Menu de Contexto Clássico",  toggle_classic_context_menu),
    "disable_hibernation":      ("Desativar Hibernação",       toggle_hibernation),
    "disable_lock_screen":      ("Desativar Tela de Bloqueio", toggle_lock_screen),
    "disable_sticky_keys":      ("Desativar Teclas de Aderência", toggle_sticky_keys),
    "hide_taskbar_chat":        ("Ocultar Chat na Barra",      toggle_taskbar_chat),
    "optimize_dns":             ("Otimizar DNS (Cloudflare)",  toggle_fast_dns),
    "dev_sanctuary":            ("Santuário do Desenvolvedor", toggle_dev_sanctuary),
    "qol_matrix":               ("Matriz QoL (Desempenho)",    toggle_qol_matrix),
}

def apply_selected_tweaks(tasks_dict, status_callback=None):
    """Aplica os tweaks usando yield para logar em RAM rapidamente."""
    total = len(tasks_dict)
    needs_explorer_restart = False
    
    for i, (key, is_on) in enumerate(tasks_dict.items(), 1):
        if key in TWEAKS_MAP:
            name, func = TWEAKS_MAP[key]
            
            # Consome o generator e relata
            for result_msg in func(is_on):
                if status_callback:
                    status_callback(result_msg)
            
            if key in ("show_hidden_extensions", "enable_dark_mode", "classic_context_menu",
                       "hide_taskbar_chat"):
                needs_explorer_restart = True
                
    if needs_explorer_restart:
        if status_callback:
            status_callback("🔄 Atualizando ambiente do Windows nativamente...")
        
        # Broadcast de WM_SETTINGCHANGE usando ctypes (Native WinAPI)
        # 0xFFFF = HWND_BROADCAST, 0x001A = WM_SETTINGCHANGE
        ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001A, 0, "Environment", 2, 500, None)
    
    if status_callback:
        status_callback("✅ Todos os tweaks foram processados na memória!")


def get_current_tweak_states():
    """Verifica no registro se os tweaks já estão ativados para inicializar o GUI."""
    def _classic_menu_active():
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32",
                               0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY):
                return True
        except OSError:
            return False

    states = {
        "disable_telemetry":      verificar_estado_registro("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0),
        "show_hidden_extensions": verificar_estado_registro("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 0),
        "disable_bing_search":    verificar_estado_registro("HKCU", r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", 1),
        "enable_dark_mode":       verificar_estado_registro("HKCU", r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 0),
        "classic_context_menu":   _classic_menu_active(),
        "disable_hibernation":    not os.path.exists("C:\\hiberfil.sys"),
        "disable_lock_screen":    verificar_estado_registro("HKLM", r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen", 1),
        "disable_sticky_keys":    verificar_estado_registro("HKCU", r"Control Panel\Accessibility\StickyKeys", "Flags", "506", winreg.REG_SZ),
        "hide_taskbar_chat":      verificar_estado_registro("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", 0),
        "optimize_dns":           False,
        "dev_sanctuary":          verificar_estado_registro("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "SeparateProcess", 1),
        "qol_matrix":             verificar_estado_registro("HKCU", r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarAl", 0),
    }
    return states
