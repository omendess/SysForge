import os
import datetime
import psutil
from gear.hardware_reader import get_all_hardware
from gear.power_config import get_current_plan
from gear.network_config import get_current_hostname

def generate_report(output_dir=None):
    """Gera um relatório completo de hardware em TXT."""
    hw = get_all_hardware()
    hostname = get_current_hostname()
    power_plan = get_current_plan()
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Informações de disco
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(f"  {part.device}  Total: {usage.total/(1024**3):.1f} GB  |  "
                        f"Usado: {usage.used/(1024**3):.1f} GB  |  "
                        f"Livre: {usage.free/(1024**3):.1f} GB  |  "
                        f"Uso: {usage.percent}%")
        except:
            continue
    
    # RAM detalhada
    mem = psutil.virtual_memory()
    
    # Rede
    nets = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                nets.append(f"  {iface}: {addr.address}")
    
    report = f"""╔══════════════════════════════════════════════════╗
║        RELATÓRIO DE HARDWARE — SysForge 2.0       ║
╠══════════════════════════════════════════════════╣
║  Data: {now:<42s}║
║  Hostname: {hostname:<38s}║
╚══════════════════════════════════════════════════╝

─── PROCESSADOR ───────────────────────────────────
  {hw['CPU']}

─── MEMÓRIA RAM ───────────────────────────────────
  Total: {mem.total/(1024**3):.2f} GB
  Usada: {mem.used/(1024**3):.2f} GB ({mem.percent}%)
  Livre: {mem.available/(1024**3):.2f} GB

─── PLACA DE VÍDEO ────────────────────────────────
  {hw['GPU']}

─── ARMAZENAMENTO ─────────────────────────────────
{chr(10).join(disks) if disks else '  Nenhum disco detectado'}

─── REDE ──────────────────────────────────────────
{chr(10).join(nets) if nets else '  Nenhuma interface detectada'}

─── ENERGIA ───────────────────────────────────────
  Plano ativo: {power_plan}

───────────────────────────────────────────────────
  Gerado por SysForge 2.0 — Motor de Implantação
───────────────────────────────────────────────────
"""
    
    if output_dir is None:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    
    os.makedirs(output_dir, exist_ok=True)
    filename = f"SysForge_Relatorio_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return filepath
