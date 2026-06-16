# SYSFORGE - Documentação Técnica Oficial

**SINGULARITY DOT // VETOR SD-02**

O **SysForge** é uma suíte autônoma de implantação e manutenção de sistemas de TI, projetada sob a arquitetura do **Samaritan Protocol** e padronizada sob as diretrizes do ecossistema **Singularity Dot**.

## 1. Modos de Operação (Arquitetura Dual-Build)

O motor possui duas compilações geradas de forma independente através do pipeline `builder.py`.

### 1.1 Modo Portable (SD-02-PORTABLE)
- **Foco**: Técnicos de Bancada, uso em Pendrives e Diagnósticos Rápidos.
- **Estrutura**: Compilado via PyInstaller com flag `--onefile`. Dependências pesadas (`matplotlib`, `pandas`, `numpy`) são propositalmente extirpadas no processo de build para garantir leveza e rapidez de inicialização.
- **Autualização**: Recebe atualizações "Over-The-Air" (OTA) de forma silenciosa e aplica patches em tempo de execução sem requerer intervenção manual (Auto-Updater).
- **Vantagem**: Não necessita de elevação extrema persistente nem de registro no sistema operacional base.

### 1.2 Modo Host (SD-02-HOST)
- **Foco**: Implantação em Servidores e Estações Locais Residenciais/Empresariais.
- **Estrutura**: Conta com um instalador compilado em Inno Setup (LZMA2), projetado para injetar dependências e configurar caminhos locais.
- **Privilégios**: Exige e opera constantemente em nível de Administrador (Ring 0 / UAC-Admin), sendo capaz de manipular o Registro do Windows, Serviços, Programações de Tarefas e Pastas Root do Sistema Operacional.
- **Atualização**: Notifica o cliente da existência de novos pacotes `SysForge_Setup.exe` diretamente da API oficial (GitHub Releases).

## 2. Subsistemas e Telemetria

- **Matriz de Vigilância (Dashboard)**: Utiliza a biblioteca `psutil` para leituras rigorosas a cada ciclo assíncrono (1.5s), extraindo IOPS de Disco, Percentual de CPU, Gargalos em RAM (Top 5 Processos gulosos) e Tráfego de Rede (mbps).
- **Engenharia de Expurgos (Cleaner)**: Executa varreduras focadas nas lixeiras do Windows Update e arquivos temporários da conta (Appdata/Temp e C:/Windows/Temp), e suporta higienização da pasta `Windows.old`.
- **Motor de Software Dinâmico**: Lê manifestos e distribui softwares e utilitários vitais em silêncio de acordo com configurações estritas.

## 3. Gestão e Versionamento

O fluxo de implantação é rastreado na **SYS_TIMELINE.md**, e a versão mestre deve ser sincronizada no nó `gear/updater.py` (variável `CURRENT_VERSION`). O pipeline de build (`builder.py`) extrai dinamicamente a string de versão do Updater para rotular os binários de saída, prevenindo esquecimentos ou colisões no ambiente de releases do GitHub.

---
*Documento gerado e atualizado autonomamente sob protocolo do Antigravity.*
