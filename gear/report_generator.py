import os
import datetime
import platform
from gear.hardware_reader import get_all_hardware
from gear.power_config import get_current_plan
from gear.network_config import get_current_hostname
from gear.system_info import get_windows_info

def generate_report(output_dir=None):
    """Gera um relatório hiper-detalhado do sistema em TXT."""
    hw = get_all_hardware()
    hostname = get_current_hostname()
    power_plan = get_current_plan()
    win_info = get_windows_info()
    now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # OS Info
    os_str = f"  Sistema: {win_info.get('product', platform.system())} {win_info.get('edition', '')}\n"
    os_str += f"  Build: {win_info.get('build', platform.version())} ({win_info.get('arch', platform.machine())})\n"
    
    # Motherboard
    mb = hw.get("Placa Mãe", {})
    mb_str = f"  Fabricante: {mb.get('Fabricante', '')}\n  Produto: {mb.get('Produto', '')}\n  Serial: {mb.get('Serial', '')}\n  BIOS: {mb.get('BIOS', '')}\n"
    
    # CPU
    cpu = hw.get("CPU", {})
    cpu_str = f"  Modelo: {cpu.get('Nome', '')}\n  Arquitetura: {cpu.get('Núcleos/Threads', '')}\n  Frequência Máxima: {cpu.get('Clock Max', '')}\n  Memória Cache: {cpu.get('Cache', '')}\n  Virtualização: {cpu.get('Virtualização', '')}\n  Socket: {cpu.get('Socket', '')}\n"
    
    # RAM
    ram = hw.get("RAM", {})
    ram_str = f"  Total: {ram.get('Total', '')}\n  Uso Atual: {ram.get('Uso', '')}\n"
    for stick in ram.get('Físico', []):
        ram_str += f"    - {stick}\n"
        
    # GPU
    gpu = hw.get("GPU", {})
    gpu_str = ""
    for g in gpu.get("Placas", []):
        gpu_str += f"  Modelo: {g.get('Nome', '')}\n  VRAM Dedicada: {g.get('VRAM', '')}\n  Display: {g.get('Resolução', '')}\n  Driver: {g.get('Driver', '')}\n"
        
    # Discos
    disks = hw.get("Disks", {})
    disk_str = "  [Físicos]\n"
    for d in disks.get("Físicos", []):
        disk_str += f"    {d.get('Tipo', 'UKN')} | {d.get('Tamanho', '')} | {d.get('Modelo', '')} (Interface: {d.get('Interface', '')}) [Saúde: {d.get('Saúde', '')}]\n"
        
    disk_str += "\n  [Lógicos (Partições)]\n"
    for p in disks.get("Lógicos", []):
        disk_str += f"    {p.get('Letra', 'C:')} [{p.get('FileSys', '')}] -> {p.get('Total', '')} Total | Livre: {p.get('Livre', '')} | Uso: {p.get('Uso', '')}\n"
        
    # Rede
    net = hw.get("Rede", [])
    net_str = ""
    for n in net:
        net_str += f"  Adaptador: {n.get('Adaptador', '')}\n  MAC: {n.get('MAC', '')}\n  IPv4: {n.get('IPv4', '')}\n  Link: {n.get('Velocidade', '')}\n\n"
        
    # Bateria
    bat = hw.get("Bateria", {})
    bat_str = "  "
    if isinstance(bat, str):
        bat_str += bat + "\n"
    else:
        bat_str += f"Status: {bat.get('Status', '')}\n  Saúde: {bat.get('Saúde da Bateria', '')}\n  Carga: {bat.get('Carga Restante', '')}\n  Design: {bat.get('Capacidade Original', '')} | Atual: {bat.get('Capacidade Atual', '')}\n"

    # Periféricos
    per = hw.get("Periféricos", {})
    per_str = "  [Áudio]\n"
    for a in per.get("Áudio", []):
        per_str += f"    - {a}\n"
    per_str += "\n  [Controladores USB]\n"
    for u in per.get("Controladores USB", []):
        per_str += f"    - {u}\n"

    report = f"""╔════════════════════════════════════════════════════════════════╗
║        RELATÓRIO DE HARDWARE E SOFTWARE — SysForge Samaritan      ║
╠════════════════════════════════════════════════════════════════╣
║  Data de Emissão: {now:<44s}║
║  Identificação: {hostname:<46s}║
╚════════════════════════════════════════════════════════════════╝

─── SISTEMA OPERACIONAL ─────────────────────────────────────────
{os_str}
─── PLACA MÃE E BIOS ────────────────────────────────────────────
{mb_str}
─── PROCESSADOR (CPU) ───────────────────────────────────────────
{cpu_str}
─── MEMÓRIA RAM ─────────────────────────────────────────────────
{ram_str}
─── PLACA DE VÍDEO (GPU) ────────────────────────────────────────
{gpu_str}
─── ARMAZENAMENTO (DISCOS E PARTIÇÕES) ──────────────────────────
{disk_str}
─── INTERFACES DE REDE ──────────────────────────────────────────
{net_str}
─── ENERGIA E BATERIA ───────────────────────────────────────────
  Plano ativo: {power_plan}
{bat_str}
─── PERIFÉRICOS ─────────────────────────────────────────────────
{per_str}
─────────────────────────────────────────────────────────────────
  Gerado por SysForge Samaritan — Motor de Implantação
  Aferição de Alta Precisão (CIM/WMI Engine)
─────────────────────────────────────────────────────────────────
"""
    
    if output_dir is None:
        output_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    
    os.makedirs(output_dir, exist_ok=True)
    filename = f"SysForge_Relatorio_Precision_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    return filepath
