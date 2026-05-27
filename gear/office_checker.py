import subprocess
import winreg
import glob
import os

CREATE_NO_WINDOW = 0x08000000

_EDITION_MAP = {
    "O365ProPlusRetail":      "Microsoft 365 ProPlus",
    "O365BusinessRetail":     "Microsoft 365 Business",
    "ProPlus2021Volume":      "Office LTSC 2021 ProPlus",
    "ProPlus2019Retail":      "Office 2019 ProPlus",
    "ProPlus2019Volume":      "Office 2019 LTSC",
    "ProPlus2016Retail":      "Office 2016 ProPlus",
    "HomeStudent2021Retail":  "Office 2021 Home & Student",
    "HomeStudent2019Retail":  "Office 2019 Home & Student",
    "Standard2021Volume":     "Office LTSC 2021 Standard",
    "Standard2019Volume":     "Office 2019 Standard",
}


def _read_reg(hive, path, key, default=""):
    try:
        k = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(k, key)
        winreg.CloseKey(k)
        return str(val).strip()
    except OSError:
        return default


# ═══════════════════════════════════════════════════════════
#  DETECÇÃO DINÂMICA DO OSPP.VBS — funciona em qualquer PC
# ═══════════════════════════════════════════════════════════
def _find_ospp_vbs():
    """
    3 estratégias em cascata:
    1. Registro: lê InstallationPath do ClickToRun
    2. Variáveis de ambiente ProgramFiles (cobre outras unidades/línguas)
    3. Glob recursivo: acha em qualquer caminho não-padrão
    """
    # Estratégia 1: via registro C2R
    c2r_base = r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration"
    install_path = _read_reg(winreg.HKEY_LOCAL_MACHINE, c2r_base, "InstallationPath")
    if install_path:
        for sub in [r"root\Office16", r"root\Office15", r"Office16", r"Office15"]:
            candidate = os.path.join(install_path, sub, "ospp.vbs")
            if os.path.exists(candidate):
                return candidate

    # Estratégia 2: variáveis de ambiente
    pf64 = os.environ.get("ProgramFiles",       r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)",  r"C:\Program Files (x86)")
    pf_w = os.environ.get("ProgramW6432",       pf64)

    subs = [
        r"Microsoft Office\root\Office16",
        r"Microsoft Office\root\Office15",
        r"Microsoft Office\Office16",
        r"Microsoft Office\Office15",
    ]
    for base in {pf64, pf86, pf_w}:
        for sub in subs:
            p = os.path.join(base, sub, "ospp.vbs")
            if os.path.exists(p):
                return p

    # Estratégia 3: glob recursivo
    for base in {pf64, pf86, pf_w}:
        pattern = os.path.join(base, "Microsoft Office*", "**", "ospp.vbs")
        results = glob.glob(pattern, recursive=True)
        if results:
            results.sort(key=lambda x: (0 if "root" in x else 1))
            return results[0]

    return None


# ═══════════════════════════════════════════════════════════
#  DETECÇÃO VIA REGISTRO C2R
# ═══════════════════════════════════════════════════════════
def _check_via_c2r():
    base = r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration"
    product_ids = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "ProductReleaseIds")
    version     = _read_reg(winreg.HKEY_LOCAL_MACHINE, base, "VersionToReport")
    if not product_ids and not version:
        return None

    edition = "Office (Edicao Desconhecida)"
    for pid, name in _EDITION_MAP.items():
        if pid in product_ids:
            edition = name
            break

    return {"edition": edition, "version": version or "---", "raw_ids": product_ids}


def _check_activation_via_registry():
    """Fallback: True se houver evidencia de ativacao no registro, None se inconclusivo."""
    paths = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Office\16.0\Common\Licensing",
         "CurrentSkuIdAgreementLicenseData"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
         "ProductReleaseIds"),
    ]
    for hive, path, key in paths:
        if _read_reg(hive, path, key):
            return True
    return None


# ═══════════════════════════════════════════════════════════
#  PARSING POR PRODUTO (ospp.vbs /dstatus)
# ═══════════════════════════════════════════════════════════
def _parse_all_products(ospp_path):
    """
    Roda ospp.vbs /dstatus e parseia cada bloco de produto.
    Retorna lista: [{name, description, sku_id, activated}, ...]
    OOB_GRACE nao e tratado como False — e inconclusivo, usa fallback de registro.
    """
    try:
        result = subprocess.run(
            ["cscript", "//NoLogo", ospp_path, "/dstatus"],
            creationflags=CREATE_NO_WINDOW, capture_output=True,
            text=True, timeout=30, encoding="utf-8", errors="replace"
        )
        out = result.stdout + result.stderr
    except Exception:
        return []

    products = []
    current  = {}

    for raw_line in out.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("---"):
            if current.get("name"):
                if current.get("activated") is None:
                    current["activated"] = _check_activation_via_registry()
                products.append(current)
            current = {}
            continue

        if ":" not in line:
            continue

        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        if key == "LICENSE NAME":
            current["name"] = val.split(",")[0].strip() if "," in val else val
        elif key == "LICENSE DESCRIPTION":
            current["description"] = val
        elif key == "SKU ID":
            current["sku_id"] = val
        elif key == "LICENSE STATUS":
            status = val.upper()
            if "LICENSED" in status:
                current["activated"] = True
            elif any(x in status for x in ("NON_GENUINE", "UNLICENSED", "NOTIFICATION")):
                reg = _check_activation_via_registry()
                current["activated"] = reg if reg is not None else False
            else:
                # OOB_GRACE ou desconhecido -> inconclusivo -> fallback decide
                current["activated"] = None

    if current.get("name"):
        if current.get("activated") is None:
            current["activated"] = _check_activation_via_registry()
        products.append(current)

    return products


# ═══════════════════════════════════════════════════════════
#  API PUBLICA
# ═══════════════════════════════════════════════════════════
def get_office_info():
    """
    Retorna:
      installed : bool
      edition   : str
      version   : str (build)
      products  : list[{name, description, sku_id, activated}]
      activated : bool | None (resumo: True=todos ok, False=algum nao, None=inconclusivo)
    """
    c2r = _check_via_c2r()
    if not c2r:
        return {"installed": False, "edition": "---", "version": "---",
                "products": [], "activated": None}

    ospp     = _find_ospp_vbs()
    products = _parse_all_products(ospp) if ospp else []

    # Fallback se ospp nao achou nada
    if not products:
        fb = _check_activation_via_registry()
        products = [{"name": c2r["edition"], "description": "Verificado via registro",
                     "sku_id": "---", "activated": fb}]

    statuses = [p["activated"] for p in products]
    if all(s is True for s in statuses):
        activated_summary = True
    elif any(s is False for s in statuses):
        activated_summary = False
    else:
        activated_summary = None

    return {
        "installed": True,
        "edition":   c2r["edition"],
        "version":   c2r["version"],
        "products":  products,
        "activated": activated_summary,
    }
