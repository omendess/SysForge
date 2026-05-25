import subprocess
import os
import datetime

CREATE_NO_WINDOW = 0x08000000

def set_high_performance(cb=None):
    """Ativa o plano de energia 'Alto Desempenho'."""
    try:
        # GUID padrão do Alto Desempenho
        guid = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"
        result = subprocess.run(
            ["powercfg", "/setactive", guid],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True
        )
        if result.returncode == 0:
            if cb: cb("✅ Plano de energia: Alto Desempenho ativado")
            return True
        else:
            # Tenta criar o plano caso não exista
            subprocess.run(
                ["powercfg", "/duplicatescheme", guid],
                creationflags=CREATE_NO_WINDOW, capture_output=True
            )
            subprocess.run(
                ["powercfg", "/setactive", guid],
                creationflags=CREATE_NO_WINDOW, capture_output=True
            )
            if cb: cb("✅ Plano Alto Desempenho criado e ativado")
            return True
    except Exception as e:
        if cb: cb(f"❌ Erro ao definir plano de energia: {e}")
        return False

def get_current_plan(cb=None):
    """Retorna o nome do plano de energia ativo."""
    try:
        result = subprocess.run(
            ["powercfg", "/getactivescheme"],
            creationflags=CREATE_NO_WINDOW, capture_output=True, text=True
        )
        if result.returncode == 0:
            # Output: "GUID do Esquema de Energia: xxx  (Nome)"
            line = result.stdout.strip()
            if "(" in line:
                return line.split("(")[-1].rstrip(")")
        return "Desconhecido"
    except:
        return "Desconhecido"
