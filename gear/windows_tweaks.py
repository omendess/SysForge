import subprocess
import time
import winreg

CREATE_NO_WINDOW = 0x08000000

def run_reg(path, key, value_type, value, status_callback=None, description=""):
    """Executa um comando reg add com feedback."""
    cmd = ["reg", "add", path, "/v", key, "/t", value_type, "/d", str(value), "/f"]
    try:
        result = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            if status_callback and description:
                status_callback(f"✅ {description}")
            return True
        else:
            if status_callback and description:
                status_callback(f"⚠️ {description} — Falha (código {result.returncode})")
            return False
    except Exception as e:
        if status_callback and description:
            status_callback(f"❌ {description} — Erro: {str(e)}")
        return False

def run_sc(action, service, status_callback=None, description=""):
    """Executa um comando sc (config ou stop/start)."""
    if action == "disable":
        cmd = ["sc", "config", service, "start=", "disabled"]
    elif action == "enable":
        cmd = ["sc", "config", service, "start=", "auto"]
    elif action == "stop":
        cmd = ["sc", "stop", service]
    elif action == "start":
        cmd = ["sc", "start", service]
    else:
        return False
    try:
        result = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30)
        if status_callback and description:
            icon = "✅" if result.returncode == 0 else "⚠️"
            status_callback(f"{icon} {description}")
        return result.returncode == 0
    except Exception as e:
        if status_callback and description:
            status_callback(f"❌ {description} — {str(e)}")
        return False

# ═══════════════════════════════════════════════════════════
#  TELEMETRIA
# ═══════════════════════════════════════════════════════════
def toggle_telemetry(enable, cb=None):
    """enable=True → Desativa telemetria. enable=False → Restaura padrão."""
    if enable:
        run_reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry", "REG_DWORD", "0", cb, "Telemetria desativada no Registro")
        time.sleep(0.3)
        run_sc("disable", "DiagTrack", cb, "Serviço DiagTrack desativado")
        run_sc("stop", "DiagTrack", cb, "Serviço DiagTrack parado")
        run_sc("disable", "dmwappushservice", cb, "Serviço dmwappushservice desativado")
        run_sc("stop", "dmwappushservice", cb, "Serviço dmwappushservice parado")
    else:
        run_reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                "AllowTelemetry", "REG_DWORD", "3", cb, "Telemetria restaurada ao padrão")
        time.sleep(0.3)
        run_sc("enable", "DiagTrack", cb, "Serviço DiagTrack reativado")
        run_sc("start", "DiagTrack", cb, "Serviço DiagTrack iniciado")
        run_sc("enable", "dmwappushservice", cb, "Serviço dmwappushservice reativado")
        run_sc("start", "dmwappushservice", cb, "Serviço dmwappushservice iniciado")

# ═══════════════════════════════════════════════════════════
#  EXTENSÕES E ARQUIVOS OCULTOS
# ═══════════════════════════════════════════════════════════
def toggle_hidden_extensions(enable, cb=None):
    """enable=True → Mostra extensões/ocultos. enable=False → Esconde (padrão Windows)."""
    base = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"
    if enable:
        run_reg(base, "HideFileExt", "REG_DWORD", "0", cb, "Extensões de arquivo visíveis")
        run_reg(base, "Hidden", "REG_DWORD", "1", cb, "Arquivos ocultos visíveis")
        run_reg(base, "ShowSuperHidden", "REG_DWORD", "1", cb, "Arquivos protegidos visíveis")
    else:
        run_reg(base, "HideFileExt", "REG_DWORD", "1", cb, "Extensões de arquivo ocultas (padrão)")
        run_reg(base, "Hidden", "REG_DWORD", "2", cb, "Arquivos ocultos escondidos (padrão)")
        run_reg(base, "ShowSuperHidden", "REG_DWORD", "0", cb, "Arquivos protegidos ocultos (padrão)")

