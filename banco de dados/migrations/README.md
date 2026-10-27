# 🔄 Migrações de Banco de Dados — Alembic

Esta pasta contém a infraestrutura oficial de migrações do **Alembic**, responsável por versionar e evoluir o esquema do banco de dados do **Sistema de Fluxo de Caixa** tanto localmente quanto no deploy automatizado em nuvem (Render + Supabase PostgreSQL / TiDB Cloud).

---

## 📁 Estrutura

```text
migrations/
├── env.py                  # Configuração do contexto Alembic (injeta backend/ no sys.path)
├── script.py.mako          # Template padrão para geração de novas revisões
├── versions/               # 9 revisões sequenciais do esquema (incluindo schema_unificado_supabase)
│   └── README.md           # Árvore de dependências e detalhamento de cada revisão
└── README.md               # Este guia operacional
```

---

## 🚀 Comandos Operacionais

Execute todos os comandos a partir da **raiz do repositório**:

### 1. Aplicar Todas as Migrações (`upgrade head`)
```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

### 2. Consultar a Revisão Atual do Banco
```powershell
python -m alembic -c "banco de dados/alembic.ini" current
```

### 3. Visualizar o Histórico Completo
```powershell
python -m alembic -c "banco de dados/alembic.ini" history --verbose
```

### 4. Gerar uma Nova Revisão
```powershell
python -m alembic -c "banco de dados/alembic.ini" revision -m "descricao_da_mudanca"
```

---

## ☁️ Execução Automática no Render (CI/CD)

No ambiente de produção do **Render**, o **Start Command** executa automaticamente `upgrade head` antes de iniciar o servidor Uvicorn:

```bash
python -m alembic -c "banco de dados/alembic.ini" upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT
```

O arquivo [`env.py`](env.py) importa `DATABASE_URL` e `engine` diretamente de [`backend/database.py`](../../backend/database.py), herdando a normalização automática da URL e o contexto TLS/SSL nativo para conectar ao **TiDB Cloud Serverless**.
