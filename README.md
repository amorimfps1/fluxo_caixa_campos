# 💰 Sistema de Fluxo de Caixa — Enterprise Edition

> 🌐 **Aplicação Web Online (Vercel):** [**https://fluxo-caixa-coral-two.vercel.app**](https://fluxo-caixa-coral-two.vercel.app)  
> ⚡ **API Backend em Produção (Render):** [**https://fluxo-caixa-cuq1.onrender.com**](https://fluxo-caixa-cuq1.onrender.com) | [**Swagger UI (`/docs`)**](https://fluxo-caixa-cuq1.onrender.com/docs) | [**Healthcheck (`/health`)**](https://fluxo-caixa-cuq1.onrender.com/health)

<div align="center">

[![Live Demo](https://img.shields.io/badge/Demo_Online-Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://fluxo-caixa-coral-two.vercel.app)
[![API Status](https://img.shields.io/badge/API_Backend-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://fluxo-caixa-cuq1.onrender.com/health)
[![Database](https://img.shields.io/badge/Database-Supabase_PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Database](https://img.shields.io/badge/MySQL_Compatível-TiDB_Cloud-005571?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.x_ORM-D71F00?logo=databricks&logoColor=white)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-16_Revisões-F59E0B?logo=alembic&logoColor=white)](https://alembic.sqlalchemy.org/)
[![Pytest](https://img.shields.io/badge/Pytest-109%20Passing-brightgreen?logo=pytest&logoColor=white)](https://pytest.org/)
[![Security](https://img.shields.io/badge/Security-LGPD_Fernet_AES128_%2B_Argon2id_%2B_OAuth2-blueviolet)](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

<br/>

**Plataforma Full-Stack de gestão patrimonial e fluxo de caixa corporativo/pessoal em nuvem. Construída com API REST assíncrona em FastAPI, banco de dados relacional (Supabase PostgreSQL / TiDB Cloud MySQL), precisão contábil exata (`Decimal 12,2`), conformidade LGPD em repouso (Fernet AES-128 + Blind Index HMAC), Login Social Google OAuth 2.0, verificação anti-bot via OTP por e-mail, Landing Page de alta conversão, interface SPA responsiva (Tema Claro e Escuro) e 109 testes automatizados.**

</div>

---

## 📑 Sumário

- [Acesso Rápido à Demo Online](#-acesso-rápido-à-demo-online)
- [Visão Geral & Proposta de Valor](#-visão-geral--proposta-de-valor)
- [Arquitetura Full-Stack em Nuvem](#-arquitetura-full-stack-em-nuvem)
- [Principais Funcionalidades e Diferenciais](#-principais-funcionalidades-e-diferenciais)
- [Stack Tecnológica Completa](#-stack-tecnológica-completa)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Execução Local Passo a Passo](#-execução-local-passo-a-passo)
- [Deploy em Nuvem (Vercel + Render + Supabase)](#-deploy-em-nuvem-vercel--render--supabase)
- [Catálogo de Endpoints da API](#-catálogo-de-endpoints-da-api)
- [Segurança & Privacidade LGPD](#-segurança--privacidade-lgpd)
- [Qualidade & Testes Automatizados](#-qualidade--testes-automatizados)
- [Documentações Complementares](#-documentações-complementares)

---

## 🌍 Acesso Rápido à Demo Online

| Recurso / Serviço | Plataforma | URL Pública | Finalidade |
|---|---|---|---|
| **Aplicação Web (SPA)** | Vercel Edge | [https://fluxo-caixa-coral-two.vercel.app](https://fluxo-caixa-coral-two.vercel.app) | Painel financeiro autenticado |
| **Página de Login** | Vercel Edge | [https://fluxo-caixa-coral-two.vercel.app/login.html](https://fluxo-caixa-coral-two.vercel.app/login.html) | Acesso seguro com rate limiting |
| **Página de Cadastro** | Vercel Edge | [https://fluxo-caixa-coral-two.vercel.app/cadastro.html](https://fluxo-caixa-coral-two.vercel.app/cadastro.html) | Criação de conta com validação de CPF |
| **API REST (Backend)** | Render Web Service | [https://fluxo-caixa-cuq1.onrender.com](https://fluxo-caixa-cuq1.onrender.com) | Núcleo de serviços e regras contábeis |
| **Documentação Interativa** | Swagger UI | [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs) | Teste e inspeção direta de endpoints |
| **Healthcheck Operacional** | Render Monitor | [https://fluxo-caixa-cuq1.onrender.com/health](https://fluxo-caixa-cuq1.onrender.com/health) | Diagnóstico de integridade da API |

> [!NOTE]
> No plano gratuito do Render, caso a API permaneça inativa por alguns minutos, a primeira requisição (*cold start*) pode levar cerca de **30 a 50 segundos** para despertar o contêiner. Após a inicialização, todas as respostas são servidas em milissegundos.

---

## 🌟 Visão Geral & Proposta de Valor

O **Sistema de Fluxo de Caixa** substitui o uso frágil de planilhas manuais por uma arquitetura transacional, auditável e resiliente:
- **Precisão Financeira Estrita:** Todo cálculo opera com aritmética contábil `Decimal(12, 2)`, sem dízimas ou erros de ponto flutuante.
- **Psicologia das Cores Financeiras:** Design corporativo sóbrio (`#0B0F19`, `#111827`, `#059669`, `#3B82F6`, `#BE123C`), sem emojis informais, utilizando exclusivamente ícones vetoriais SVG de alto contraste.
- **Módulo Unificado de Investimentos:** Aporte direto em ativos de Renda Fixa e Renda Variável com débito automático da conta de origem e consolidação patrimonial em tempo real.
- **Classificação Transacional:** Subdivisão estruturada de receitas (**Ganhos Fixos** vs **Ganhos Variáveis**) e despesas (**Gastos Fixos** vs **Gastos Variáveis**).
- **Proteção Ativa:** Notificações proativas no dashboard para saídas agendadas nos próximos 7 dias e tetos orçamentários mensais por categoria.

---

## 🏛️ Arquitetura Full-Stack em Nuvem

A aplicação adota o princípio de **Separação de Responsabilidades (SoC)** com três camadas desacopladas em nuvem e suporte nativo a ambiente local:

```mermaid
flowchart TD
    subgraph PresentationLayer ["🌐 Camada de Apresentação (Vercel CDN / Edge)"]
        SPA["Frontend SPA (index.html, login.html, cadastro.html)"]
        DESIGN["Design System & Cores Financeiras (style.css)"]
        HTTP_CLIENT["Cliente HTTP Inteligente (api.js)"]
        SPA --- DESIGN
        SPA --> HTTP_CLIENT
    end

    subgraph ApplicationLayer ["⚡ Camada de Aplicação (Render / FastAPI)"]
        CORS_FILTER["Middleware CORS Estrito por Ambiente"]
        RATE_LIMIT["Rate Limiter Anti-Brute Force (IP + E-mail)"]
        SECURITY_MOD["OAuth2 JWT + Hashing Argon2id (pwdlib)"]
        ROUTERS["Controladores REST (/rotasdeapi)"]
        ENGINE["Motor Contábil & Regras de Domínio (financeiro.py)"]
        CRYPTO["Criptografia LGPD (Fernet AES-128 + Blind Index HMAC)"]
        EMAIL_SVC["Serviço de E-mail Transacional SMTP (servicos/email.py)"]

        HTTP_CLIENT -- "HTTPS REST JSON (Bearer JWT)" --> CORS_FILTER
        CORS_FILTER --> RATE_LIMIT
        RATE_LIMIT --> SECURITY_MOD
        SECURITY_MOD --> ROUTERS
        ROUTERS --> ENGINE
        ROUTERS --> CRYPTO
        ROUTERS --> EMAIL_SVC
    end

    subgraph PersistenceLayer ["🗄️ Camada de Persistência (Supabase PostgreSQL / TiDB Cloud)"]
        ORM["SQLAlchemy 2.x Declarative Models"]
        POOL["Engine com SSL/TLS Nativo & Pool Pre-Ping"]
        ALEMBIC["Alembic Migrations (16 Revisões Versionadas)"]
        DATABASE[("Supabase PostgreSQL 15+ / TiDB MySQL Serverless")]

        ENGINE --> ORM
        CRYPTO --> ORM
        ORM --> POOL
        POOL -- "Conexão Segura Criptografada (Pooler 6543)" --> DATABASE
        ALEMBIC -. "Upgrade Automático no Deploy" .-> DATABASE
    end
```

---

## 🚀 Principais Funcionalidades e Diferenciais

### 💼 Motor Contábil & Investimentos
- **Gestão de Investimentos Integrada:** Registro de aportes com dedução instantânea da conta bancária de origem e integração direta com o resumo de patrimônio. Ativos suportados:
  - *Renda Fixa:* Poupança, CDB, LCI/LCA, Tesouro Direto, Fundos de Investimento.
  - *Renda Variável:* Ações, ETFs, FIIs e Subscrições.
- **Subdivisão de Entradas e Saídas:**
  - *Entradas:* Classificação explícita entre **Ganhos Fixos** (Salário, pró-labore) e **Ganhos Variáveis** (Pix, vendas de itens, freelas, rendimentos).
  - *Saídas:* Classificação entre **Gastos Fixos** (contas essenciais) e **Gastos Variáveis** (consumo pontual).
- **Transferências Atômicas Vinculadas:** Operações entre contas geram pares vinculados por `transferencia_id` (UUIDv4) com trava pessimista (`SELECT ... FOR UPDATE`), garantindo que a exclusão de qualquer ponta reverta os saldos das duas contas de forma indivisível.
- **Orçamentos Mensais & Alertas Proativos:** Estabeleça tetos de gastos por categoria no mês, com barras de progresso dinâmicas e avisos de saídas nos próximos 7 dias.

### 🎨 Experiência do Usuário (UI/UX) de Alta Fidelidade
- **Psicologia das Cores Financeiras:** Paleta profissional com fundo escuro profundo (`#0B0F19`), verde crescimento institucional (`#059669` / `#10B981`), azul confiança estrutural (`#3B82F6`) e vermelho sóbrio (`#BE123C`).
- **100% Vetorial (Zero Emojis):** Elementos visuais construídos com SVG inline de alta definição.
- **Microinterações Refinadas:**
  - Fechamento de modais ao clicar no backdrop externo (*click outside*).
  - Layout calibrado sem barras de rolagem lateral (`overflow-x: hidden`).
  - Botão de acesso rápido a **Nova Movimentação** no topo do Dashboard.
  - Atalhos corporativos no rodapé da barra lateral: link direto para o **Gmail** e **Configurações**.
  - Confirmação visual defensiva ao realizar *logout*.

### 🔒 Segurança & Privacidade LGPD
- **Criptografia Simétrica em Repouso:** CPF e telefone armazenados cifrados com **Fernet (AES-128-CBC + HMAC-SHA256)**.
- **Blind Index Criptográfico:** Verificação instantânea de unicidade de CPF sem descriptografar a base de dados, utilizando HMAC-SHA256 com chave derivada (`cpf_indice`).
- **Proteção Anti-Força Bruta:** Limitação de 5 falhas consecutivas de login por IP/conta em janela de 15 minutos (`HTTP 429`).
- **Isolamento de Tenant:** Todas as operações no banco utilizam obrigatoriamente o `usuario_id` extraído criptograficamente do token JWT.

---

## 🛠️ Stack Tecnológica Completa

| Camada | Tecnologia | Descrição & Papel |
|---|---|---|
| **Frontend Hosting** | Vercel Edge Network | Hospedagem estática global com HTTPS e rewrites via `vercel.json` |
| **Frontend Core** | HTML5, CSS3, JavaScript (ES6+), Chart.js | SPA responsiva sem frameworks pesados, gráficos analíticos e exportação CSV |
| **Backend Hosting** | Render Web Service | Contêiner Python gerenciado com deploy contínuo integrado ao GitHub |
| **API Framework** | FastAPI + Uvicorn | Framework assíncrono moderno com validação via Pydantic v2 e OpenAPI 3.1 |
| **ORM & Migrações** | SQLAlchemy 2.x + Alembic | Mapeamento declarativo relacional, transações ACID e 16 revisões versionadas |
| **Banco em Nuvem** | Supabase PostgreSQL / TiDB Cloud | PostgreSQL 15+ com Pooler PgBouncer porta 6543 e MySQL 8 Serverless com TLS |
| **Segurança & Crypto** | Cryptography (Fernet) + pwdlib (Argon2id) + PyJWT | Cifragem de PII, hashing resistente a GPU e autenticação por tokens assinados |
| **Serviço de E-mail** | Python smtplib com STARTTLS | Envio de códigos OTP e e-mails de confirmação com fallback resiliente |
| **Suíte de Testes** | Pytest + HTTPX TestClient | 109 testes automatizados cobrindo fluxos E2E, integridade contábil, OAuth 2.0, OTP anti-bot e LGPD |

---

## 📁 Estrutura do Projeto

```text
fluxo_caixas/
├── backend/                            # Núcleo da API REST e regras de negócio
│   ├── rotasdeapi/                     # Controladores REST modulares por domínio
│   │   ├── usuario.py                  # Cadastro LGPD, Google OAuth 2.0, OTP anti-bot, login, perfil e exclusão
│   │   ├── conta_bancaria.py           # Gestão de contas correntes, poupanças e investimentos
│   │   ├── fluxo_dinheiro.py           # Lançamentos, transferências vinculadas e aportes de investimentos
│   │   ├── calculo_financeiro.py       # Relatórios e balanços consolidados periódicos
│   │   ├── meta_financeira.py          # Metas financeiras com acompanhamento de progresso
│   │   ├── orcamentos_alertas.py       # Tetos por categoria, acompanhamento e alertas de vencimento
│   │   └── readme.md                   # Catálogo técnico de rotas, contratos e payloads
│   ├── seguranca/                      # Segurança e criptografia
│   │   ├── seguranca.py                # Hashing e validação de senhas com Argon2id
│   │   └── readme.md                   # Diretrizes de proteção de senhas
│   ├── servicos/                       # Serviços utilitários
│   │   ├── email.py                    # Envio defensivo de e-mails transacionais via SMTP
│   │   └── google_oauth.py             # Validação de ID Token Google OAuth 2.0 (iss, aud, exp, email_verified)
│   ├── tests/                          # Suíte de 109 testes automatizados
│   │   ├── conftest.py                 # Fixtures globais e banco em memória SQLite
│   │   ├── test_*.py                   # Módulos de testes por especialidade (incluindo OAuth 2.0 e LGPD)
│   │   └── README.md                   # Guia detalhado da suíte de testes
│   ├── api.py                          # Configuração do FastAPI, CORS, tradução PT-BR e healthcheck
│   ├── autenticacao.py                 # Emissão e validação de tokens JWT
│   ├── configuracao.py                 # Carregamento seguro de configurações (.env)
│   ├── dados_sensiveis.py              # Cifragem Fernet AES-128 e Blind Index HMAC (CPF, telefone e OAuth)
│   ├── database.py                     # Conexão SQLAlchemy normalizada (PostgreSQL/Supabase/MySQL)
│   ├── esquema.py                      # Schemas Pydantic v2 (CPF estrito, senha forte e consentimento LGPD)
│   ├── financeiro.py                   # Motor contábil e cálculos com precisão Decimal
│   ├── models.py                       # Entidades ORM (10 tabelas mapeadas)
│   └── readme.md                       # Documentação técnica do backend
│
├── banco de dados/                     # Esquema relacional e versionamento
│   ├── migrations/                     # Histórico oficial gerenciado pelo Alembic
│   │   ├── versions/                   # 16 migrações incrementais do banco
│   │   └── env.py                      # Contexto operacional Alembic
│   ├── alembic.ini                     # Arquivo de configuração Alembic
│   └── readme.md                       # Diagrama ERD e dicionário de dados
│
├── frontend/                           # Aplicação Web SPA & Landing Page (Vercel)
│   ├── assets/logo.svg                 # Logotipo vetorial corporativo oficial em SVG
│   ├── css/style.css                   # Design system financeiro responsivo (Modo Claro e Modo Escuro)
│   ├── js/                             # Módulos JS (api.js, legal.js, dashboard.js, login.js, cadastro.js)
│   ├── inicio.html                     # Landing Page de alta conversão com CTAs estratégicos
│   ├── index.html                      # Painel financeiro principal autenticado (SPA)
│   ├── login.html                      # Tela de login com Google OAuth 2.0 e recuperação segura
│   ├── cadastro.html                   # Cadastro com CPF em tempo real, checklist de senha, LGPD e modal OTP
│   ├── termos.html                     # Página dedicada dos Termos de Serviço
│   ├── privacidade.html                # Página dedicada da Política de Privacidade e LGPD
│   └── README.md                       # Guia do frontend e publicação
│
├── scripts/                            # Scripts utilitários administrativos
│   ├── migrar_para_supabase.py         # Script de migração de banco para Supabase
│   ├── supabase_schema_completo.sql    # DDL estruturado para o SQL Editor
│   ├── remover_usuario_teste.py        # Exclusão segura e transacional de usuário de teste
│   └── README.md                       # Guia de uso dos scripts
│
├── .env.example                        # Template seguro de variáveis de ambiente
├── .gitignore                          # Regras de exclusão do Git
├── .vercelignore                       # Exclusão de arquivos backend no deploy do frontend
├── ESTRUTURA.md                        # Mapa arquitetural detalhado do sistema
├── main.py                             # Ponto de entrada unificado para execução local
├── pytest.ini                          # Configuração do executor Pytest
├── requirements.txt                    # Dependências Python fixadas
└── vercel.json                         # Roteamento e rewrites estáticos da Vercel
```

---

## 💻 Execução Local Passo a Passo

### 1. Clonar o Repositório e Criar o Ambiente Virtual

```powershell
git clone https://github.com/arthurcamrocha20052008/fluxo_caixa.git
cd fluxo_caixas
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente (`.env`)

Crie seu arquivo local a partir do modelo `.env.example`:

```powershell
Copy-Item .env.example .env
```

Gere chaves criptográficas seguras:

```powershell
# Chave para assinatura JWT
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Chave Fernet para PII (CPF e telefone)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Preencha no seu arquivo `.env`:
```ini
APP_ENV=development
DATABASE_URL=postgresql+psycopg2://usuario:senha@host:6543/postgres?sslmode=require
JWT_SECRET_KEY=sua_chave_gerada_acima
CPF_ENCRYPTION_KEY=sua_chave_fernet_gerada_acima
CORS_ORIGINS=http://127.0.0.1:5500,http://127.0.0.1:5173
```

### 3. Aplicar as Migrações do Banco de Dados

Execute o Alembic para criar ou atualizar todas as tabelas:

```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

### 4. Inicializar a API FastAPI

```powershell
python main.py
```

A API estará disponível em:
- **API Local:** `http://127.0.0.1:8000`
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **Healthcheck:** `http://127.0.0.1:8000/health`

### 5. Executar o Frontend Localmente

Inicie um servidor HTTP local a partir da pasta `frontend`:

```powershell
python -m http.server 5173 --bind 127.0.0.1 --directory frontend
```

Acesse em seu navegador: [**http://127.0.0.1:5173/login.html**](http://127.0.0.1:5173/login.html).

---

## ☁️ Deploy em Nuvem (Vercel + Render + Supabase)

O fluxo de CI/CD está configurado para publicação automática a partir de commits na branch `main`:

```mermaid
flowchart LR
    GIT["GitHub (branch main)"] -->|Deploy Automático| VERCEL["Frontend (Vercel)"]
    GIT -->|Deploy Automático| RENDER["Backend (Render)"]
    RENDER -->|Pooler AWS 6543| SUPABASE[("Banco de Dados (Supabase PostgreSQL)")]
```

1. **Banco de Dados (Supabase PostgreSQL):**
   - Criação das tabelas e índices via migrações Alembic ou script [`scripts/supabase_schema_completo.sql`](scripts/supabase_schema_completo.sql).
   - Conexão configurada pelo connection pooler PgBouncer na porta `6543` com SSL obrigatório.
2. **Backend (Render Web Service):**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m alembic -c "banco de dados/alembic.ini" upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Environment Variables:** `APP_ENV=production`, `CORS_ORIGINS=https://fluxo-caixa-coral-two.vercel.app`, `DATABASE_URL`, `JWT_SECRET_KEY`, `CPF_ENCRYPTION_KEY`.
3. **Frontend (Vercel):**
   - Publicação configurada em [`vercel.json`](vercel.json) (`outputDirectory: "frontend"`), redirecionando a raiz para `/login.html`.

---

## 📡 Catálogo de Endpoints da API

| Módulo | Método | Rota | Descrição | Autenticação |
|---|---|---|---|---|
| **Sistema** | `GET` | `/` | Confirmação de status da API | Pública |
| **Sistema** | `GET` | `/health` | Healthcheck operacional e ambiente ativo | Pública |
| **Usuários** | `POST` | `/usuarios/` | Cadastro com validação estrita de CPF, senha forte, aceite LGPD e disparo de OTP | Pública |
| **Usuários** | `POST` | `/usuarios/verificar-email` | Confirmação anti-bot de e-mail via código OTP de 6 dígitos (uso único) + emissão de JWT | Pública |
| **Usuários** | `POST` | `/usuarios/confirmar-email` | Rota compatível de confirmação de e-mail via código OTP de 6 dígitos | Pública |
| **Usuários** | `POST` | `/usuarios/reenviar-verificacao` | Reenvio de código OTP temporário de verificação de cadastro | Pública (Rate Limited) |
| **Usuários** | `GET` | `/usuarios/auth/google/config` | Consulta disponibilidade e `client_id` público do Google OAuth 2.0 | Pública |
| **Usuários** | `POST` | `/usuarios/auth/google` | Login Social Google OAuth 2.0 (cria/vincula conta e retorna JWT) | Pública (Rate Limited) |
| **Usuários** | `POST` | `/login` | Autenticação OAuth2 (`username` = e-mail, `password` = senha) | Pública (Rate Limited) |
| **Usuários** | `POST` | `/usuarios/esqueci-senha` | Solicitação de código de recuperação por e-mail | Pública |
| **Usuários** | `POST` | `/usuarios/redefinir-senha` | Redefinição de senha com validação de código OTP | Pública |
| **Usuários** | `GET` | `/usuarios/me` | Retorna dados cadastrais do usuário autenticado | Bearer JWT |
| **Usuários** | `PUT` | `/usuarios/me` | Atualiza perfil cadastral (`nome_completo`, `telefone`) | Bearer JWT |
| **Usuários** | `DELETE`| `/usuarios/me` | Exclui a conta do usuário logado e dados vinculados | Bearer JWT |
| **Usuários** | `GET` | `/usuarios/` | Listagem administrativa de usuários cadastrados | Bearer JWT |
| **Usuários** | `DELETE`| `/usuarios/{id}` | Exclusão administrativa de usuário específico | Bearer JWT |
| **Contas** | `GET` | `/contas-bancarias/` | Lista contas bancárias com saldos atualizados | Bearer JWT |
| **Contas** | `POST` | `/contas-bancarias/` | Cria nova conta (`corrente`, `poupanca`, `investimento`) | Bearer JWT |
| **Contas** | `PUT` | `/contas-bancarias/{id}` | Atualiza nome, tipo ou status da conta bancária | Bearer JWT |
| **Contas** | `DELETE`| `/contas-bancarias/{id}` | Exclui conta bancária sem vínculos pendentes | Bearer JWT |
| **Fluxo** | `GET` | `/fluxo-dinheiro/` | Extrato de movimentações com filtros combinados | Bearer JWT |
| **Fluxo** | `POST` | `/fluxo-dinheiro/` | Registra entrada, saída, investimento ou transferência | Bearer JWT |
| **Fluxo** | `PUT` | `/fluxo-dinheiro/{id}` | Atualiza movimentação e recalcula saldos vinculados | Bearer JWT |
| **Fluxo** | `DELETE`| `/fluxo-dinheiro/{id}` | Exclui movimentação (ou par atômico de transferência) | Bearer JWT |
| **Orçamentos**| `GET` | `/orcamentos` | Lista orçamentos mensais e percentual de consumo | Bearer JWT |
| **Orçamentos**| `POST` | `/orcamentos` | Define teto mensal de gastos por categoria | Bearer JWT |
| **Orçamentos**| `PUT` | `/orcamentos/{id}` | Altera o limite mensal de um orçamento existente | Bearer JWT |
| **Orçamentos**| `DELETE`| `/orcamentos/{id}` | Remove teto orçamentário | Bearer JWT |
| **Alertas** | `GET` | `/alertas` | Consulta alertas de orçamentos e saídas dos próximos 7 dias | Bearer JWT |
| **Alertas** | `PUT` | `/alertas/lido` | Marca alerta específico como lido | Bearer JWT |
| **Alertas** | `GET` | `/alertas/preferencias` | Consulta preferências de notificação do usuário | Bearer JWT |
| **Alertas** | `PUT` | `/alertas/preferencias` | Atualiza preferências de notificação | Bearer JWT |
| **Cálculos** | `POST` | `/calculos-financeiros/` | Consolida e grava balanço contábil por período | Bearer JWT |
| **Cálculos** | `GET` | `/calculos-financeiros/` | Histórico de consolidações contábeis | Bearer JWT |
| **Metas** | `GET` | `/metas-financeiras/` | Lista metas de economia e percentual concluído | Bearer JWT |
| **Metas** | `POST` | `/metas-financeiras/` | Cria nova meta financeira com alvo e data | Bearer JWT |
| **Metas** | `PUT` | `/metas-financeiras/{id}` | Atualiza aportes e conclui automaticamente ao atingir alvo | Bearer JWT |
| **Metas** | `DELETE`| `/metas-financeiras/{id}` | Remove meta financeira | Bearer JWT |

---

## 🔒 Segurança & Privacidade LGPD

- **Cifragem Simétrica Fernet:** CPF e telefone trafegam e residem em repouso sob cifra AES-128 em modo CBC com integridade verificada por HMAC-SHA256.
- **Blind Index HMAC (`cpf_indice`):** Permite buscas indexadas e restrição de unicidade sem expor o CPF em texto plano.
- **Hashing de Senha Resistente a GPU:** Implementação moderna via `pwdlib` utilizando **Argon2id** (vencedor da Password Hashing Competition) e fallback Bcrypt.
- **Defesa Anti-Enumeração:** A rota de login utiliza tempo simulado caso o e-mail não exista, prevenindo enumeração de contas por análise de latência (*timing attacks*).
- **Rate Limiting em Camada de Aplicação:** Bloqueio progressivo após 5 falhas consecutivas em janela de 15 minutos com status `HTTP 429`.

---

## 🧪 Qualidade & Testes Automatizados

A aplicação conta com **109 testes automatizados** executados via Pytest com banco de dados SQLite em memória totalmente isolado:

```powershell
python -m pytest -q
```

Saída esperada:
```text
109 passed, 5 deselected
```

Os 5 testes marcados como `deselected` correspondem a testes de alta concorrência com bloqueio pessimista (`SELECT ... FOR UPDATE`) que exigem um cluster MySQL ativo.

---

## 📚 Documentações Complementares

- 🏛️ [**Mapa Arquitetural Completo (ESTRUTURA.md)**](ESTRUTURA.md)
- ⚙️ [**Guia do Módulo Backend**](backend/readme.md)
- 🧭 [**Catálogo Técnico de Rotas da API**](backend/rotasdeapi/readme.md)
- 🔐 [**Arquitetura de Segurança e Criptografia LGPD**](backend/seguranca/readme.md)
- 🧪 [**Manual da Suíte de Testes Automatizados**](backend/tests/README.md)
- 🗄️ [**Modelagem e Dicionário de Dados**](banco%20de%20dados/readme.md)
- 🔄 [**Manual de Migrações Alembic**](banco%20de%20dados/migrations/README.md)
- 🖥️ [**Documentação do Frontend e SPA Vercel**](frontend/README.md)
- 🛠️ [**Guia de Scripts Administrativos**](scripts/README.md)

---

<div align="center">
Desenvolvido com excelência técnica, precisão contábil, segurança de dados e arquitetura moderna em nuvem.
</div>
