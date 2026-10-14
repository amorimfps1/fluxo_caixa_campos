# Revisões Alembic

Os arquivos Python desta pasta descrevem, em ordem, as alterações versionadas no esquema do banco. Cada revisão declara uma função `upgrade()` e, quando possível, uma função `downgrade()`.

## Histórico atual

| Revisão | Descrição |
|---|---|
| `esquema_inicial` | Cria usuários, contas bancárias, movimentações, cálculos financeiros e metas. |
| `transferencias` | Relaciona as duas pontas de uma transferência e a conta contraparte. |
| `categorias_movimentacao` | Cria categorias fixas e normaliza movimentações existentes. |
| `ajustes_e_resumos` | Adiciona ajustes assinados, totais separados de transferências e normaliza categorias legadas para a lista fixa. |
| `limite_login` | Cria o armazenamento de tentativas de login para limitar falhas por endereço cliente. |
| `normalizar_schema` | Normaliza o esquema MySQL existente. |
| `proteger_cpf` | Cifra CPFs armazenados e cria índices HMAC para duplicatas. |
| `adicionar_telefone_usuario` | Adiciona telefone opcional cifrado ao cadastro. |

As dependências entre revisões são declaradas por `down_revision`. Os IDs das revisões antigas foram mantidos para preservar compatibilidade com bancos que já as aplicaram. Não renomeie ou remova revisões já aplicadas; crie uma nova revisão para mudanças futuras e revise o resultado antes de aplicá-la a dados existentes.

Os novos arquivos de revisão usam nomes descritivos em português. `alembic.ini` define `file_template = %%(slug)s`; para criar uma revisão com ID textual explícito, use por exemplo `alembic revision -m "limitar tentativas de login" --rev-id limite_login`. As operações de downgrade podem remover colunas ou tabelas, e a reversão do ajuste converte ajustes existentes em entradas/saídas. Faça backup e avalie os dados antes de reverter uma revisão.
