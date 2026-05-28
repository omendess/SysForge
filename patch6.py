import os

with open('gear/report_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('RELATÓRIO DE HARDWARE — SysForge 2.0', 'RELATÓRIO DE HARDWARE — SysForge Samaritan')
content = content.replace('Gerado por SysForge 2.0', 'Gerado por SysForge Samaritan')

with open('gear/report_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)


with open('gui/app_window.py', 'r', encoding='utf-8') as f:
    content = f.read()

safe_io_init = '''        net_io = psutil.net_io_counters()
        disk_io = psutil.disk_io_counters()
        self._last_net = (net_io.bytes_recv + net_io.bytes_sent) if net_io else 0
        self._last_disk = (disk_io.read_bytes + disk_io.write_bytes) if disk_io else 0'''

content = content.replace('        self._last_net = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent\n        self._last_disk = psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes', safe_io_init)

safe_io_loop = '''                # Rede
                net_io = psutil.net_io_counters()
                net_now = (net_io.bytes_recv + net_io.bytes_sent) if net_io else 0
                mbps = ((net_now - self._last_net) * 8) / 1000000.0 if self._last_net else 0
                self._last_net = net_now
                
                # Disco I/O
                disk_io = psutil.disk_io_counters()
                disk_now = (disk_io.read_bytes + disk_io.write_bytes) if disk_io else 0
                mbps_disk = ((disk_now - self._last_disk) / (1024 * 1024)) if self._last_disk else 0
                self._last_disk = disk_now'''

old_io_loop = '''                # Rede
                net_now = psutil.net_io_counters().bytes_recv + psutil.net_io_counters().bytes_sent
                mbps = ((net_now - self._last_net) * 8) / 1000000.0
                self._last_net = net_now
                
                # Disco I/O
                disk_now = psutil.disk_io_counters().read_bytes + psutil.disk_io_counters().write_bytes
                mbps_disk = ((disk_now - self._last_disk) / (1024 * 1024))
                self._last_disk = disk_now'''

content = content.replace(old_io_loop, safe_io_loop)

with open('gui/app_window.py', 'w', encoding='utf-8') as f:
    f.write(content)
