# Fluxo de Caixa

Aplicação de controle financeiro com API FastAPI, banco MySQL, interface web
estática e testes automatizados.

## Funcionalidades


### Funcionalidades da API

- Cadastro com nome, CPF, e-mail, senha e telefone opcional; Gmail pode ser
  usado como e-mail comum (sem autenticação Google OAuth).
- Contas bancárias e movimentações isoladas por usuário.
- Entradas, saídas, investimentos, transferências e ajustes.
- Cálculos financeiros: rotas da API existem, mas ainda não têm tela na
  interface.
- Metas: rotas da API existem, mas ainda não têm tela na interface.
- Relatórios: ainda não existem rotas dedicadas na API nem tela na interface.
- Senhas com hash; CPF e telefone cifrados; limites de tentativas no login e
  no cadastro.

### Funcionalidades da interface

- Dashboard web com contas e movimentações reais da API.
- Gráficos: apenas espaços reservados (placeholders), sem dados conectados à
  API.
- Itens de menu "Categorias", "Investimentos" e "Relatórios": apenas espaços
  reservados, sem tela implementada.


## Estrutura

```text
.
├── backend/                    # API, regras, segurança e testes
│   ├── rotasdeapi/              # Endpoints por recurso
│   ├── seguranca/               # Hash e verificação de senha
│   └── tests/                   # SQLite; concorrência MySQL opt-in
├── banco de dados/
│   ├── migrations/              # Histórico oficial Alembic
│   └── *.sql                    # Dumps legados; não executar
├── frontend/
│   ├── login.html
│   ├── index.html               # Dashboard
│   ├── css/
│   └── js/
├── .env.example                 # Modelo sem segredos reais
├── main.py                      # Entrada local da API
├── requirements.txt
└── pytest.ini
```

Veja [ESTRUTURA.md](ESTRUTURA.md) e os READMEs de
[backend](backend/readme.md), [testes](backend/tests/README.md),
[frontend](frontend/README.md) e [banco de dados](banco%20de%20dados/readme.md).

## Pré-requisitos

- Python 3.10 ou superior.
- MySQL para executar a aplicação e as migrações.
- PowerShell no Windows para os exemplos abaixo.

## Configuração local segura

Crie e ative um ambiente virtual, instale as dependências e copie o modelo de
configuração:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edite `.env` localmente: configure as chaves e uma base MySQL exclusiva para
desenvolvimento, vazia ou descartável. Nunca configure desenvolvimento,
migrações ou testes para apontar à base de produção. `.env` e ambientes virtuais
são ignorados pelo Git.

No Windows, `%LOCALAPPDATA%\fluxo_caixa\secrets.env` tem precedência sobre o
arquivo `.env` da raiz. Verifique qual configuração local será usada antes de
iniciar a API.

### Gerar chaves para produção

Gere cada chave diretamente no ambiente de destino e nunca compartilhe valores
entre ambientes:

```powershell
# Chave JWT (assinatura do token; mínimo 32 caracteres)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Chave Fernet (cifragem de CPF e telefone)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Use o primeiro valor para `JWT_SECRET_KEY` e o segundo para `CPF_ENCRYPTION_KEY`.
Defina `APP_ENV=development` ou `APP_ENV=production` (variável obrigatória).
Em produção, preencha `CORS_ORIGINS` somente com as origens confiáveis do frontend.

Faça backup seguro da chave Fernet: perdê-la impede recuperar CPFs e telefones
cifrados. Não troque essa chave sem um procedimento de recifragem dos dados
já armazenados. Nunca versão `.env`, tokens, chaves ou segredos.

## Banco de dados

Confirme que `DATABASE_URL` aponta para a base de desenvolvimento antes de
consultar ou alterar o esquema. Para uma base nova:

```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

Faça backup e revise o destino antes de aplicar migrações a qualquer base com
dados. Não use `stamp` sem confirmar o esquema. Os arquivos `.sql` são dumps
legados e podem conter comandos destrutivos; não os execute em bancos ativos.

## Executar localmente

Na raiz, inicie a API:

```powershell
python main.py
```

Ela escuta apenas em `127.0.0.1:8000`. Documentação:

- API: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>