# ═══════════════════════════════════════════════════════════
#  PESQUISA BING
# ═══════════════════════════════════════════════════════════
def toggle_bing_search(enable, cb=None):
    """enable=True → Desativa Bing. enable=False → Restaura Bing."""
    if enable:
        run_reg(r"HKCU\Software\Policies\Microsoft\Windows\Explorer",
                "DisableSearchBoxSuggestions", "REG_DWORD", "1", cb, "Sugestões do Bing desativadas")
        run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
                "BingSearchEnabled", "REG_DWORD", "0", cb, "Bing Search desativado")
        run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
                "CortanaConsent", "REG_DWORD", "0", cb, "Cortana desativada")
    else:
        run_reg(r"HKCU\Software\Policies\Microsoft\Windows\Explorer",
                "DisableSearchBoxSuggestions", "REG_DWORD", "0", cb, "Sugestões do Bing reativadas")
        run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
                "BingSearchEnabled", "REG_DWORD", "1", cb, "Bing Search reativado")
        run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Search",
                "CortanaConsent", "REG_DWORD", "1", cb, "Cortana reativada")

# ═══════════════════════════════════════════════════════════
#  MODO ESCURO
# ═══════════════════════════════════════════════════════════
def toggle_dark_mode(enable, cb=None):
    """enable=True → Modo escuro. enable=False → Modo claro (padrão)."""
    val = "0" if enable else "1"
    desc_apps = "Modo escuro nos apps" if enable else "Modo claro nos apps (padrão)"
    desc_sys = "Modo escuro no sistema" if enable else "Modo claro no sistema (padrão)"
    run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            "AppsUseLightTheme", "REG_DWORD", val, cb, desc_apps)
    run_reg(r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            "SystemUsesLightTheme", "REG_DWORD", val, cb, desc_sys)

# ═══════════════════════════════════════════════════════════
#  MENU DE CONTEXTO CLÁSSICO (Win 11 → Win 10)
# ═══════════════════════════════════════════════════════════
def toggle_classic_context_menu(enable, cb=None):
    """enable=True → Ativa menu clássico. enable=False → Reverte para o novo menu do Win 11."""
    clsid_path = r"HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32"
    if enable:
        # Cria a chave com valor padrão vazio — isso força o menu clássico
        cmd = ["reg", "add", clsid_path, "/ve", "/t", "REG_SZ", "/d", "", "/f"]
        try:
            result = subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30)
            if cb:
                icon = "✅" if result.returncode == 0 else "⚠️"
                cb(f"{icon} Menu de contexto clássico ativado")
        except Exception as e:
            if cb: cb(f"❌ Menu clássico — Erro: {str(e)}")
    else:
        # Remove a chave para voltar ao comportamento padrão do Win 11
        cmd = ["reg", "delete", clsid_path, "/f"]
        try:
            subprocess.run(cmd, creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30)
            if cb: cb("✅ Menu de contexto moderno restaurado (padrão Win 11)")
        except Exception as e:
            if cb: cb(f"❌ Erro ao restaurar menu: {str(e)}")

# ═══════════════════════════════════════════════════════════
#  HIBERNAÇÃO / INICIALIZAÇÃO RÁPIDA
# ═══════════════════════════════════════════════════════════
def toggle_hibernation(enable, cb=None):
    """enable=True → Desativa hibernação (libera GBs no C:). enable=False → Reativa."""
    action = "off" if enable else "on"
    desc = "Hibernação desativada (hiberfil.sys removido)" if enable else "Hibernação reativada"
    try:
        result = subprocess.run(
            ["powercfg.exe", "/hibernate", action],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=30
        )
        if cb:
            icon = "✅" if result.returncode == 0 else "⚠️"
            cb(f"{icon} {desc}")
    except Exception as e:
        if cb: cb(f"❌ Hibernação — Erro: {str(e)}")

# ═══════════════════════════════════════════════════════════
#  TELA DE BLOQUEIO
# ═══════════════════════════════════════════════════════════
def toggle_lock_screen(enable, cb=None):
    """enable=True → Desativa tela de bloqueio. enable=False → Restaura."""
    val = "1" if enable else "0"
    desc = "Tela de bloqueio desativada" if enable else "Tela de bloqueio restaurada (padrão)"
    run_reg(r"HKLM\SOFTWARE\Policies\Microsoft\Windows\Personalization",
            "NoLockScreen", "REG_DWORD", val, cb, desc)

# ═══════════════════════════════════════════════════════════
#  TECLAS DE ADERÊNCIA (STICKY KEYS)
# ═══════════════════════════════════════════════════════════
def toggle_sticky_keys(enable, cb=None):
    """enable=True → Desativa Sticky Keys (flags=506). enable=False → Restaura padrão."""
    val = "506" if enable else "510"
    desc = "Teclas de Aderência desativadas" if enable else "Teclas de Aderência restauradas (padrão)"
    run_reg(r"HKCU\Control Panel\Accessibility\StickyKeys",
            "Flags", "REG_SZ", val, cb, desc)

