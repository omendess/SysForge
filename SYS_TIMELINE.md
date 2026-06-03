# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 5.0.3.0 (Ciclo de Expurgo Completo + Ponte Portable-Host)

## DIRETRIZES GLOBAIS DE PRODUÇÃO (REGRAS ABSOLUTAS)
As regras a seguir são a lei máxima de desenvolvimento deste projeto. Elas não podem ser ignoradas ou alteradas pela IA.

1. **Higiene de Estrutura:** Mantenha a árvore de arquivos limpa. Arquivos temporários, pastas de build cache ou artefatos gerados (que não são estritamente necessários para rodar, compilar ou versionar o projeto) devem ser excluídos imediatamente após o uso.
2. **Atualização Diária Obrigatória:** Ao final de cada sessão/dia de trabalho, a IA DEVE atualizar a seção "HISTÓRICO DE INTERVENÇÕES" deste arquivo, relatando tudo o que foi implementado e ajustando o número da versão conforme a Matriz de 4 Eixos.
3. **Controle de Deploy Manual:** A IA NÃO tem autorização para compilar o executável final ou realizar `git push`/`commit` por conta própria. O processo de build e upload para o GitHub só deve ser executado quando o usuário solicitar explicitamente ("Suba para o GitHub" ou "Compile o projeto").
4. **Bloqueio de Dependências (Leveza):** O SysForge é um executável de pendrive. É ESTRITAMENTE PROIBIDO adicionar novas bibliotecas/pacotes (via `pip`) que aumentem o peso do `.exe` sem solicitar aprovação prévia do usuário. Priorize sempre APIs nativas do Windows e bibliotecas padrão do Python.
5. **Zero Código Fantasma:** O código final entregue não pode conter restos de debug (ex: `print()` soltos para testes de console), blocos de código antigo comentado, ou marcações `TODO`. O código de produção deve ser cirúrgico e finalizado.

## DIRETRIZ DE OPERAÇÃO PARA A IA (SISTEMA):
1. LER PRIMEIRO: Toda nova sessão de desenvolvimento deve começar com a leitura deste arquivo para entender o estado atual.
2. ATUALIZAR POR ÚLTIMO: Ao finalizar uma implementação solicitada, a IA DEVE registrar a mudança aqui e calcular a nova versão com base na Matriz de 4 Eixos.

## HISTÓRICO DE INTERVENÇÕES
### [Versão 5.0.3.0] - Data: 2026-06-03
- [Arquitetura/Segurança] Patch de Segurança no Updater: Injeção de roteamento 'Edition-Aware'. O motor agora distingue assets de download no GitHub, garantindo que a versão Portable receba apenas binários portáteis e o Host redirecione o usuário para o instalador oficial.
- [Sistema/Interface] Fim do expediente. Implementada ponte de download Host via Portable (`webbrowser.open` para GitHub Releases). Otimizações geométricas aplicadas na UI (Geometria Fixa, Spring Row, Sidebar Clusters). Higiene de `.gitignore` e remoção de artefatos stale.

### [Versão 5.0.2.4] - Data: 2026-06-03
- [Interface] Correção Geométrica (UI/UX): Substituição da expansão fluida por Geometria Fixa Estrita (`height=200`, `grid_propagate(False)`) nas abas Dashboard e Info. Implementação de Absorvedor de Espaço (Spring Row `weight=1`) para preservar o minimalismo e ancorar os cartões ao topo.

### [Versão 5.0.2.3] - Data: 2026-06-03
- [Interface] Refatoração Geométrica Master: Implementação de responsividade (`weight=1`, `sticky='nsew'`) nas views Dashboard e Info para eliminação de espaços vazios. Correção de ancoragem do badge na Sidebar (`sticky='sew'`) e redução de padding entre clusters.

### [Versão 5.0.2.2] - Data: 2026-06-03
- [Interface] Refatoração de Elite na Sidebar: Redução da geometria de botões (height=32), calibração tipográfica (Consolas 11 bold) e aplicação de agrupamento semântico (Clusters: Monitoramento, Engenharia, Pacotes, Base) com padding assimétrico para melhoria cognitiva (UI/UX).

### [Versão 5.0.2.1] - Data: 2026-06-03
- [Lógica/UX] Implementação do Consentimento Informado: O motor de expurgo agora detecta navegadores ativos via `psutil` e exibe um prompt de confirmação antes de abater os processos silenciosamente, protegendo o workflow do usuário.
- [Lógica/Matemática] Implementação de Auditoria de Lixo (Verbose Log) para rastreabilidade de arquivos e expansão do Dicionário Mestre com alvos profundos do Windows (Update, WER, Delivery Optimization).
- [Interface] Refatoração de UI/UX na Limpeza Personalizada: Implementação de Menus Accordion (Expansíveis), remoção do painel lateral e reposicionamento de botões na base.

### [Versão 5.0.2.0] - Data: 2026-06-03
- [Lógica/Interface] Implementação do Mapeamento Dinâmico de Ambiente no Motor de Expurgo. O sistema agora escaneia diretórios via `os.path.exists` para gerar opções de limpeza exclusivas aos softwares instalados (Opera GX, Brave, Firefox, etc).

