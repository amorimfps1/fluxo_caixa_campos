# Testes do backend

Esta pasta reúne testes automatizados das regras financeiras, validações e
endpoints da API. `conftest.py` fornece as fixtures compartilhadas; cada
arquivo `test_*.py` cobre uma área do sistema.

## Cobertura existente

- agregações de entradas, saídas e investimentos e resumo do período;
- transferência entre contas, reversão ao excluir, rejeição da mesma conta e
  atomicidade quando o saldo é insuficiente;
- precisão Decimal em entradas fracionárias, ajustes e saldos calculados;
- bloqueio de saídas ou ajustes negativos que deixariam saldo de poupança
  negativo, aceitando ajuste que zera o saldo e rejeitando excesso de um
  centavo sem persistência parcial;
- validação dos dígitos verificadores do CPF;
- rejeição de CPF com algarismos Unicode antes de qualquer operação de
  cifragem ou indexação;
- correspondência entre o tipo de cálculo e o intervalo informado;
- precisão decimal e validação de categorias fixas/reservadas;
- normalização de e-mail e categorias;
- ajustes assinados fora dos totais comuns;
- login, expiração de JWT, limites por IP/conta no login, limite por IP no
  cadastro e mensagens genéricas para credenciais inválidas;
- isolamento entre usuários em operações de leitura, criação, edição e
  exclusão de contas, movimentações e metas;
- fluxo integrado com `TestClient`: cadastro de duas contas, login, uso do
  JWT em rotas protegidas, validação de saldos e tentativas cruzadas que devem
  retornar 404;
- cadastro de usuário com telefone opcional, validação e cifragem do telefone
  armazenado.

Os testes usam um banco SQLite temporário em memória, ativam as chaves
estrangeiras e criam/removem o esquema para cada teste. O `conftest.py`
substitui explicitamente `DATABASE_URL` e usa chaves criptográficas dedicadas
ao ambiente de teste. Assim, a suíte não conecta ao banco nem assina tokens
com os segredos configurados para executar a API.

## Executar

Na raiz do repositório:

```bash
python -m pytest -q
```

Os testes não dependem do MySQL de desenvolvimento. A validação funcional em
SQLite não substitui teste de bloqueios concorrentes no MySQL: SQLite não
implementa o mesmo comportamento de `SELECT ... FOR UPDATE`. Testes manuais ou
de integração com MySQL devem usar uma base exclusiva de desenvolvimento e
dados fictícios; não execute migrações ou testes contra produção.

## Concorrência MySQL (opt-in)

`test_mysql_concorrencia.py` verifica saques simultâneos, transferências
cruzadas, conservação do saldo total, rollback após falha e um controle
negativo sem `FOR UPDATE`. Esses testes não fazem parte da suíte padrão.

Crie um schema MySQL vazio e dedicado, com sufixo `_test` ou `_tests`, e um
usuário próprio com permissões restritas ao schema e permissões DDL para
Alembic. Não use a base de desenvolvimento `fluxo_caixa`, uma base com dados a
preservar ou produção. Na raiz do repositório, configure a URL no PowerShell e
execute:

```powershell
$env:TEST_MYSQL_URL = "mysql+pymysql://USUARIO:SENHA@127.0.0.1:3306/fluxo_caixa_test"
python -m pytest -m mysql -q
```

O fixture aplica `alembic upgrade head` ao schema dedicado. Se a variável não
estiver definida, os testes são ignorados sem executar migrações. Não coloque a
URL nem suas credenciais em arquivos versionados.
