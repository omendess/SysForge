import psutil
import subprocess
import json
import os
import winreg
import concurrent.futures

CREATE_NO_WINDOW = 0x08000000

def _run_ps_json(cmd):
    try:
        full_cmd = ["powershell", "-NoProfile", "-Command", f"{cmd} | ConvertTo-Json -Compress"]
        out = subprocess.check_output(full_cmd, creationflags=CREATE_NO_WINDOW, text=True, timeout=10)
        if out.strip():
            data = json.loads(out)
            return [data] if isinstance(data, dict) else data
    except Exception:
        pass
    return []

def get_motherboard_info():
    board_data = _run_ps_json("Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product, SerialNumber, Version")
    bios_data = _run_ps_json("Get-CimInstance Win32_BIOS | Select-Object Manufacturer, Name, Version, ReleaseDate")
    
    info = {"Fabricante": "Desconhecido", "Produto": "Desconhecido", "Serial": "—", "BIOS": "—"}
    if board_data:
        b = board_data[0]
        info["Fabricante"] = b.get("Manufacturer", "Desconhecido").strip()
        info["Produto"] = b.get("Product", "Desconhecido").strip()
        info["Serial"] = b.get("SerialNumber", "—").strip()
        
    if bios_data:
        bi = bios_data[0]
        date_str = bi.get("ReleaseDate", "")
        # PowerShell JSON date format usually looks like "\/Date(1629849600000)\/"
        bios_v = f"{bi.get('Manufacturer', '')} {bi.get('Name', '')} ({bi.get('Version', '')})"
        info["BIOS"] = bios_v.strip()
        
    return info

def get_cpu_info():
    data = _run_ps_json("Get-CimInstance Win32_Processor | Select-Object Name, Manufacturer, NumberOfCores, NumberOfLogicalProcessors, MaxClockSpeed, L2CacheSize, L3CacheSize, VirtualizationFirmwareEnabled, SocketDesignation")
    if not data:
        return {"Nome": "Desconhecido"}
        
    c = data[0]
    name = c.get("Name", "Desconhecido").strip()
    cores = c.get("NumberOfCores", 0)
    threads = c.get("NumberOfLogicalProcessors", 0)
    clock = c.get("MaxClockSpeed", 0)
    l2 = c.get("L2CacheSize", 0)
    l3 = c.get("L3CacheSize", 0)
    virt = "Habilitada" if c.get("VirtualizationFirmwareEnabled") else "Desabilitada"
    socket = c.get("SocketDesignation", "—")
    
    return {
        "Nome": name,
        "Núcleos/Threads": f"{cores} Cores / {threads} Threads",
        "Clock Max": f"{clock} MHz",
        "Cache": f"L2: {l2} KB | L3: {l3/1024 if l3 else 0:.1f} MB",
        "Virtualização": virt,
        "Socket": socket
    }

def get_ram_info():
    vm = psutil.virtual_memory()
    total_gb = vm.total / (1024**3)
    used_gb = vm.used / (1024**3)
    
    # Detalhes físicos
    data = _run_ps_json("Get-CimInstance Win32_PhysicalMemory | Select-Object Manufacturer, PartNumber, Capacity, Speed, FormFactor, MemoryType, DeviceLocator")
    
    sticks = []
    if data:
        for stick in data:
            cap = stick.get("Capacity", 0)
            if cap == 0: continue
            cap_gb = cap / (1024**3)
            speed = stick.get("Speed", 0)
            man = stick.get("Manufacturer", "Unknown").strip()
            part = stick.get("PartNumber", "").strip()
            loc = stick.get("DeviceLocator", "").strip()
            sticks.append(f"{loc}: {cap_gb:.0f}GB {speed}MHz {man} ({part})")
            
    # Formata a string para compatibilidade com o GUI, mas envia o dict detalhado no retorno
    gui_string = f"{total_gb:.2f} GB"
    
    return {
        "GUI_String": gui_string,
        "Total": f"{total_gb:.2f} GB",
        "Uso": f"{used_gb:.2f} GB ({vm.percent}%)",
        "Físico": sticks
    }

def get_gpu_info():
    data = _run_ps_json("Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate")
    gpus = []
    gui_names = []
    if data:
        for g in data:
            name = g.get("Name", "Desconhecida").strip()
            gui_names.append(name)
            ram = g.get("AdapterRAM", 0)
            ram_gb = ram / (1024**3) if ram else 0
            res_h = g.get("CurrentHorizontalResolution", 0)
            res_v = g.get("CurrentVerticalResolution", 0)
            refresh = g.get("CurrentRefreshRate", 0)
            driver = g.get("DriverVersion", "—")
            
            res_str = f"{res_h}x{res_v} @ {refresh}Hz" if res_h else "Sem monitor ativo"
            gpus.append({
                "Nome": name,
                "VRAM": f"{ram_gb:.2f} GB" if ram_gb else "Compartilhada/Desconhecida",
                "Resolução": res_str,
                "Driver": driver
            })
            
    return {
        "GUI_String": " / ".join(gui_names) if gui_names else "Desconhecida",
        "Placas": gpus
    }

