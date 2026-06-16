# DNA DO SISTEMA - Controle de Feature Flags (Arquitetura Monorepo)

# Altere esta variável para "HOST" para gerar a versão completa instalada.
# Mantenha como "PORTABLE" para gerar a versão leve de pendrive.
EDICAO_ATUAL = "HOST"

# Variáveis booleanas derivadas para uso interno no código
IS_PORTABLE = (EDICAO_ATUAL == "PORTABLE")
IS_HOST = (EDICAO_ATUAL == "HOST")
