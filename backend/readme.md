# ⚙️ Backend — Fluxo de Caixa

Módulo central de regras de negócio, persistência relacional e exposição de endpoints REST do **Sistema de Fluxo de Caixa**, construído com **FastAPI** e **SQLAlchemy**.

---

## 🎯 Responsabilidades do Backend

- Centralizar as regras de integridade financeira (cálculos de saldos, conciliações, poupanças e investimentos).
- Gerenciar o ciclo de vida de autenticação por tokens **JWT (JSON Web Tokens)** no padrão OAuth2 Password Bearer.
- Garantir o isolamento total de dados entre diferentes usuários.
- Cifrar e proteger dados sensíveis de usuários em conformidade com as diretrizes de privacidade.
- Fornecer documentação viva e interativa via **OpenAPI / Swagger UI**.

---

## 🧩 Componentes Principais

| Arquivo / Diretório | Responsabilidade Principal |
|---|---|
| [`api.py`](api.py) | Inicialização da aplicação FastAPI, configuração de CORS, registro de rotas e endpoint de saúde (`/health`). |
| [`database.py`](database.py) | Gerenciamento da engine SQLAlchemy com conexão em pool resiliente (`pool_pre_ping=True`, `pool_recycle=3600`) e gerador de sessões (`get_db`). |
| [`configuracao.py`](configuracao.py) | Carregamento desacoplado de configurações locais do `.env` e `%LOCALAPPDATA%`. |
| [`autenticacao.py`](autenticacao.py) | Criação, decodificação e validação de tokens JWT; injeção de dependência do usuário autenticado. |
| [`dados_sensiveis.py`](dados_sensiveis.py) | Algoritmos de cifragem Fernet para CPF/telefone e geração de índice cego HMAC-SHA256 para busca de duplicidades. |
| [`financeiro.py`](financeiro.py) | Regras matemáticas financeiras: cálculos agregados em SQL, validação de limites de poupança e consolidação de transferências. |
| [`models.py`](models.py) | Declaração dos modelos relacionais ORM (tabelas: `usuarios`, `contas_bancarias`, `fluxo_dinheiro`, `calculos_financeiros`, `metas_financeiras`, `tentativas_login`). |
| [`esquema.py`](esquema.py) | Modelos Pydantic v2 para validação rigorosa de entrada (Payloads) e serialização segura de saída (Responses). |
| [`rotasdeapi/`](rotasdeapi/) | Módulos de endpoints REST segmentados por domínio (`usuario.py`, `conta_bancaria.py`, `fluxo_dinheiro.py`, etc.). |
| [`seguranca/`](seguranca/) | Hashing e verificação de senhas com algoritmo Argon2/Bcrypt através do `pwdlib`. |
| [`tests/`](tests/) | Bateria abrangente de testes automatizados com SQLite em memória. |

---

## 🏗️ Padrões de Arquitetura

### 1. Injeção de Dependências
As rotas da API recebem suas dependências de forma declarativa pelo FastAPI:
- `db: Session = Depends(get_db)` garante uma sessão de banco aberta e fechada deterministicamente por requisição.
- `usuario_atual: Usuario = Depends(obter_usuario_logado)` garante que a rota só seja acessível por usuários com token JWT válido, isolando os dados de cada conta.

### 2. Resiliência de Conexão com o Banco
Em [database.py](database.py), o pool de conexões com o MySQL é configurado com:
- `pool_pre_ping=True`: Testa a validade da conexão antes de entregá-la à requisição, evitando falhas silenciosas de timeout ("MySQL server has gone away").
- `pool_recycle=3600`: Recicla periodicamente conexões antigas para respeitar os limites de inatividade do servidor MySQL.

### 3. Criptografia de Dados em Repouso
- **CPF e Telefone:** Cifrados com a chave simétrica `CPF_ENCRYPTION_KEY` antes de qualquer gravação no banco de dados.
- **Índice HMAC:** O CPF recebe hash HMAC com chave derivada e é armazenado na coluna `cpf_indice` com restrição `UNIQUE`, impedindo cadastros duplicados sem expor o CPF em texto puro.

---

## 🚀 Como Executar o Backend

### Via Ponto de Entrada Raiz (Recomendado)
```powershell
python main.py
```

### Via Uvicorn Direto
```powershell
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

Acesse a documentação interativa em:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Status Operacional:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
