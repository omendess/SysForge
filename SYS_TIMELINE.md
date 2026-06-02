# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 4.10.2.3 (Correção de Layout Sidebar)

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
