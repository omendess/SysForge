# ⚡ SysForge
**Motor de Implantação e Manutenção de Sistemas TI**
*(Versão 1.0.0 - Release Candidate)*

O SysForge é uma suíte de engenharia de software nativa para Windows, desenhada para automação de setups, telemetria de hardware e limpeza profunda de SO. Construído sob uma **Arquitetura Dual-Build**, ele opera tanto como uma ferramenta tática de pendrive quanto como um serviço residente na máquina do cliente.

## ⚙️ Arquitetura e Recursos
* **Modo Portable (Bancada):** Executável único (`.exe`). Ideal para técnicos. Não deixa rastros no registro.
* **Modo Host (Cliente):** Instalador comprimido via LZMA2. Requer elevação UAC (Ring 0) para manutenção profunda de discos locais.
* **Motor de Expurgo Profundo:** Varredura granular de lixo de sistema (Cache, Temp, Update Logs) com interceptação de processos (Process Termination) via `psutil`.
* **Matriz de Vigilância:** Dashboard de telemetria em tempo real (CPU, RAM, I/O, Rede).
* **Auto-Updater Consciente (Edition-Aware):** Conectado à REST API do GitHub. O modo Portable atualiza a si mesmo via OTA; o modo Host notifica o cliente sobre novos instaladores.

## 🚀 Instalação
Para baixar a versão mais recente, acesse a aba [Releases](../../releases/latest) e escolha sua versão:
* `SysForge_Portable.exe` (Para Pendrives)
* `SysForge_Setup_vX.exe` (Para Instalação Local)

---
*Desenvolvido e mantido por Orlando Mendes.*
