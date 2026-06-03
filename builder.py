import os
import sys
import shutil
import re

def main():
    if len(sys.argv) < 2:
        print("Uso: python builder.py [PORTABLE|HOST]")
        sys.exit(1)
        
    mode = sys.argv[1].upper()
    if mode not in ["PORTABLE", "HOST"]:
        print("Modo invalido. Use PORTABLE ou HOST.")
        sys.exit(1)
        
    # 1. Altera temporariamente a flag no build_config.py
    config_path = os.path.join("gear", "build_config.py")
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Substitui a linha EDICAO_ATUAL
    content = re.sub(r'EDICAO_ATUAL\s*=\s*".*"', f'EDICAO_ATUAL = "{mode}"', content)
    
    with open(config_path, "w", encoding="utf-8") as f:
        f.write(content)
        
    print(f"[*] Flag EDICAO_ATUAL definida para: {mode}")
    
    # 2. Executa o PyInstaller com configuracoes limpas
    exe_name = f"SysForge_{mode.capitalize()}"
    
    # Montando o comando do pyinstaller com os parametros solicitados e dependencias
    cmd = (
        f'pyinstaller --noconfirm --onefile --noconsole --uac-admin --name "{exe_name}" '
        f'--icon "icon.ico" '
        f'--add-data "gui;gui" --add-data "gear;gear" --add-data "worker;worker" '
        f'--add-data "version.json;." --add-data "icon.ico;." '
        f'--add-data "icon.png;." --add-data "logo_mlabs.png;." '
    )
    
    # Se for PORTABLE, podemos excluir bibliotecas pesadas aqui (ex: --exclude-module=opencv)
    if mode == "PORTABLE":
        cmd += '--exclude-module=matplotlib --exclude-module=numpy --exclude-module=pandas '
        
    cmd += 'main.py'
    
    print(f"[*] Compilando {exe_name}...")
    print(f"[*] Comando: {cmd}")
    
    exit_code = os.system(cmd)
    
    if exit_code != 0:
        print("[!] Erro durante a compilacao.")
        sys.exit(1)
        
    # 3. Limpeza Cirurgica (Obrigatório)
    print("\n[*] Iniciando limpeza de cache (Regra 1)...")
    
    build_dir = "build"
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
        print(f"[-] Pasta removida: {build_dir}/")
        
    spec_file = f"{exe_name}.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"[-] Arquivo removido: {spec_file}")
        
    print(f"\n[+] Build {mode} concluido com sucesso! O executavel esta limpo na pasta 'dist/'.\n")

if __name__ == "__main__":
    main()