Em outro terminal, inicie o frontend seguindo
[frontend/README.md](frontend/README.md). Para login manual, use apenas uma
conta fictícia de desenvolvimento. Para abrir sem informar uma porta, sirva o
frontend na porta 80 e use `http://app.fluxocaixa/login.html`; esse nome
precisa apontar para `127.0.0.1` no arquivo `hosts` do Windows. Como
alternativa, use a porta 5173 e abra
`http://127.0.0.1:5173/login.html` ou
`http://app.fluxocaixa:5173/login.html`.

## Testes automatizados

Execute na raiz:

```powershell
python -m pytest -q
```

Os testes substituem explicitamente `DATABASE_URL` por SQLite em memória e
usam chaves dedicadas aos testes. Não conectam ao MySQL configurado para a
API. A cobertura inclui regras financeiras, autenticação, isolamento entre
usuários, proteção de dados, CORS e rotas.

Os testes unitários/funcionais em SQLite não validam a concorrência específica
do MySQL nem substituem um teste manual ponta a ponta. Faça testes de
integração somente com uma base local separada e dados fictícios.
Os testes de cadastro também confirmam que CPFs com algarismos Unicode são
rejeitados antes da cifragem; o formato aceito usa 11 dígitos ASCII.

### Concorrência no MySQL

Os testes MySQL são opt-in e usam migrações Alembic. Crie primeiro um schema
vazio e exclusivo para testes (nome terminado em `_test` ou `_tests`) e um
usuário MySQL dedicado, com permissões somente nesse schema e permissões DDL
necessárias às migrações. Não use a base `fluxo_caixa` de desenvolvimento,
qualquer base com dados que queira preservar ou produção.

No PowerShell, configure a URL apenas no terminal atual; não a grave em
arquivos versionados:

```powershell
$env:TEST_MYSQL_URL = "mysql+pymysql://USUARIO:SENHA@127.0.0.1:3306/fluxo_caixa_test"
python -m pytest -m mysql -q
```

O comando aplica `alembic upgrade head` ao schema apontado antes dos testes.
Use credenciais locais, não compartilhe a URL e confirme cuidadosamente o nome
do schema antes de executar. Sem `TEST_MYSQL_URL`, os testes MySQL são
ignorados. A suíte padrão `python -m pytest -q` sempre os exclui.

## Segurança e limites

- A allowlist CORS local contém somente `http://app.fluxocaixa`,
  `http://app.fluxocaixa:5173` e `http://127.0.0.1:5173`. O frontend usa a API
  em `http://127.0.0.1:8000`. `APP_ENV` é obrigatória (`development` ou
  `production`). Em produção, preencha `CORS_ORIGINS` somente com as origens
  confiáveis.
- Antes de iniciar a API com o campo telefone, aplique a revisão
  `adicionar_telefone_usuario` somente à base local de desenvolvimento.
- A API local fica vinculada a loopback; não altere para `0.0.0.0` em uma rede
  não confiável.
- Frontend e API usam HTTP sem TLS e JWT em `sessionStorage`; são apenas para
  desenvolvimento local, não para produção.
- Nunca versão `.env`, tokens, chaves, dados pessoais, dados bancários ou
  dumps de bancos reais.

### Pendências para produção (não implementadas)

- **Armazenamento do token:** o JWT é mantido em `sessionStorage` pelo frontend.
  Ainda não foi decidido se o token deve continuar em `sessionStorage` ou migrar
  para um cookie `HttpOnly`. Essa mudança não será feita sem consulta prévia.
- **HTTPS:** a aplicação roda em HTTP sem TLS. Para produção é necessário
  configurar HTTPS (certificado TLS e redirecionamento de HTTP para HTTPS).
  Ainda não há implementação nessa direção.

## Documentação adicional

- [Guia da estrutura](ESTRUTURA.md)
- [API e regras do backend](backend/readme.md)
- [Rotas](backend/rotasdeapi/readme.md)
- [Segurança de senhas](backend/seguranca/readme.md)
- [Testes](backend/tests/README.md)
- [Frontend](frontend/README.md)
- [Banco de dados](banco%20de%20dados/readme.md)
- [Migrações](banco%20de%20dados/migrations/README.md)
