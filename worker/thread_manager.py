import threading
import time
import datetime
from gear.system_cleaner import clean_temp_folders, remove_windows_old
from gear.software_installer import install_software
from gear.office_deploy import install_and_activate_office
from gear.windows_tweaks import apply_selected_tweaks
from gear.app_manager import uninstall_multiple
from gear.power_config import set_high_performance
from gear.network_config import set_hostname
from gear.wallpaper import set_wallpaper
from gear.windows_update import check_and_install_updates
from gear.startup_manager import disable_startup_item
from gear.report_generator import generate_report


class LogManager:
    """Gerenciador de logs centralizado — Thread-safe."""
    def __init__(self):
        self._logs = []
        self._lock = threading.Lock()
        self._listeners = []
    
    def add(self, message):
        with self._lock:
            entry = {
                "time": datetime.datetime.now().strftime("%H:%M:%S"),
                "msg": message
            }
            self._logs.append(entry)
            for listener in self._listeners:
                try:
                    listener(entry)
                except:
                    pass
    
    def get_all(self):
        with self._lock:
            return list(self._logs)
    
    def clear(self):
        with self._lock:
            self._logs.clear()
    
    def subscribe(self, callback):
        self._listeners.append(callback)
    
    def export(self, filepath):
        with self._lock:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("═══ SysForge 2.0 — Log de Operações ═══\n\n")
                for entry in self._logs:
                    f.write(f"[{entry['time']}] {entry['msg']}\n")
            return filepath


# Instância global de logs
LOG = LogManager()


class GenericWorker:
    def __init__(self, tasks, status_callback, completion_callback):
        self.tasks = tasks
        self.status_callback = status_callback
        self.completion_callback = completion_callback
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def _log_and_status(self, msg):
        LOG.add(msg)
        if self.status_callback:
            self.status_callback(msg)

    def _run(self):
        try:
            task_type = self.tasks.get("type")
            
            if task_type == "dashboard":
                if self.tasks.get("clean_temp"):
                    self._log_and_status("🧹 Limpando arquivos temporários...")
                    clean_temp_folders()
                    self._log_and_status("✅ Temporários limpos")
                if self.tasks.get("clean_win_old"):
                    self._log_and_status("🧹 Removendo Windows.old...")
                    remove_windows_old()
                    self._log_and_status("✅ Windows.old removido")
                if self.tasks.get("install_office"):
                    install_and_activate_office(self._log_and_status)
                    
            elif task_type == "software":
                softs = self.tasks.get("list", [])
                total = len(softs)
                for i, wid in enumerate(softs, 1):
                    self._log_and_status(f"[{i}/{total}] Instalando...")
                    install_software(wid, self._log_and_status)
                    
            elif task_type == "tweaks":
                apply_selected_tweaks(self.tasks.get("tweaks_dict", {}), self._log_and_status)
                
            elif task_type == "uninstall":
                uninstall_multiple(self.tasks.get("app_list", []), self._log_and_status)
            
            elif task_type == "power":
                self._log_and_status("⚡ Configurando Alto Desempenho...")
                set_high_performance()
                self._log_and_status("✅ Plano ativado")
            
            elif task_type == "hostname":
                self._log_and_status(f"🏷️ Renomeando para {self.tasks['name']}...")
                set_hostname(self.tasks["name"], self._log_and_status)
            
            elif task_type == "wallpaper":
                set_wallpaper(self.tasks.get("path", ""), self._log_and_status)
            
            elif task_type == "winupdate":
                check_and_install_updates(self._log_and_status)
            
            elif task_type == "startup_disable":
                item = self.tasks.get("item")
                if item:
                    disable_startup_item(item, self._log_and_status)
            
            elif task_type == "task_disable":
                item = self.tasks.get("item")
                if item:
                    from gear.startup_manager import disable_scheduled_task
                    disable_scheduled_task(item["path"], self._log_and_status)
            
            elif task_type == "report":
                self._log_and_status("📄 Gerando relatório...")
                path = generate_report()
                if path:
                    self._log_and_status(f"✅ Relatório: {path}")
                    import os
                    os.startfile(path)
                else:
                    self._log_and_status("❌ Erro ao gerar.")
                    
            elif task_type == "custom":
                func = self.tasks.get("func")
                if func:
                    func(self._log_and_status)
                    
            elif task_type == "custom_generator":
                func = self.tasks.get("generator_func")
                if func:
                    for msg in func():
                        self._log_and_status(msg)
                        time.sleep(0.05)
                        
            self._log_and_status("Operação concluída com sucesso!")
            time.sleep(1)
        except Exception as e:
            self._log_and_status(f"❌ Erro crítico: {str(e)}")
        finally:
            if self.completion_callback:
                self.completion_callback()

class InterventionWorker:
    def __init__(self, func, log_callback, is_revert=False):
        self.func = func
        self.log_callback = log_callback
        self.is_revert = is_revert
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.thread.start()

    def _run(self):
        try:
            from gear.intervention_matrix import protocolo_guarda_chuva
            
            if not self.is_revert:
                self.log_callback("> INICIANDO PROTOCOLO GUARDA-CHUVA...")
                status = protocolo_guarda_chuva()
                self.log_callback(status)
            
            for step_msg in self.func():
                self.log_callback(step_msg)
                time.sleep(0.1)
            
            self.log_callback("> OPERAÇÃO CONCLUÍDA.\n")
        except Exception as e:
            self.log_callback(f"> [ ERRO CRÍTICO ]: {str(e)}\n")
