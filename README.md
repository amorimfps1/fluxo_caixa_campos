# 💰 Sistema de Fluxo de Caixa

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-ORM-red?logo=databricks&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-orange)
![Pytest](https://img.shields.io/badge/Pytest-62%20passing-brightgreen?logo=pytest&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

**Aplicação completa de gestão e planejamento financeiro pessoal com API REST assíncrona em FastAPI, persistência relacional com SQLAlchemy e MySQL, interface web responsiva e suíte abrangente de testes automatizados.**

</div>

---

## 📑 Sumário

- [Visão Geral](#-visão-geral)
- [Arquitetura do Sistema](#-arquitetura-do-sistema)
- [Principais Funcionalidades](#-principais-funcionalidades)
- [Stack Tecnológica](#-stack-tecnológica)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a Aplicação](#-executando-a-aplicação)
- [Resumo das Rotas da API](#-resumo-das-rotas-da-api)
- [Segurança e Proteção de Dados](#-segurança-e-proteção-de-dados)
- [Testes Automatizados](#-testes-automatizados)
- [Documentações Complementares](#-documentações-complementares)

---

## 🌟 Visão Geral

O **Sistema de Fluxo de Caixa** foi desenvolvido para oferecer controle rigoroso, transparente e seguro das finanças pessoais. Ele substitui planilhas manuais propensas a erros por um modelo transacional íntegro, que calcula receitas, despesas, transferências entre contas e conciliações em tempo real com precisão `Decimal`.

---

## 🏛️ Arquitetura do Sistema

A aplicação segue uma arquitetura em camadas desacopladas com separação clara de responsabilidades:

```mermaid
flowchart TD
    subgraph FrontendLayer ["🖥️ Camada de Apresentação (Frontend)"]
        UI["Interface do Usuário (HTML5 / CSS3 / JS)"]
        CLIENT["Cliente HTTP api.js (Fetch API + SessionStorage)"]
        UI --> CLIENT
    end

    subgraph APILayer ["⚡ Camada de Aplicação (FastAPI)"]
        CORS["CORS Middleware (Allowlist)"]
        AUTH["Segurança & JWT (OAuth2PasswordBearer)"]
        ROUTERS["Controladores REST (/rotasdeapi)"]
        RULES["Regras de Negócio & Cálculos (financeiro.py)"]
        CRYPTO["Criptografia Fernet & HMAC Blind Index"]
        
        CLIENT -- "HTTP REST (Bearer JWT)" --> CORS
        CORS --> AUTH
        AUTH --> ROUTERS
        ROUTERS --> RULES
        ROUTERS --> CRYPTO
    end

    subgraph DataLayer ["🗄️ Camada de Persistência (SQLAlchemy + MySQL)"]
        MODELS["Modelos Declarativos ORM (models.py)"]
        POOL["Engine com Pool Pre-Ping & Reciclagem"]
        ALEMBIC["Alembic (Versionamento de Esquema)"]
        DB[("MySQL Database")]
        
        RULES --> MODELS
        CRYPTO --> MODELS
        MODELS --> POOL
        POOL --> DB
        ALEMBIC -. "Migrações DDL" .-> DB
    end
```

---

## 🚀 Principais Funcionalidades

### 💼 Backend & API
- **Autenticação Segura:** Login OAuth2 com tokens JWT, expiração configurável e rate limiting contra força bruta (máx. 5 tentativas com bloqueio temporário).
- **Proteção de Dados Sensíveis:** Cifragem simétrica Fernet para CPFs e telefones no banco de dados, com índice cego HMAC-SHA256 para prevenir duplicidades sem expor o valor original.
- **Contas Bancárias:** Criação, edição e exclusão de contas correntes, poupanças e contas de investimento com isolamento estrito entre usuários.
- **Movimentações Completas:** Registro de entradas, saídas, investimentos, transferências entre contas (com par vinculado de débito/crédito) e ajustes de conciliação assinados.
- **Regras de Negócio Rigorosas:** Contas de poupança e investimentos não podem ficar negativas; categorias fixas normalizadas; atomicidade transacional.
- **Cálculos e Metas Financeiras:** Endpoints dedicados para consolidação por período (diário, semanal, mensal, anual) e progresso de metas de economia.
- **Healthcheck & Monitoramento:** Endpoint `/health` para monitoramento de integridade da API e `/docs` interativo OpenAPI Swagger UI.

### 🎨 Frontend
- **Dashboard Intuitivo:** Visualização instantânea de saldo total, saldo por conta e últimas movimentações reais.
- **Modais Dinâmicos:** Abertura rápida de formulários para cadastro de novas contas e novas movimentações.
- **Autenticação Integrada:** Telas dedicadas para login e cadastro de usuários com validação instantânea.
- **Compatibilidade Local:** Suporte nativo tanto ao Live Server do VS Code (`porta 5500`) quanto ao servidor Python local (`porta 5173` ou `80`).

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologia | Função |
|---|---|---|
| **Linguagem** | Python 3.10+ | Linguagem principal do ecossistema backend |
| **Framework Web** | FastAPI | Construção da API REST assíncrona de alta performance |
| **ORM** | SQLAlchemy 2.x | Mapeamento objeto-relacional e gerenciamento de transações |
| **Banco de Dados** | MySQL 8.x | Banco relacional com integridade referencial ACID |
| **Migrações** | Alembic | Versionamento e evolução do esquema do banco |
| **Criptografia** | Cryptography (Fernet) + pwdlib | Cifragem de campos sensíveis e hash seguro de senhas |
| **Testes** | Pytest + AnyIO + Starlette TestClient | Testes unitários, de isolamento e concorrência |
| **Frontend** | HTML5, CSS3, JavaScript Vanilla | Interface estática leve sem dependência de frameworks |

---

## 📁 Estrutura do Projeto

```text
fluxo_caixas/
├── backend/                        # Núcleo da API REST
│   ├── rotasdeapi/                 # Controladores organizados por recurso
│   │   ├── usuario.py              # Cadastro, autenticação e perfil
│   │   ├── conta_bancaria.py       # Gestão de contas financeiras
│   │   ├── fluxo_dinheiro.py       # Movimentações e transferências
│   │   ├── calculo_financeiro.py   # Resumos e balanços periódicos
│   │   └── meta_financeira.py      # Gestão de metas de economia
│   ├── seguranca/                  # Algoritmos de hash e validação de senhas
│   ├── tests/                      # Suíte de testes automatizados (62+ testes)
│   ├── api.py                      # Instância principal FastAPI, CORS e rotas
│   ├── autenticacao.py             # Criação e decodificação de JWT
│   ├── configuracao.py             # Carregamento centralizado de variáveis
│   ├── dados_sensiveis.py          # Cifragem Fernet e índice cego HMAC
│   ├── database.py                 # Engine SQLAlchemy com Pool Pre-Ping
│   ├── esquema.py                  # Schemas Pydantic de validação
│   ├── financeiro.py               # Lógica de negócio e cálculos
│   └── models.py                   # Modelos relacionais ORM
├── banco de dados/                 # Infraestrutura de banco de dados
│   ├── migrations/                 # Scripts oficiais de migração Alembic
│   │   └── versions/               # Histórico das revisões do banco
│   └── alembic.ini                 # Configuração do ambiente Alembic
├── frontend/                       # Interface estática
│   ├── css/                        # Estilos responsivos
│   ├── js/                         # api.js, dashboard.js, login.js, cadastro.js
│   ├── index.html                  # Dashboard autenticado
│   ├── login.html                  # Tela de login
│   └── cadastro.html               # Tela de cadastro de novos usuários
├── scripts/                        # Utilitários de manutenção e testes
├── .env.example                    # Modelo seguro de variáveis de ambiente
├── main.py                         # Ponto de entrada para inicialização local
├── pytest.ini                      # Configuração da suíte de testes
└── requirements.txt                # Dependências Python do projeto
```

---

## 📋 Pré-requisitos

- **Python 3.10 ou superior** instalado.
- **MySQL Server 8.0+** ativo localmente ou em container Docker.
- **Git** para clonagem e versionamento.
- Navegador web moderno (Chrome, Firefox, Edge, Safari).

---

## ⚙️ Instalação e Configuração

### 1. Clonar o Repositório

```bash
git clone https://github.com/arthurcamrocha20052008/fluxo_caixa.git
cd fluxo_caixas
```

### 2. Criar e Ativar o Ambiente Virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar Dependências

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente

Copie o arquivo de exemplo para `.env`:

```powershell
Copy-Item .env.example .env
```

Gere as chaves criptográficas necessárias:

```powershell
# Chave JWT (mínimo de 32 caracteres)
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Chave Fernet (para CPF e telefone)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Abra o arquivo `.env` e configure seus valores:

```ini
DATABASE_URL=mysql+pymysql://seu_usuario:sua_senha@127.0.0.1:3306/fluxo_caixa
JWT_SECRET_KEY=sua_chave_jwt_gerada_acima
CPF_ENCRYPTION_KEY=sua_chave_fernet_gerada_acima
ACCESS_TOKEN_EXPIRE_MINUTES=60
APP_ENV=development
CORS_ORIGINS=http://app.fluxocaixa,http://app.fluxocaixa:5173,http://127.0.0.1:5173,http://127.0.0.1:5500
```

### 5. Executar as Migrações do Banco

Com o MySQL rodando e a base de dados criada, execute:

```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

---

## 🚀 Executando a Aplicação

### 1. Iniciar o Backend (API)

A partir da raiz do projeto:

```powershell
python main.py
```

A API estará disponível em:
- **API Base:** `http://127.0.0.1:8000`
- **Healthcheck:** `http://127.0.0.1:8000/health`
- **Swagger UI Interativo:** `http://127.0.0.1:8000/docs`
- **Especificação OpenAPI:** `http://127.0.0.1:8000/openapi.json`

### 2. Iniciar o Frontend

Você tem duas opções para servir a interface:

#### Opção A — Live Server do VS Code (Recomendado para Dev)
Abra a pasta do projeto no VS Code, clique com o botão direito em `frontend/login.html` e selecione **"Open with Live Server"**. O navegador abrirá em `http://127.0.0.1:5500/frontend/login.html` (já liberado no CORS).

#### Opção B — Servidor Local Python (Porta 5173)
```powershell
Set-Location frontend
..\.venv\Scripts\python.exe -m http.server 5173 --bind 127.0.0.1
```
Acesse no navegador: `http://127.0.0.1:5173/login.html`.

---

## 📡 Resumo das Rotas da API

| Módulo | Método | Rota | Descrição | Autenticação |
|---|---|---|---|---|
| **Sistema** | `GET` | `/` | Boas-vindas e status da API | Não |
| **Sistema** | `GET` | `/health` | Verificação de integridade operacional | Não |
| **Usuários** | `POST` | `/usuarios/` | Cadastro com validação de CPF | Não |
| **Usuários** | `POST` | `/login` | Autenticação OAuth2 e retorno do JWT | Não |
| **Usuários** | `GET` | `/usuarios/me` | Dados do usuário autenticado | Sim (Bearer) |
| **Contas** | `GET` | `/contas-bancarias/` | Lista contas bancárias do usuário | Sim (Bearer) |
| **Contas** | `POST` | `/contas-bancarias/` | Cadastra nova conta com saldo inicial | Sim (Bearer) |
| **Contas** | `PUT` | `/contas-bancarias/{id}` | Atualiza nome/tipo da conta | Sim (Bearer) |
| **Contas** | `DELETE`| `/contas-bancarias/{id}` | Inativa/remove conta | Sim (Bearer) |
| **Fluxo** | `GET` | `/fluxo-dinheiro/` | Extrato com filtros de período e conta | Sim (Bearer) |
| **Fluxo** | `POST` | `/fluxo-dinheiro/` | Lançamento (receita, despesa, transf.) | Sim (Bearer) |
| **Fluxo** | `DELETE`| `/fluxo-dinheiro/{id}` | Remove movimentação (reverte transações)| Sim (Bearer) |
| **Cálculos** | `POST` | `/calculos-financeiros/` | Consolida balanço por período | Sim (Bearer) |
| **Cálculos** | `GET` | `/calculos-financeiros/` | Histórico de cálculos consolidados | Sim (Bearer) |
| **Metas** | `GET` | `/metas-financeiras/` | Consulta metas ativas e concluídas | Sim (Bearer) |
| **Metas** | `POST` | `/metas-financeiras/` | Cria nova meta de economia | Sim (Bearer) |

---

## 🔒 Segurança e Proteção de Dados

- **Proteção do CPF e Telefone:** Em conformidade com as melhores práticas de privacidade (LGPD), o CPF e o telefone são cifrados com **Fernet** em repouso. O CPF nunca é retornado em texto puro pelas APIs.
- **Prevenção de Duplicidade:** Um hash **HMAC-SHA256** com salt derivado gera um índice cego determinístico (`cpf_indice`), permitindo checar unicidade sem descriptografar a base.
- **Proteção contra Brute Force:** Bloqueio progressivo temporário com código HTTP 429 para IPs com múltiplas tentativas inválidas em uma janela de 15 minutos.
- **Controle de CORS Estrito:** Origens autorizadas explicitamente configuráveis por ambiente, prevenindo requisições indesejadas de domínios externos.
- **Validação de Entrada:** Validação de formato e dígitos verificadores de CPF, bloqueio de dígitos Unicode arbitrários e tipagem estrita com Pydantic v2.

---

## 🧪 Testes Automatizados

O projeto conta com uma suíte abrangente de testes automatizados com SQLite em memória, garantindo isolamento total da base de desenvolvimento.

Execute os testes com:

```powershell
python -m pytest -q
```

Para visualização detalhada com saída completa:

```powershell
python -m pytest -v
```

> 💡 **Nota:** Para executar os testes de concorrência específicos do MySQL (`SELECT ... FOR UPDATE`), consulte [backend/tests/README.md](backend/tests/README.md).

---

## 📚 Documentações Complementares

Para um mergulho detalhado em cada área da aplicação, consulte os guias especializados:

- 🏛️ [**Guia de Arquitetura e Estrutura**](ESTRUTURA.md)
- ⚙️ [**Documentação do Backend**](backend/readme.md)
- 🧭 [**Manual de Rotas e Endpoints da API**](backend/rotasdeapi/readme.md)
- 🔐 [**Arquitetura de Segurança e Criptografia**](backend/seguranca/readme.md)
- 🧪 [**Guia Completo da Suíte de Testes**](backend/tests/README.md)
- 🗄️ [**Modelagem do Banco de Dados**](banco%20de%20dados/readme.md)
- 🔄 [**Manual de Migrações Alembic**](banco%20de%20dados/migrations/README.md)
- 📜 [**Changelog de Revisões do Esquema**](banco%20de%20dados/migrations/versions/README.md)
- 🖥️ [**Manual do Frontend e Telas**](frontend/README.md)

---

<div align="center">
Desenvolvido com foco em segurança, integridade financeira e excelência arquitetural.
</div>
