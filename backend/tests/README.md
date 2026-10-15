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
