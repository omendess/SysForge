# SysForge 2.0 - Motor de Implantação OS

SysForge 2.0 é um utilitário desenvolvido em Python (com interface CustomTkinter em paradigma Dashboard) destinado a automatizar o processo pós-formatação de máquinas Windows 11. O aplicativo roda silenciosamente em background e foi refatorado para entregar máxima performance sem congelamentos de UI e estritamente sem caixas pretas de CMD.

## Estrutura de Diretórios
```
/SysForge
 ├── README.md
 ├── main.py
 ├── /gui
 │    └── app_window.py
 ├── /worker
 │    └── thread_manager.py
 ├── /gear
 │    ├── hardware_reader.py
 │    ├── system_cleaner.py
 │    ├── software_installer.py
 │    ├── office_deploy.py
 │    ├── windows_tweaks.py
 │    └── app_manager.py
 └── /OfficeInstall
      ├── config.xml
      └── setup.exe
```

## Como Compilar via PyInstaller
Utilize o seguinte comando para gerar o `.exe` modular:
```bash
pyinstaller --noconfirm --onedir --windowed --add-data "gui;gui" --add-data "gear;gear" --add-data "worker;worker" main.py
```
**Importante:** A pasta `/OfficeInstall` original deve ser copiada manualmente para dentro da pasta `dist/main` ao lado do `.exe` compilado para que a instalação do Office LTSC funcione corretamente.

## Funcionalidades
- **Dashboard e Limpeza**: Exibição de hardware via psutil, limpeza de temporários e `Windows.old` utilizando `takeown`/`icacls`.
- **Softwares (Arsenal Expandido)**: Listas categorizadas do Winget para navegadores, comunicação, desenvolvimento e mais.
- **Windows Tweaks**: Ferramenta de injeção de registro para modo escuro, desativação de telemetria, Bing no iniciar e exibição de arquivos ocultos.
- **App Manager**: Desinstalador e varredor de Bloatwares (ex: TikTok, McAfee), que localiza registros da Microsoft para obter Uninstall Strings precisas.