# ═══════════════════════════════════════════════════════════
#  ÍCONE DO CHAT / MEET NOW NA BARRA DE TAREFAS
# ═══════════════════════════════════════════════════════════
def toggle_taskbar_chat(enable, cb=None):
    """enable=True → Oculta ícone do Chat/Meet Now. enable=False → Exibe (padrão)."""
    val = "0" if enable else "1"
    desc = "Ícone de Chat/Teams oculto na barra" if enable else "Ícone de Chat/Teams visível (padrão)"
    run_reg(r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
            "TaskbarMn", "REG_DWORD", val, cb, desc)

# ═══════════════════════════════════════════════════════════
#  OTIMIZAÇÃO DE DNS
# ═══════════════════════════════════════════════════════════
def toggle_fast_dns(enable, cb=None):
    """enable=True → Define Cloudflare DNS. enable=False → DHCP."""
    desc = "DNS Cloudflare Ativado" if enable else "DNS restaurado para DHCP Automático"
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
            if cb: cb(f"✅ {desc}")
        else:
            if cb: cb("⚠️ Nenhuma interface de rede ativa encontrada para alterar o DNS.")
    except Exception as e:
        if cb: cb(f"❌ DNS — Erro: {str(e)}")

# ═══════════════════════════════════════════════════════════
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
}

def apply_selected_tweaks(tasks_dict, status_callback=None):
    """Aplica ou reverte cada tweak conforme o estado do switch (ON/OFF)."""
    total = len(tasks_dict)
    needs_explorer_restart = False
    
    for i, (key, is_on) in enumerate(tasks_dict.items(), 1):
        if key in TWEAKS_MAP:
            name, func = TWEAKS_MAP[key]
            action = "Ativando" if is_on else "Revertendo"
            if status_callback:
                status_callback(f"[{i}/{total}] {action}: {name}...")
            func(enable=is_on, cb=status_callback)
            
            if key in ("show_hidden_extensions", "enable_dark_mode", "classic_context_menu",
                       "hide_taskbar_chat"):
                needs_explorer_restart = True
            time.sleep(0.3)
    
    # Reinicia Explorer para aplicar mudanças visuais
    if needs_explorer_restart:
        if status_callback:
            status_callback("🔄 Reiniciando Explorer para aplicar mudanças visuais...")
        time.sleep(1)
        try:
            subprocess.run(["taskkill", "/F", "/IM", "explorer.exe"],
                         creationflags=CREATE_NO_WINDOW, capture_output=True)
            time.sleep(1.5)
            subprocess.Popen(["explorer.exe"], creationflags=CREATE_NO_WINDOW)
        except:
            pass
    
    if status_callback:
        status_callback("✅ Todos os tweaks foram processados!")

def check_reg(hkey, path, key, expected_val):
    try:
        reg_key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(reg_key, key)
        winreg.CloseKey(reg_key)
        return str(val) == str(expected_val)
    except OSError:
        return False

def get_current_tweak_states():
    """Verifica no registro se os tweaks já estão ativados."""
    # Menu clássico: chave existe = ativado
    def _classic_menu_active():
        try:
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32",
                               0, winreg.KEY_READ)
            winreg.CloseKey(k)
            return True
        except OSError:
            return False

    states = {
        "disable_telemetry":      check_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\DataCollection", "AllowTelemetry", 0),
        "show_hidden_extensions": check_reg(winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "HideFileExt", 0),
        "disable_bing_search":    check_reg(winreg.HKEY_CURRENT_USER,  r"Software\Policies\Microsoft\Windows\Explorer", "DisableSearchBoxSuggestions", 1),
        "enable_dark_mode":       check_reg(winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize", "AppsUseLightTheme", 0),
        "classic_context_menu":   _classic_menu_active(),
        "disable_hibernation":    False,   # powercfg não tem estado legível via reg de forma confiável
        "disable_lock_screen":    check_reg(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows\Personalization", "NoLockScreen", 1),
        "disable_sticky_keys":    check_reg(winreg.HKEY_CURRENT_USER,  r"Control Panel\Accessibility\StickyKeys", "Flags", "506"),
        "hide_taskbar_chat":      check_reg(winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "TaskbarMn", 0),
        "optimize_dns":           False,   # Sem checagem complexa de DNS
    }
    return states