### [Versão 5.0.1.0] - Data: 2026-06-03
- [Lógica/Interface] Refatoração do Motor de Expurgo para Dicionário Multicamadas. Implementação de seleção granular de sub-itens (Chrome/Sistema) com execução híbrida (Arquivos/Comandos).
- [Lógica/Interface] Início do Motor de Expurgo Profundo (Host-Exclusive). Lógica de caminhos e Interface granular criadas preservando o ecossistema existente.

### [Versão 5.0.0.0] - Data: 2026-06-03
- [Arquitetura] Refatoração para Arquitetura Monorepo com Feature Flags (Preparação para Dual-Build Portable/Host).
- [Build] Criação dos scripts de build em lote separados (`build_portable.bat` e `build_host.bat`) e centralização da variável `EDICAO_ATUAL` em `gear/build_config.py`.
- [Build] Otimização dos motores de compilação (.bat) com rotinas de auto-limpeza (PyInstaller cleanup).
- [Interface] Injeção dinâmica da flag `IS_PORTABLE` na barra lateral, ocultando recursos pesados (como App Manager e Softwares) na compilação leve.
- [Deploy] Implementação de Assinatura Visual Dinâmica, injeção de Manifesto UAC (--uac-admin) e criação do script de instalação corporativa (Inno Setup).

### [Versão 4.10.2.3] - Data: 2026-06-01
- [Interface] Correção de dimensionamento dinâmico na Sidebar: transferência de peso do grid da aba INFO para um row invisível (12), evitando o corte dos botões inferiores e badge de versão em telas/resoluções menores ou com escala.
- [Código] Análise e validação dos scripts mais recentes `triage_engine.py`, `blackbox.py`, `repair_protocols.py`. Nenhuma anomalia crítica foi encontrada no código pendente.

### [Versão 4.10.2.2] - Data: 2026-05-30
- [Matemática] Correção de Diagnóstico: Adicionado expurgo de logs (wevtutil) pós-cura para evitar falsos positivos no Índice de Integridade (Amnésia de Sistema).

### [Versão 4.10.1.2] - Data: 2026-05-30
- [Interface] Implementação de Feedback Visual (Spinner Assíncrono) no Terminal de Operações para tarefas de alto custo computacional da Autocura.
- [Lógica] Injeção de segurança: Protocolo Guarda-Chuva acoplado como Gatilho Zero do Motor de Autocura.

### [Versão 3.10.1.1] - Data: 2026-05-30
- [Lógica] Implementação do backend de Autocura (`gear/repair_protocols.py`) com subprocessos invisíveis para expurgo de rede, aniquilação de cache de update e reparo de kernel (DISM/SFC).
- [Matemática] Refinamento do Motor de Triage para consultar os eventos do Windows via `FilterHashtable` do PowerShell, garantindo leitura cirúrgica e indexação matemática hiper-precisa dos últimos 150 erros/alertas do log 'System'.
- [Lógica] Integração de botão "Autocura Inteligente" na Matriz de Intervenção, lendo os eixos matemáticos de anomalia (Rede/Update/Kernel) e despachando threads de cura silenciosas sob demanda.
- [Interface] Restruturação da área do Terminal de Operações para recuperar estabilidade visual após aplicação de limites de altura.

### [Versão 2.9.1.1] - Data: 2026-05-30
- [Lógica] Implementação da Auditoria Caixa Preta (`blackbox.py`) executada no startup silenciosamente para coletar telemetria em base local (`M-LABS-<HOSTNAME>-snapshot.json`).
- [Matemática] Adição do Motor de Triage via análise matemática de EventLogs do Windows, convertendo adivinhação em diagnóstico reativo.
- [Interface] Injeção de Telemetria no HUD em tempo real, monitorando sinais vitais com alerta visual (>95% crítico).
- [Interface] Execução e padronização da Regra Global de restrição visual, convertendo `_build_info` para `CTkFrame` fixo, extinguindo o scrollbar desnecessário e honrando o bloqueio rigoroso.

### [Versão 2.8.0.2] - Data: 2026-05-30
- [Correção/Deploy] Correção da compilação PyInstaller (`SysForge.spec`) para incluir `icon.ico`, `icon.png` e `logo_mlabs.png` nos dados de build em runtime e definição do ícone base do executável gerado.

### [Versão 2.8.0.1] - Data: 2026-05-30
- [Lógica/Interface] Implementação do Módulo de Gerenciamento Granular UWP (Desinstalação e Reparo Cirúrgico).

### [Versão 2.7.0.0] - Data: 2026-05-30
- [Lógica] Implementado Shadow Updater via Ghost Rename (Imunidade AV).
- [Interface] Adicionada trava geométrica global (center_window) para inicialização de janelas.
- [Matemática] Adicionado protocolo de idempotência na aplicação de Tweaks do Registro.
- [Interface] Refatoração do container de operações para um CTkFrame compacto, sem scroll e perfeitamente ajustado na geometria principal.
- [Matemática] Correção no mapeamento da string de build para detecção correta e isolada do Windows 11 no motor de informações do sistema.
- [Interface] Adição e refatoração do botão 'APLICAR TWEAKS' na aba Windows Tweaks via CTkScrollableFrame.
