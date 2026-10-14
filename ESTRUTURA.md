# Estrutura do projeto

Guia rápido dos diretórios, pontos de entrada e instruções locais. Os caminhos
foram mantidos para preservar imports Python, migrações existentes e links
entre os READMEs.

```text
fluxo_caixas/
├── backend/
│   ├── api.py                 # Aplicação FastAPI e CORS
│   ├── autenticacao.py        # Emissão e validação de JWT
│   ├── configuracao.py        # Carregamento de segredos locais
│   ├── dados_sensiveis.py     # Cifragem de CPF e índice HMAC
│   ├── database.py            # Engine e sessões SQLAlchemy
│   ├── financeiro.py          # Agregações e cálculos
│   ├── models.py              # Modelos ORM
│   ├── esquema.py             # Schemas de entrada e resposta
│   ├── rotasdeapi/            # Rotas por recurso
│   ├── seguranca/             # Hash e verificação de senhas
│   └── tests/                 # Testes isolados em SQLite
├── banco de dados/
│   ├── alembic.ini            # Configuração das migrações
│   ├── migrations/            # Histórico oficial do esquema
│   └── *.sql                  # Dumps legados; não executar em bancos ativos
├── frontend/
│   ├── login.html             # Formulário de autenticação
│   ├── cadastro.html          # Cadastro de usuário
│   ├── index.html             # Dashboard autenticado
│   ├── css/                   # Estilos
│   └── js/                    # Cliente da API, cadastro, login e dashboard
├── main.py                    # Entrada recomendada da API
├── requirements.txt           # Dependências do backend
├── pytest.ini                 # Descoberta dos testes
└── .env.example               # Modelo sem credenciais reais
```

## Fluxo de execução

- A API é iniciada a partir da raiz com `python main.py` e escuta somente em
  `127.0.0.1:8000` por padrão.
- O frontend é servido separadamente; os comandos e origens CORS autorizadas
  estão em [frontend/README.md](frontend/README.md).
- As migrações oficiais são executadas por Alembic usando
  `banco de dados/alembic.ini`.
- O cadastro armazena telefone opcional cifrado; aplique a revisão
  `adicionar_telefone_usuario` à base local antes de subir a versão atual da
  API.
- Os testes automatizados usam fixtures em memória e podem ser executados com
  `python -m pytest -q`; veja [backend/tests/README.md](backend/tests/README.md).

## Segredos e dados locais

`.env`, `secrets.env`, bancos locais, ambientes virtuais e artefatos de teste
são ignorados pelo Git. O arquivo `.env.example` contém somente valores de
exemplo. Nunca coloque chaves ou dados bancários reais em arquivos versionados
ou em commits.
