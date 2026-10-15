# ⚙️ Backend — Fluxo de Caixa

Este backend foi desenvolvido para gerenciar o sistema financeiro do projeto com uma API REST em FastAPI. Ele conecta ao banco de dados MySQL por meio do SQLAlchemy, valida dados com Pydantic e organiza a lógica em módulos específicos para usuários, contas, movimentações, cálculos e segurança.

As rotas financeiras exigem autenticação JWT e limitam os dados acessíveis ao usuário autenticado.

---

## 🎯 Objetivo

O backend tem como objetivo centralizar a regra de negócio do sistema financeiro, com foco em:

- cadastro e consulta de usuários;
- controle de contas bancárias;
- registro de movimentações financeiras;
- cálculo de saldos e resumos por período;
- gestão de metas financeiras;
- segurança na persistência de senhas.

---

## 🧰 Stack

- Python
- FastAPI
- SQLAlchemy
- MySQL
- Pydantic
- Uvicorn
- pwdlib
- PyJWT
- Alembic

---

## 📁 Estrutura atual

```text
backend/
├── api.py
├── autenticacao.py
├── configuracao.py
├── dados_sensiveis.py
├── database.py
├── financeiro.py
├── esquema.py
├── models.py
├── readme.md
├── tests/
├── seguranca/
│   ├── __init__.py
│   ├── seguranca.py
│   └── readme.md
└── rotasdeapi/
    ├── __init__.py
    ├── usuario.py
    ├── conta_bancaria.py
    ├── fluxo_dinheiro.py
    ├── calculo_financeiro.py
    ├── meta_financeira.py
    └── readme.md
```

As migrações e a configuração Alembic ficam em `../banco de dados/`, junto
com os demais arquivos do banco.

---

## 🧩 Componentes principais

### `api.py`
Inicializa a aplicação FastAPI e registra todos os routers da API.

### `database.py`
Responsável pela configuração da engine, sessão do banco e conexão com o MySQL. A aplicação informa claramente se `DATABASE_URL` estiver ausente.

### `autenticacao.py`
Emite e valida JWT assinados com a variável de ambiente `JWT_SECRET_KEY`.

### `financeiro.py`
Calcula totais por meio de agregações SQL e reconstrói os saldos, incluindo as duas pontas das transferências.

### `models.py`
Define os modelos ORM das entidades do sistema: usuários, contas, categorias,
fluxo, cálculos e metas. O telefone opcional do usuário é armazenado cifrado.

### `esquema.py`
Contém os schemas de entrada e saída usados pela API com validação do Pydantic.

### `rotasdeapi/`
Agrupa os endpoints organizados por recurso:

- `usuario.py`
- `conta_bancaria.py`
- `fluxo_dinheiro.py`
- `calculo_financeiro.py`
- `meta_financeira.py`

### `seguranca/`
Módulo dedicado ao hash e verificação de senha.

O cadastro público `POST /usuarios/` recebe nome, CPF, e-mail, senha e
telefone opcional. O CPF precisa conter 11 dígitos ASCII e é validado antes
das funções de cifragem e indexação. O telefone é cifrado no banco com a mesma chave Fernet
`CPF_ENCRYPTION_KEY` usada para os CPFs. A revisão Alembic
`adicionar_telefone_usuario` deve estar aplicada antes de iniciar a API com
este campo.

---

## 🔄 Fluxo da aplicação

```text
Requisição HTTP
      │
      ▼
  Router da API
      │
      ▼
  Regras de negócio (`financeiro.py`)
      │
      ▼
  SQLAlchemy ORM
      │
      ▼
     MySQL
```

---

## ▶️ Como executar

Execute a partir da raiz do repositório:

```powershell
python main.py
```

Configure `DATABASE_URL`, `JWT_SECRET_KEY` e `CPF_ENCRYPTION_KEY` em `.env`
local ou em `%LOCALAPPDATA%\fluxo_caixa\secrets.env`. Consulte o README da
raiz para gerar chaves. Use uma base exclusiva de desenvolvimento e dados
fictícios. O servidor padrão escuta somente em `127.0.0.1:8000`.

O login está disponível em `POST /login`; nas demais rotas, envie o JWT no
cabeçalho `Authorization: Bearer <access_token>`. A validade é configurada por
`ACCESS_TOKEN_EXPIRE_MINUTES` (padrão: 60 minutos).

Para criar ou atualizar o esquema:

