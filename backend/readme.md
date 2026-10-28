# ⚙️ Backend — Fluxo de Caixa

> ⚡ **API em Produção (Render):** [https://fluxo-caixa-cuq1.onrender.com](https://fluxo-caixa-cuq1.onrender.com)  
> 📖 **Swagger UI:** [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs)  
> 🩺 **Healthcheck:** [https://fluxo-caixa-cuq1.onrender.com/health](https://fluxo-caixa-cuq1.onrender.com/health)

Módulo central de regras de negócio, criptografia, persistência relacional e exposição de endpoints REST do **Sistema de Fluxo de Caixa**, construído com **FastAPI** e **SQLAlchemy 2.x**.

---

## 🎯 Responsabilidades do Backend

- **Integridade Contábil Rigorosa:** Aritmética financeira com `Decimal(12, 2)` para saldos consolidados, aportes de investimentos, conciliações, poupanças e transferências atômicas vinculadas (`SELECT ... FOR UPDATE`).
- **Autenticação & Controle de Acesso:** Padrão **OAuth2 Password Bearer** com tokens **JWT (HS256)**, controle de taxa (*rate limiting*) anti-força bruta por IP e conta.
- **Proteção e Privacidade LGPD em Repouso:** Cifragem simétrica com **Fernet (AES-128-CBC + HMAC-SHA256)** para CPF e telefone; verificação de unicidade por **Blind Index HMAC-SHA256** sem expor dados sensíveis.
- **Segurança de Credenciais:** Hashing de senhas moderno via `pwdlib` com **Argon2id** e fallback para Bcrypt com tempo de comparação constante.
- **Banco de Dados Híbrido & Alta Disponibilidade:** Compatibilidade nativa com **Supabase (PostgreSQL 15+ com Connection Pooler PgBouncer porta 6543 e SSL obrigatório)** e **MySQL 8 / TiDB Cloud Serverless** com TLS nativo.
- **Serviços Transacionais de Notificação:** Envio de e-mails via SMTP com STARTTLS para confirmação de cadastro, boas-vindas e recuperação de senha.

---

## 🧩 Componentes do Módulo

| Arquivo / Diretório | Responsabilidade Principal |
|---|---|
| [`api.py`](api.py) | Inicialização da aplicação FastAPI, validação estrita de `APP_ENV`, política de CORS e rotas raiz (`/` e `/health`). |
| [`database.py`](database.py) | Normalizador automático de `DATABASE_URL` (PostgreSQL / Supabase / MySQL), injeção de SSLContext nativo e pool SQLAlchemy (`pool_pre_ping=True`, `pool_recycle=3600`). |
| [`configuracao.py`](configuracao.py) | Carregamento seguro e centralizado de variáveis de ambiente a partir do `.env` ou do ambiente do servidor. |
| [`autenticacao.py`](autenticacao.py) | Emissão, decodificação e validação de tokens JWT; injeção de dependência `obter_usuario_logado`. |
| [`dados_sensiveis.py`](dados_sensiveis.py) | Cifragem Fernet (`CPF_ENCRYPTION_KEY`) e geração de índice cego HMAC-SHA256 (`cpf_indice`). |
| [`financeiro.py`](financeiro.py) | Motor contábil: recálculo de saldos, débitos de aportes de investimentos, validação de saldo disponível e consolidação de relatórios. |
| [`models.py`](models.py) | 10 entidades ORM SQLAlchemy (`Usuario`, `ContaBancaria`, `FluxoDinheiro`, `CategoriaMovimentacao`, `CalculoFinanceiro`, `MetaFinanceira`, `TentativaLogin`, `Orcamento`, `PreferenciaAlerta`, `AlertaLido`). |
| [`esquema.py`](esquema.py) | Schemas Pydantic v2 com validações de CPF algorítmico, senha forte, tipos de conta e contratos de entrada/saída. |
| [`rotasdeapi/`](rotasdeapi/) | Controladores REST modulares (`usuario.py`, `conta_bancaria.py`, `fluxo_dinheiro.py`, `calculo_financeiro.py`, `meta_financeira.py`, `orcamentos_alertas.py`). |
| [`servicos/`](servicos/) | Serviços auxiliares da aplicação, incluindo envio de e-mails transacionais via SMTP em [`servicos/email.py`](servicos/email.py). |
| [`seguranca/`](seguranca/) | Hashing de senhas com `pwdlib` (Argon2id) e rotinas criptográficas defensivas. |
| [`tests/`](tests/) | Suíte completa com **80 testes automatizados** passando em SQLite em memória isolado e fixtures especializadas. |

---

## 🏗️ Destaques de Engenharia no Backend

### 1. Conexão Resiliente e Multi-Driver (`database.py`)
A função `normalizar_database_url` detecta automaticamente a tecnologia do banco configurada em `DATABASE_URL`:
- **PostgreSQL / Supabase:** Converte `postgres://` para `postgresql+psycopg2://` e configura parâmetros SSL exigidos pelos poolers em nuvem (`sslmode=require`).
- **MySQL / TiDB Cloud:** Converte `mysql://` para `mysql+pymysql://`, sanitiza caracteres especiais de credenciais via `urllib.parse.quote_plus` e instancia `ssl.create_default_context()` diretamente no driver TLS.
- **SQLite (Testes):** Conexão rápida em memória para isolamento total dos testes sem dependências externas.

### 2. Política de CORS Estrita por Ambiente (`api.py`)
- **`APP_ENV=development`:** Permite origens locais (`127.0.0.1:5500`, `127.0.0.1:5173`) para desenvolvimento ágil.
- **`APP_ENV=production`:** Exige que `CORS_ORIGINS` seja explicitamente configurada (rejeita curingas `*`), liberando exclusivamente o domínio oficial de produção (`https://fluxo-caixa-coral-two.vercel.app`).

### 3. Gestão Integrada de Investimentos (`rotasdeapi/fluxo_dinheiro.py`)
- Ao registrar um lançamento do tipo `investimento`, o motor contábil debita automaticamente o valor da conta bancária de origem e atualiza o patrimônio global do usuário, suportando tanto **Renda Fixa** (Poupança, CDB, LCI/LCA, Tesouro Direto, Fundos) quanto **Renda Variável** (Ações, ETFs, FIIs, Subscrições).
