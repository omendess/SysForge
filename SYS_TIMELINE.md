# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 1.0.1 (Validação OTA Update)

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
### [Versão 1.0.1] - Data: 2026-06-03
- [Arquitetura/Sistema] Auditoria de Pipeline de Build concluída. Injetada ancoragem UAC (`cd /d "%~dp0"`) nos scripts batch e revisada a segurança da rotina de cleanup para proteger artefatos vitais do PyInstaller. Correção de caminho de ícone do Inno Setup restabelecida à raiz.
- [Arquitetura/Sistema] Execução de Higiene Profunda (build/dist/Output). Aplicação de Headers (User-Agent) na GitHub API para bypass de restrição. Implementação de Substring Match na busca de assets para suportar versionamento dinâmico no nome dos executáveis.
- [Arquitetura/Sistema] Bump para v1.0.1. Objetivo: Validação em produção do motor Auto-Updater Edition-Aware conectado à API do GitHub (Dummy Bump para forçar trigger de atualização).

### [Versão 1.0.0] - Data: 2026-06-03
- [Arquitetura/Sistema] Reboot de Arquitetura (Tábula Rasa). Limpeza absoluta de artefatos residuais e re-versionamento global para o Marco Zero (1.0.0) como Release Candidate.
- [Deploy] Inno Setup modernizado (WizardStyle=modern, Compressão LZMA2 Ultra64, bloqueio x64).
- [Interface] Implementação bidirecional da Ponte Host-Portable na Sidebar.
- [Build] Scripts de compilação injetados com destruição recursiva da pasta build para higiene automatizada de cache.