```bash
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

Documentação da API:

```text
http://127.0.0.1:8000/docs
```

Os testes automatizados usam SQLite em memória e podem ser executados na raiz
com `python -m pytest -q`; não usam a base configurada para a API. A suíte
padrão exclui testes de concorrência MySQL; veja
`backend/tests/README.md` para executá-los, de forma opt-in, em um schema
descartável dedicado.

---

## 🧠 Módulos do sistema

### Usuários
- cadastro;
- listagem;
- consulta por ID;
- exclusão;
- validação de dados, como CPF e e-mail.

### Contas bancárias
- criação e atualização;
- associação ao usuário;
- controle de saldo atual;
- ativação/desativação.

### Fluxo de dinheiro
- entradas;
- saídas;
- transferências;
- ajustes de saldo assinados;
- investimentos;
- registros com data, categoria e observação.

### Cálculos financeiros
- saldo inicial;
- total de entradas;
- total de saídas;
- total de investimentos;
- totais separados de transferências recebidas/enviadas e ajustes;
- saldo final.

### Metas financeiras
- criação de metas;
- acompanhamento de progresso;
- respostas incluem percentual atingido e valor restante;
- atualização e exclusão.

### Relatórios financeiros
- relatórios por conta em períodos diário, semanal, mensal ou anual;
- saldo inicial e final, entradas, saídas, investimentos, transferências e ajustes;
- criação, listagem, consulta e exclusão de cálculos salvos pela API.

---

## 🔐 Segurança

O módulo `seguranca` protege as senhas antes do armazenamento. O login emite JWT; as respostas de usuário omitem o CPF; e as rotas filtram as consultas pelo usuário autenticado. O CPF é cifrado com Fernet usando `CPF_ENCRYPTION_KEY`, separada da chave JWT. Um HMAC com chave derivada permite detectar CPFs duplicados sem armazená-los em texto puro. Mantenha a chave CPF em um gestor de segredos e em backup protegido: sem ela, os CPFs existentes não podem ser recuperados. Não troque essa chave sem um procedimento de recifragem. No Windows, `configuracao.py` carrega primeiro `%LOCALAPPDATA%\fluxo_caixa\secrets.env`; evite guardar credenciais no `.env` da pasta do projeto se ela for sincronizada.

Recursos pertencentes a outro usuário respondem 404 em operações de leitura,
edição e exclusão. Login e cadastro limitam tentativas por endereço IP; o login
também limita tentativas por e-mail. Após cinco tentativas em 15 minutos, a
chave de controle recebe bloqueio temporário e a API responde HTTP 429 com
`Retry-After`. O banco guarda hashes das chaves, não o IP nem o e-mail usados
para agrupá-las. Falhas de login retornam a mesma mensagem para conta
inexistente ou senha incorreta.

O CORS aceita somente `http://app.fluxocaixa`, `http://app.fluxocaixa:5173`
e `http://127.0.0.1:5173`, com métodos e cabeçalhos da API explicitamente
permitidos. Para a origem `app.fluxocaixa`, configure esse nome para
`127.0.0.1` no arquivo `hosts` do Windows.

## 💳 Regras de saldo e transferências

- O saldo não pode ser editado pelo endpoint de atualização da conta; ajustes devem ser lançados como movimentações.
- Ajustes de saldo são lançamentos do tipo `ajuste`; use valor positivo para aumentar e negativo para reduzir. Eles aparecem em `total_ajustes`, não como renda ou gasto.
- Contas correntes podem ter saldo negativo. Contas poupança e investimento não podem.
- Uma transferência entre contas do mesmo usuário cria lançamentos vinculados para origem e destino.
- Os resumos exibem transferências recebidas/enviadas separadamente, sem classificá-las como renda/gasto; o saldo final considera esses valores.
- As categorias de movimentação são uma lista fixa em português sem acentos: `alimentacao`, `ajuste`, `compras`, `contas`, `educacao`, `freelance`, `impostos`, `investimento`, `lazer`, `moradia`, `outros`, `salario`, `saude`, `transporte`, `transferencia` e `vendas`. `ajuste` e `transferencia` são reservadas a seus respectivos tipos.
- Uma meta cancelada permanece cancelada mesmo que o valor atual alcance o objetivo.
- Transferências são excluídas como um par. Uma conta com transferências precisa ter os lançamentos removidos antes de ser excluída.
- Após cinco falhas de login do mesmo endereço IP em 15 minutos, novas tentativas desse IP recebem HTTP 429 durante a janela de bloqueio. O banco guarda um hash do endereço, não o IP em texto.

## 🧪 Testes e migrações

Execute os testes com `python -m pytest -q`. `pytest.ini` configura os imports
do backend e os testes usam SQLite temporário. `backend/tests/conftest.py`
define explicitamente o banco e as chaves de teste; a suíte não se conecta ao
MySQL configurado para executar a aplicação. Os testes cobrem cadastro,
telefone opcional cifrado, login/JWT, contas, movimentações, saldo, isolamento,
metas, relatórios e proteção de dados, inclusive rejeição de CPFs com
algarismos Unicode.

O Alembic mantém o esquema versionado em `../banco de dados/migrations/`.
Depois da revisão `proteger_cpf`, a revisão
`adicionar_telefone_usuario` adiciona a coluna opcional usada pelo cadastro.
Confirme o destino antes de aplicar revisões; os dumps SQL em `banco de
dados/` são legados e podem conter `DROP TABLE`. Não os execute em bancos com
dados.

---

Os testes MySQL opt-in cobrem concorrência e bloqueios usando um schema
descartável. A aplicação continua voltada ao desenvolvimento local; HTTP sem
TLS e JWT em `sessionStorage` não são uma configuração de produção.
