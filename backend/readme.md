# ⚙️ Backend — Fluxo de Caixa

> ⚡ **API em Produção (Render):** [https://fluxo-caixa-cuq1.onrender.com](https://fluxo-caixa-cuq1.onrender.com)  
> 📖 **Swagger UI:** [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs)

Módulo central de regras de negócio, criptografia, persistência relacional e exposição de endpoints REST do **Sistema de Fluxo de Caixa**, construído com **FastAPI** e **SQLAlchemy 2.x**.

---

## 🎯 Responsabilidades do Backend

- Centralizar a integridade contábil com precisão `Decimal(12, 2)` (saldos consolidados, conciliações, poupanças, investimentos e transferências atômicas).
- Gerenciar autenticação **OAuth2 Password Bearer** com tokens **JWT (HS256)** e rate limiting contra força bruta.
- Garantir isolamento multiusuário estrito em todas as consultas e escritas.
- Cifrar dados pessoais sensíveis (CPF e telefone) em repouso com **Fernet** e manter unicidade via **Blind Index HMAC-SHA256**.
- Conectar de forma transparente tanto ao **MySQL 8 local** quanto ao **TiDB Cloud Serverless** via TLS/SSL nativo.

---

## 🧩 Componentes do Módulo

| Arquivo / Diretório | Responsabilidade Principal |
|---|---|
| [`api.py`](api.py) | Instância FastAPI, validação estrita de `APP_ENV`, política de CORS e rotas `/` e `/health`. |
| [`database.py`](database.py) | Normalizador automático de `DATABASE_URL`, injeção de `ssl.create_default_context()` para TiDB Cloud e pool SQLAlchemy (`pool_pre_ping=True`, `pool_recycle=3600`). |
| [`configuracao.py`](configuracao.py) | Carregamento seguro de variáveis de ambiente a partir do `.env` local ou ambiente do servidor. |
| [`autenticacao.py`](autenticacao.py) | Emissão, decodificação e validação de tokens JWT e dependência `obter_usuario_logado`. |
| [`dados_sensiveis.py`](dados_sensiveis.py) | Cifragem Fernet (`CPF_ENCRYPTION_KEY`) e geração de índice cego HMAC-SHA256 (`cpf_indice`). |
| [`financeiro.py`](financeiro.py) | Motor contábil: recálculo de saldo, validação de contas sem cheque especial e resumos por período. |
| [`models.py`](models.py) | Entidades ORM (`Usuario`, `ContaBancaria`, `FluxoDinheiro`, `CategoriaMovimentacao`, `CalculoFinanceiro`, `MetaFinanceira`, `TentativaLogin`). |
| [`esquema.py`](esquema.py) | Schemas Pydantic v2 para validação de entrada, CPF, complexidade de senha e serialização de saída. |
| [`rotasdeapi/`](rotasdeapi/) | Controladores REST divididos por recurso (`usuario.py`, `conta_bancaria.py`, `fluxo_dinheiro.py`, `calculo_financeiro.py`, `meta_financeira.py`). |
| [`seguranca/`](seguranca/) | Hashing de senhas com `pwdlib` (Argon2id / Bcrypt) e verificação em tempo constante. |
| [`tests/`](tests/) | Suíte com 65 testes automatizados em SQLite em memória e 5 testes de concorrência MySQL. |

---

## 🏗️ Destaques de Engenharia no Backend

### 1. Conexão Resiliente e Normalização de URL (`database.py`)
A função `normalizar_database_url` trata automaticamente variações de string de conexão em nuvem:
- Converte `mysql://` para `mysql+pymysql://`.
- Redireciona referências acidentais ao schema reservado `/sys` para `/test`.
- Codifica caracteres especiais na senha com `urllib.parse.quote_plus`.
- Quando detecta `tidbcloud.com` ou `DB_SSL=true`, instancia `ssl.create_default_context()` diretamente no `connect_args={"ssl": ssl_ctx}`, garantindo compatibilidade com OpenSSL 3 e Python 3.10–3.14 em Linux e Windows.

### 2. Política de CORS por Ambiente (`api.py`)
- **`APP_ENV=development`:** Permite origens locais de desenvolvimento (`127.0.0.1:5500`, `127.0.0.1:5173`, `app.fluxocaixa`) e previews da Vercel.
- **`APP_ENV=production`:** Exige que `CORS_ORIGINS` seja explicitamente definida e bloqueia o uso de curinga `*`, liberando apenas o domínio oficial de produção (`https://fluxo-caixa-coral-two.vercel.app`).

---

## 🚀 Como Executar

### Localmente (Desenvolvimento)
Na raiz do repositório:
```powershell
python main.py
```

### Em Produção (Render Start Command)
```bash
python -m alembic -c "banco de dados/alembic.ini" upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```
