# SYSFORGE - MATRIZ DE RASTREAMENTO (TIMELINE)
**Status Atual:** ATIVO
**Versão Atual:** 2.7.0.0 (Considerando as refatorações arquiteturais recentes)

## DIRETRIZ DE OPERAÇÃO PARA A IA (SISTEMA):
1. LER PRIMEIRO: Toda nova sessão de desenvolvimento deve começar com a leitura deste arquivo para entender o estado atual.
2. ATUALIZAR POR ÚLTIMO: Ao finalizar uma implementação solicitada, a IA DEVE registrar a mudança aqui e calcular a nova versão com base na Matriz de 4 Eixos.

## HISTÓRICO DE INTERVENÇÕES
### [Versão 2.7.0.0] - Data: 2026-05-30
- [Lógica] Implementado Shadow Updater via Ghost Rename (Imunidade AV).
- [Interface] Adicionada trava geométrica global (center_window) para inicialização de janelas.
- [Matemática] Adicionado protocolo de idempotência na aplicação de Tweaks do Registro.
- [Interface] Refatoração do container de operações para um CTkFrame compacto, sem scroll e perfeitamente ajustado na geometria principal.
- [Matemática] Correção no mapeamento da string de build para detecção correta e isolada do Windows 11 no motor de informações do sistema.
- [Interface] Adição e refatoração do botão 'APLICAR TWEAKS' na aba Windows Tweaks via CTkScrollableFrame.
