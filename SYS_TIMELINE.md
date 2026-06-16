# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 1.0.1 (Teste de Auto-Updater)

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
- [Deploy] Implementação de Dynamic Naming no pipeline de build. O builder.py e o Inno Setup agora carimbam o artefato final com a versão correspondente (ex: v1.0.1) de forma automatizada via extração da constante global. Limpeza de batch scripts adaptada com wildcards (`v*.exe`).
- [Arquitetura/Sistema] Bump de versão para v1.0.1. Preparação dos artefatos para o teste de validação de campo do Auto-Updater e roteamento da API.

### [Versão 1.0.0] - Data: 2026-06-03
- [Arquitetura/Sistema] Hotfix no Pipeline de Build: Transição de 'Destructive Cleanup' (`rmdir dist`) para Limpeza Seletiva (`del target.exe`) nos orquestradores batch, garantindo a coexistência dos artefatos Host e Portable.
- [Arquitetura/Interface] Refatoração Global de Fase 1 (v1.0.0): Injeção do Protocolo de Higiene Automática (.bat com `del /q *.exe`), calibração do Grid de UI (Sidebar rígida de 220px, botões 36px com raio 2, margens 20px no Dashboard/Info), e injeção de logs de batalha no motor OTA Updater (`gear/updater.py`). Re-verificado separação correta dos binários via `--name`.
- [Arquitetura/Sistema] Auditoria de Pipeline de Build concluída. Injetada ancoragem UAC (`cd /d "%~dp0"`) nos scripts batch e revisada a segurança da rotina de cleanup para proteger artefatos vitais do PyInstaller. Correção de caminho de ícone do Inno Setup restabelecida à raiz.
- [Deploy] Inno Setup modernizado (WizardStyle=modern, Compressão LZMA2 Ultra64, bloqueio x64).
- [Interface] Implementação bidirecional da Ponte Host-Portable na Sidebar.
- [Build] Scripts de compilação injetados com destruição recursiva da pasta build para higiene automatizada de cache.