def get_disks_detailed():
    data = _run_ps_json("Get-PhysicalDisk | Select-Object FriendlyName, MediaType, Size, HealthStatus, BusType")
    disks = []
    if data:
        for d in data:
            name = d.get("FriendlyName", "Unknown").strip()
            media = str(d.get("MediaType", "0")).upper()
            if media == "3": media = "HDD"
            elif media == "4": media = "SSD"
            elif media == "5": media = "SCM"
            else: media = "Desconhecido"
            
            size = d.get("Size", 0)
            size_gb = size / (1024**3) if size else 0
            health = d.get("HealthStatus", "—")
            bus = d.get("BusType", "—")
            
            disks.append({
                "Modelo": name,
                "Tipo": media,
                "Interface": bus,
                "Saúde": health,
                "Tamanho": f"{size_gb:.2f} GB"
            })
            
    # Partições Lógicas
    partitions = []
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt' and ('cdrom' in part.opts or not part.fstype):
            continue
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "Letra": part.device.replace("\\", ""),
                "FileSys": part.fstype,
                "Total": f"{usage.total / (1024**3):.2f} GB",
                "Livre": f"{usage.free / (1024**3):.2f} GB",
                "Uso": f"{usage.percent}%"
            })
        except:
            pass
            
    return {"Físicos": disks, "Lógicos": partitions}

def get_network_info():
    data = _run_ps_json("Get-NetAdapter | Where-Object Status -eq 'Up' | Select-Object Name, InterfaceDescription, MacAddress, LinkSpeed")
    net = []
    if data:
        for n in data:
            desc = n.get("InterfaceDescription", "").strip()
            mac = n.get("MacAddress", "").strip()
            speed = n.get("LinkSpeed", "").strip()
            
            # Pega o IP usando psutil
            ip = "—"
            for iface, addrs in psutil.net_if_addrs().items():
                if n.get("Name", "") in iface or desc in iface:
                    for addr in addrs:
                        if addr.family.name == 'AF_INET' and not addr.address.startswith('127.'):
                            ip = addr.address
                            break
                            
            net.append({
                "Adaptador": desc,
                "MAC": mac,
                "IPv4": ip,
                "Velocidade": speed
            })
    return net

def get_battery_info():
    data = _run_ps_json("Get-CimInstance Win32_Battery | Select-Object Name, DesignCapacity, FullChargeCapacity, EstimatedChargeRemaining, BatteryStatus")
    if not data:
        return "Nenhuma bateria detectada (Desktop)"
    
    b = data[0]
    name = b.get("Name", "Desconhecida").strip()
    design = b.get("DesignCapacity", 0)
    full = b.get("FullChargeCapacity", 0)
    rem = b.get("EstimatedChargeRemaining", 0)
    status = b.get("BatteryStatus", 0)
    
    # Status WMI map
    st_map = {1: "Descarregando", 2: "Conectada (AC)", 3: "Carregando", 4: "Crítica"}
    st_str = st_map.get(status, f"Status Code: {status}")
    
    health = "—"
    if design and full:
        health = f"{(full/design)*100:.1f}% (Saúde)"
        
    return {
        "Nome": name,
        "Capacidade Original": f"{design} mWh",
        "Capacidade Atual": f"{full} mWh",
        "Saúde da Bateria": health,
        "Carga Restante": f"{rem}%",
        "Status": st_str
    }

def get_peripherals():
    audio_data = _run_ps_json("Get-CimInstance Win32_SoundDevice | Select-Object Manufacturer, Name, Status")
    usb_data = _run_ps_json("Get-CimInstance Win32_USBController | Select-Object Manufacturer, Name")
    
    audio = []
    if audio_data:
        for a in audio_data:
            audio.append(f"{a.get('Manufacturer', '')} - {a.get('Name', '')} [{a.get('Status', '')}]")
            
    usb = []
    if usb_data:
        for u in usb_data:
            usb.append(f"{u.get('Manufacturer', '')} - {u.get('Name', '')}")
            
    return {"Áudio": audio, "Controladores USB": list(set(usb))}

def get_all_hardware():
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f_mb = executor.submit(get_motherboard_info)
        f_cpu = executor.submit(get_cpu_info)
        f_ram = executor.submit(get_ram_info)
        f_gpu = executor.submit(get_gpu_info)
        f_disk = executor.submit(get_disks_detailed)
        f_net = executor.submit(get_network_info)
        f_bat = executor.submit(get_battery_info)
        f_per = executor.submit(get_peripherals)
        
        mb = f_mb.result()
        cpu = f_cpu.result()
        ram = f_ram.result()
        gpu = f_gpu.result()
        disk = f_disk.result()
        net = f_net.result()
        bat = f_bat.result()
        per = f_per.result()

    return {
        "Placa Mãe": mb,
        "CPU": cpu,
        "RAM": ram,
        "GPU": gpu,
        "Disks": disk,
        "Rede": net,
        "Bateria": bat,
        "Periféricos": per,
        # Compatibilidade com GUI legada
        "CPU_GUI": cpu.get("Nome", "Desconhecido"),
        "RAM_GUI": ram.get("GUI_String", "Desconhecido"),
        "GPU_GUI": gpu.get("GUI_String", "Desconhecido")
    }
