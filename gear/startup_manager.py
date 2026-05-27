import winreg
import os
import subprocess

CREATE_NO_WINDOW = 0x08000000

# ── Chaves de registro para inicialização ─────────────────────────────────────
_REG_RUN_PATHS = [
    (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\Run",         "Usuário (Run)"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",         "Sistema (Run)"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run", "Sistema x86 (Run)"),
    (winreg.HKEY_CURRENT_USER,  r"Software\Microsoft\Windows\CurrentVersion\RunOnce",     "Usuário (RunOnce)"),
    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",     "Sistema (RunOnce)"),
]

# Chave onde Autoruns/Windows armazena itens desabilitados
_DISABLED_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"
_DISABLED_KEY_CU = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"


def _is_disabled_via_approved(hive_hint, name):
    """
    Windows armazena o estado de habilitação em StartupApproved.
    O primeiro byte do valor binário indica: 02/06 = enabled, 03/07 = disabled.
    """
    keys_to_try = [
        (winreg.HKEY_CURRENT_USER,  _DISABLED_KEY_CU),
        (winreg.HKEY_LOCAL_MACHINE, _DISABLED_KEY),
    ]
    for hive, path in keys_to_try:
        try:
            k = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            data, _ = winreg.QueryValueEx(k, name)
            winreg.CloseKey(k)
            if isinstance(data, bytes) and len(data) > 0:
                return data[0] in (3, 7)   # 3/7 = disabled
        except OSError:
            pass
    return False   # não encontrado = habilitado


def get_startup_items():
    """Retorna lista de programas de inicialização com estado habilitado/desabilitado."""
    items = []

    for hkey, path, scope in _REG_RUN_PATHS:
        try:
            key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    disabled = _is_disabled_via_approved(hkey, name)
                    items.append({
                        "name":     name,
                        "command":  value,
                        "scope":    scope,
                        "source":   "registro",
                        "hkey":     hkey,
                        "reg_path": path,
                        "enabled":  not disabled,
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except OSError:
            continue

    # ── Pasta Startup do usuário atual ───────────────────────────────────────
    for folder_key, label in [
        (os.path.join(os.environ.get("APPDATA", ""),
                      r"Microsoft\Windows\Start Menu\Programs\Startup"), "Pasta Startup (Usuário)"),
        (r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\StartUp", "Pasta Startup (Todos)"),
    ]:
        if os.path.exists(folder_key):
            for f in os.listdir(folder_key):
                fp = os.path.join(folder_key, f)
                if os.path.isfile(fp):
                    items.append({
                        "name":     f.replace(".lnk", "").replace(".bat", "").replace(".cmd", ""),
                        "command":  fp,
                        "scope":    label,
                        "source":   "pasta",
                        "hkey":     None,
                        "reg_path": folder_key,
                        "enabled":  True,
                    })

    return sorted(items, key=lambda x: x["name"].lower())


def get_scheduled_tasks():
    """
    Retorna tarefas agendadas relevantes (exclui tarefas da Microsoft/sistema).
    Usa schtasks /query /fo CSV para compatibilidade universal.
    """
    tasks = []
    try:
        result = subprocess.run(
            ["schtasks", "/query", "/fo", "CSV", "/v"],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True,
            encoding="cp850", errors="replace", timeout=30
        )
        lines = result.stdout.splitlines()
        if not lines:
            return tasks

        # Descobre índices das colunas no cabeçalho
        header = lines[0].replace('"', '').split(",")
        def col(name_part):
            for i, h in enumerate(header):
                if name_part.lower() in h.lower():
                    return i
            return -1

        idx_name    = col("nome da tarefa") or col("taskname") or col("task name") or 0
        idx_status  = col("status") or col("scheduled task state") or 2
        idx_next    = col("próxima") or col("next run") or 3
        idx_trigger = col("gatilho") or col("trigger") or col("schedule type") or 6
        idx_author  = col("autor") or col("author") or -1

        seen = set()
        for line in lines[1:]:
            if not line.strip() or line.startswith('"Nenhuma tarefa'):
                continue
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) <= max(idx_name, idx_status):
                continue

            task_name = parts[idx_name] if idx_name < len(parts) else ""
            status    = parts[idx_status] if idx_status < len(parts) else "—"
            next_run  = parts[idx_next]  if idx_next  < len(parts) else "—"
            trigger   = parts[idx_trigger] if idx_trigger < len(parts) else "—"
            author    = parts[idx_author] if idx_author > 0 and idx_author < len(parts) else "—"

            # Filtra tarefas do sistema Microsoft
            lower = task_name.lower()
            if any(x in lower for x in ["\\microsoft\\", "\\windows\\"]):
                continue

            # Limpa o nome da tarefa (remove path)
            display = task_name.split("\\")[-1] if "\\" in task_name else task_name
            if not display or display in seen:
                continue
            seen.add(display)

            enabled = "habilitado" in status.lower() or "enabled" in status.lower() or "pronta" in status.lower() or "ready" in status.lower()

            tasks.append({
                "name":     display,
                "path":     task_name,
                "status":   status,
                "next_run": next_run,
                "trigger":  trigger,
                "author":   author,
                "enabled":  enabled,
            })

    except Exception:
        pass

    return sorted(tasks, key=lambda x: x["name"].lower())


def disable_startup_item(item, cb=None):
    """Remove um item da inicialização automática."""
    try:
        if item["source"] == "registro" and item["hkey"] is not None:
            key = winreg.OpenKey(item["hkey"], item["reg_path"], 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, item["name"])
            winreg.CloseKey(key)
            if cb: cb(f"✅ '{item['name']}' removido da inicialização")
            return True
        else:
            # Pasta Startup
            fp = item["command"]
            if not os.path.exists(fp):
                fp = os.path.join(item["reg_path"], item["name"] + ".lnk")
            if os.path.exists(fp):
                os.remove(fp)
                if cb: cb(f"✅ '{item['name']}' removido da pasta Startup")
                return True
            else:
                if cb: cb(f"⚠️ Arquivo não encontrado: {item['name']}")
                return False
    except PermissionError:
        if cb: cb(f"⚠️ Sem permissão para remover '{item['name']}' — execute como Admin")
        return False
    except Exception as e:
        if cb: cb(f"❌ Erro: {e}")
        return False


def disable_scheduled_task(task_path, cb=None):
    """Desabilita uma tarefa agendada via schtasks."""
    try:
        result = subprocess.run(
            ["schtasks", "/change", "/tn", task_path, "/disable"],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            if cb: cb(f"✅ Tarefa '{task_path}' desabilitada")
            return True
        else:
            if cb: cb(f"⚠️ Falha ao desabilitar tarefa (código {result.returncode})")
            return False
    except Exception as e:
        if cb: cb(f"❌ Erro: {e}")
        return False

