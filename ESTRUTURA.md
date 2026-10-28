# 🏛️ Arquitetura e Estrutura do Projeto

> 🌐 **Aplicação Web (Vercel):** [https://fluxo-caixa-coral-two.vercel.app](https://fluxo-caixa-coral-two.vercel.app)  
> ⚡ **API REST (Render):** [https://fluxo-caixa-cuq1.onrender.com](https://fluxo-caixa-cuq1.onrender.com)  
> 📖 **Swagger OpenAPI:** [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs)  
> 🗄️ **Banco de Dados:** [Supabase PostgreSQL](https://supabase.com) (Pooler AWS porta 6543) / Compatível com MySQL 8

Este documento detalha o mapa arquitetural completo do **Sistema de Fluxo de Caixa**, explicando a topologia de nuvem, a separação de responsabilidades em camadas (SoC), os padrões de projeto, a modelagem de dados e o fluxo de dados ponta a ponta.

---

## 📐 Topologia de Nuvem e Separação de Responsabilidades (SoC)

O projeto adota uma arquitetura desacoplada em três camadas independentes em produção, com total paridade para execução local:

```mermaid
flowchart TD
    subgraph ClientLayer ["🌐 Camada de Apresentação (Frontend SPA - Vercel Edge)"]
        UI["Interface Responsiva (index.html, login.html, cadastro.html)"]
        CSS["Design System & Psicologia das Cores (#0B0F19, #059669, #3B82F6, #BE123C)"]
        CHARTS["Visualização Analítica (Chart.js + SVG Vetoriais Nativos)"]
        API_CLIENT["Cliente HTTP SPA (frontend/js/api.js)"]
        
        UI --- CSS
        UI --- CHARTS
        UI --> API_CLIENT
    end

    subgraph ServerLayer ["⚡ Camada de Aplicação (Backend REST - Render / FastAPI)"]
        CORS["Middleware CORS Estrito (Allowlist de Produção)"]
        RATE["Rate Limiter Anti-Brute Force (IP + E-mail)"]
        AUTH["OAuth2 Password Bearer + JWT (HS256)"]
        ROUTERS["Controladores REST Modulares (backend/rotasdeapi/)"]
        DOMAIN["Motor Contábil & Regras de Domínio (financeiro.py)"]
        CRYPTO["Criptografia LGPD (Fernet AES-128 + Blind Index HMAC)"]
        NOTIF["Serviço de Notificação Transacional (servicos/email.py)"]

        API_CLIENT -- "HTTPS REST JSON (Bearer JWT)" --> CORS
        CORS --> RATE
        RATE --> AUTH
        AUTH --> ROUTERS
        ROUTERS --> DOMAIN
        ROUTERS --> CRYPTO
        ROUTERS --> NOTIF
    end

    subgraph DataLayer ["🗄️ Camada de Persistência (Supabase PostgreSQL / TiDB Cloud MySQL)"]
        ORM["Mapeamento Objeto-Relacional (SQLAlchemy 2.x Declarative)"]
        POOL["Engine com SSL Nativo, Pre-Ping & Connection Recycling"]
        MIGRATIONS["Versionamento de Esquema (Alembic Migrations)"]
        DB[("Supabase PostgreSQL 15+ / TiDB MySQL Serverless")]

        DOMAIN --> ORM
        CRYPTO --> ORM
        ORM --> POOL
        POOL -- "Conexão Segura SSL/TLS (Pooler 6543)" --> DB
        MIGRATIONS -. "Upgrade Automático no Deploy" .-> DB
    end
```

---

## 🧩 Camadas da Aplicação e Padrões de Projeto

### 1. Camada de Apresentação (Frontend SPA)
- **Tecnologia:** HTML5 Semântico, CSS3 Moderno (Custom Properties, Flexbox e CSS Grid), Vanilla JavaScript (ES6+).
- **Psicologia das Cores Financeiras:**
  - *Fundo e Superfícies:* `#0B0F19` e `#111827` (transmitem solidez, sobriedade e tecnologia).
  - *Verde Institucional / Crescimento:* `#059669` / `#10B981` (entradas, ganhos fixos, saldos positivos e botões CTA primários).
  - *Azul Confiança / Neutro Estrutural:* `#3B82F6` (contas bancárias, links e elementos estruturais).
  - *Vermelho/Coral Sutil:* `#BE123C` (saídas, despesas e alertas).
  - *Padronização de Bordas:* `border-radius: 10px` em inputs, botões e selects.
- **Zero Emojis:** Interface 100% composta por vetores SVG nativos para acabamento institucional de nível bancário.
- **Microinterações:** Fechamento automático de modais ao clicar no backdrop externo (*click outside*), controle de overflow para eliminar scroll horizontal indesejado e confirmação segura para encerramento de sessão (*logout*).

### 2. Camada de Segurança e Autenticação
- **Autenticação:** Tokens JWT assinados com algoritmo HS256 e tempo de vida configurável via variável de ambiente.
- **Proteção Anti-Força Bruta:** Limitação estrita de 5 tentativas consecutivas de login por janela de 15 minutos, persistidas na tabela `tentativas_login` e bloqueadas com status `HTTP 429 Too Many Requests`.
- **Criptografia e LGPD em Repouso:**
  - CPF e telefone cifrados via **Fernet (AES-128 em modo CBC com assinatura HMAC-SHA256)**.
  - O CPF possui um índice cego determinístico derivado (**Blind Index** via `HMAC-SHA256`) armazenado na coluna `cpf_indice`, permitindo validação de unicidade instantânea sem expor o número real do documento.
- **Hashing de Senhas:** Utilização de `pwdlib` com o algoritmo recomendado **Argon2id** (memória e tempo parametrizados), com fallback automático para Bcrypt.

### 3. Camada de Domínio e Motor Contábil (`backend/financeiro.py`)
- **Aritmética Exata:** Uso exclusivo da classe `Decimal` de Python com 2 casas decimais (`Decimal(12, 2)` no banco), eliminando erros de arredondamento de ponto flutuante IEEE 754.
- **Transferências Atômicas Vinculadas:** Ao transferir valores entre contas, o sistema cria dois registros interligados por um identificador único `transferencia_id` (UUIDv4) e executa a operação em transação atômica protegida por `SELECT ... FOR UPDATE`. Se qualquer ponta for excluída, a contraparte e os respectivos saldos são restaurados atomicamente.
- **Módulo de Investimentos Unificado:** Registro direto de aportes com débito automático da conta bancária de origem e integração com a carteira de patrimônio (Renda Fixa: Poupança, CDB, LCI/LCA, Tesouro Direto, Fundos; Renda Variável: Ações, ETFs, FIIs, Subscrições).
- **Subdivisão Estruturada:**
  - *Entradas:* Ganhos Fixos (Salário) e Ganhos Variáveis (Pix, Vendas, Freela, etc.).
  - *Saídas:* Gastos Fixos e Gastos Variáveis.

### 4. Camada de Persistência e Banco de Dados Relacional
- **Multi-Driver Suportado:** Engine SQLAlchemy 2.x com detecção automática e normalização de `DATABASE_URL`:
  - PostgreSQL / Supabase: `postgresql+psycopg2://...` com pooler PgBouncer e `sslmode=require`.
  - MySQL / TiDB Cloud: `mysql+pymysql://...` com TLS 1.3 nativo (`ssl.create_default_context()`).
  - SQLite: `sqlite:///:memory:` para execução instantânea dos 80 testes automatizados.
- **Versionamento com Alembic:** 16 revisões históricas incrementais gerenciadas em `banco de dados/migrations/versions/`.

---

## 📁 Árvore Completa de Diretórios do Projeto

```text
fluxo_caixas/
├── backend/                            # Núcleo da API REST e regras de negócio
│   ├── rotasdeapi/                     # Controladores REST modulares
│   │   ├── usuario.py                  # Cadastro, login OAuth2, OTP por e-mail, perfil e exclusão
│   │   ├── conta_bancaria.py           # Gestão de contas (corrente, poupança, investimento)
│   │   ├── fluxo_dinheiro.py           # Movimentações, transferências e aportes de investimentos
│   │   ├── calculo_financeiro.py       # Consolidação periódica de relatórios (diário, mensal, anual)
│   │   ├── meta_financeira.py          # Metas de economia com evolução percentual
│   │   ├── orcamentos_alertas.py       # Tetos por categoria, acompanhamento e alertas de vencimento
│   │   └── readme.md                   # Catálogo técnico detalhado de rotas e contratos
│   ├── seguranca/                      # Segurança e criptografia de credenciais
│   │   ├── seguranca.py                # Hashing e verificação de senhas (Argon2id / Bcrypt)
│   │   └── readme.md                   # Manual de segurança e proteção de senhas
│   ├── servicos/                       # Serviços auxiliares e utilitários
│   │   ├── email.py                    # Envio defensivo de e-mails via SMTP com STARTTLS
│   │   └── __init__.py                 # Exportador de serviços
│   ├── tests/                          # Suíte de testes automatizados (80 testes passing)
│   │   ├── conftest.py                 # Fixtures globais, banco em memória e TestClient FastAPI
│   │   ├── test_cadastro_usuario.py    # Validação de CPF, complexidade de senha e integridade
│   │   ├── test_cors.py                # Preflight CORS, allowlist e ambientes dev/prod
│   │   ├── test_dados_sensiveis.py     # Cifragem Fernet, Blind Index HMAC e privacidade LGPD
│   │   ├── test_financeiro.py          # Precisão Decimal, saldo disponível e transferências
│   │   ├── test_fluxo_integracao.py    # Fluxo end-to-end completo da aplicação
│   │   ├── test_limites_requisicoes.py # Testes de rate limit (HTTP 429) e janelas temporais
│   │   ├── test_metas_relatorios.py    # Testes de metas financeiras e relatórios consolidados
│   │   ├── test_orcamentos_alertas.py  # Testes de tetos orçamentários e regras de alertas
│   │   ├── test_mysql_concorrencia.py  # Testes de concorrência com bloqueio pessimista
│   │   └── README.md                   # Guia de execução da suíte de testes
│   ├── api.py                          # Ponto de montagem FastAPI, CORS, middlewares e healthcheck
│   ├── autenticacao.py                 # Emissão, decodificação e validação de tokens JWT
│   ├── configuracao.py                 # Carregamento tipado e seguro de variáveis de ambiente
│   ├── dados_sensiveis.py              # Implementação Fernet AES-128 e Blind Index HMAC
│   ├── database.py                     # Normalização de URL, SSLContext e engine SQLAlchemy 2.x
│   ├── esquema.py                      # Modelos de validação de dados Pydantic v2
│   ├── financeiro.py                   # Motor de cálculos contábeis e recálculo de saldos
│   ├── models.py                       # Entidades relacionais ORM (10 tabelas mapeadas)
│   └── readme.md                       # Documentação interna da camada backend
│
├── banco de dados/                     # Esquema relacional e migrações Alembic
│   ├── migrations/                     # Histórico versionado de migrações
│   │   ├── versions/                   # 16 arquivos de migração cronológica
│   │   ├── env.py                      # Contexto online/offline de migrações
│   │   └── README.md                   # Guia de comandos e operações Alembic
│   ├── alembic.ini                     # Configuração global do Alembic
│   ├── *.sql                           # Dumps e scripts DDL de referência
│   └── readme.md                       # Diagrama de relacionamentos e dicionário de dados
│
├── frontend/                           # Aplicação Web SPA Estática (hospedada na Vercel)
│   ├── css/
│   │   └── style.css                   # Design system corporativo, variáveis e responsividade
│   ├── js/
│   │   ├── api.js                      # Cliente HTTP com detecção de ambiente e hook de modais
│   │   ├── cadastro.js                 # Validação client-side, máscaras e cadastro de usuário
│   │   ├── dashboard.js                # Orquestração do painel, gráficos, filtros e modais
│   │   └── login.js                    # Autenticação OAuth2, sessão e recuperação de senha
│   ├── index.html                      # Dashboard financeiro principal autenticado
│   ├── login.html                      # Tela de login
│   ├── cadastro.html                   # Tela de criação de conta
│   └── README.md                       # Documentação do frontend e deploy na Vercel
│
├── scripts/                            # Scripts utilitários de administração e manutenção
│   ├── migrar_para_supabase.py         # Migração ponta a ponta para Supabase PostgreSQL
│   ├── supabase_schema_completo.sql    # DDL estruturado para o SQL Editor do Supabase
│   ├── remover_usuario_teste.py        # Exclusão segura e transacional de usuários de teste
│   └── README.md                       # Guia de uso dos utilitários
│
├── .env.example                        # Template documentado de variáveis de ambiente
├── .gitignore                          # Exclusões de versionamento do Git
├── .vercelignore                       # Filtro de deploy estático da Vercel
├── ESTRUTURA.md                        # Este documento arquitetural
├── main.py                             # Ponto de entrada unificado para execução local
├── pytest.ini                          # Configuração de descoberta do Pytest
├── README.md                           # Documentação principal do repositório no GitHub
├── requirements.txt                    # Dependências Python fixadas
└── vercel.json                         # Roteamento e rewrites estáticos da Vercel
```
