# Migrações do banco

Esta pasta contém a configuração e o histórico oficial das migrações Alembic do projeto. O código das revisões fica em `versions/`; os modelos e a conexão necessários para executá-las permanecem no `backend/`.

## Arquivos

- `env.py` carrega a URL de conexão configurada em `DATABASE_URL`, importa os modelos do projeto para obter os metadados SQLAlchemy e executa as revisões em modo online ou offline.
- `versions/` contém as revisões ordenadas por dependência: esquema inicial;
  transferências; categorias fixas/normalizadas; ajustes e resumos; limite de
  tentativas de login; normalização MySQL; cifragem de CPF; e telefone
  opcional cifrado.

Os arquivos de revisão têm nomes descritivos em português; os IDs usados pelo
Alembic estão declarados nos próprios arquivos e ligados por `down_revision`.
Esses IDs são parte do histórico dos bancos: não renomeie nem remova revisões
já aplicadas. Consulte o histórico em
[versions/README.md](versions/README.md). Novas revisões usam o slug definido
em `file_template = %%(slug)s`.

## Comandos

Execute na raiz do repositório:

```bash
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

Para consultar a revisão atualmente aplicada:

```bash
python -m alembic -c "banco de dados/alembic.ini" current
```

`DATABASE_URL` deve estar configurada antes da execução. A migração
`proteger_cpf` também exige `CPF_ENCRYPTION_KEY` e cifra os CPFs existentes;
confirme que essa chave é a correta e mantenha um backup seguro dela. Antes de
aplicar qualquer revisão, confirme que `DATABASE_URL` aponta para a base
correta. Em banco existente, faça backup e compare o esquema com as revisões
antes de usar `stamp` ou aplicar atualizações. A revisão de proteção do CPF
bloqueia downgrade para evitar regravar dados em texto puro. Nunca execute
comandos Alembic contra produção sem revisão, backup e aprovação explícita.
