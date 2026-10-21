# 🗄️ Modelagem de Banco de Dados — Fluxo de Caixa

Este documento é a referência completa da modelagem relacional, tabelas, relacionamentos e dicionário de dados do **Sistema de Fluxo de Caixa**.

---

## 📊 Diagrama Entidade-Relacionamento (ERD)

```mermaid
erDiagram
    usuarios ||--o{ contas_bancarias : "possui"
    usuarios ||--o{ metas_financeiras : "define"
    contas_bancarias ||--o{ fluxo_dinheiro : "registra"
    contas_bancarias ||--o{ calculos_financeiros : "consolida"
    categorias_movimentacao ||--o{ fluxo_dinheiro : "classifica"

    usuarios {
        int id PK
        string nome_completo
        string cpf "Cifrado Fernet"
        string cpf_indice UK "HMAC-SHA256"
        string email UK
        string telefone "Opcional Cifrado"
        string senha_hash "Argon2/Bcrypt"
        datetime criado_em
    }

    contas_bancarias {
        int id PK
        int usuario_id FK
        string nome_banco
        enum tipo_conta "corrente, poupanca, investimento"
        decimal valor_conta_atual
        boolean ativa
        datetime criado_em
    }

    fluxo_dinheiro {
        int id PK
        int conta_bancaria_id FK
        string descricao
        decimal valor
        enum tipo "entrada, saida, transferencia, ajuste"
        string categoria FK
        date data_movimentacao
        string observacao
        string transferencia_id "UUID do par"
        enum transferencia_direcao "origem, destino"
        int conta_destino_id FK
    }

    categorias_movimentacao {
        int id PK
        string nome UK
    }

    calculos_financeiros {
        int id PK
        int conta_bancaria_id FK
        enum tipo_calculo "diario, semanal, mensal, anual"
        date data_inicio
        date data_fim
        decimal total_entradas
        decimal total_saidas
        decimal total_investimentos
        decimal saldo_final
    }

    metas_financeiras {
        int id PK
        int usuario_id FK
        string nome_meta
        decimal valor_desejado
        decimal valor_atual
        date data_limite
        enum status "em_andamento, concluida"
    }

    tentativas_login {
        int id PK
        string chave_tentativa UK "Hash IP ou E-mail"
        int total_falhas
        datetime ultima_falha
        datetime bloqueado_ate
    }
```

---

## 📋 Dicionário de Dados das Tabelas

### 1. `usuarios`
Armazena a identidade dos usuários do sistema.

| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Identificador único do usuário |
| `nome_completo` | `VARCHAR(150)` | `NOT NULL` | Nome informado no cadastro |
| `cpf` | `VARCHAR(255)` | `NOT NULL, UNIQUE` | CPF cifrado com algoritmo Fernet |
| `cpf_indice` | `VARCHAR(64)` | `NOT NULL, UNIQUE` | Hash cego HMAC-SHA256 para checar duplicatas |
| `email` | `VARCHAR(100)` | `NOT NULL, UNIQUE` | E-mail para login |
| `telefone` | `VARCHAR(255)` | `NULLABLE` | Telefone opcional cifrado com Fernet |
| `senha_hash` | `VARCHAR(255)` | `NOT NULL` | Hash seguro da senha gerado com `pwdlib` |
| `criado_em` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Data e hora de criação da conta |

### 2. `contas_bancarias`
Representa as contas financeiras geridas por cada usuário.

| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Identificador único da conta |
| `usuario_id` | `INT` | `FOREIGN KEY (usuarios.id)` | Usuário proprietário da conta |
| `nome_banco` | `VARCHAR(100)` | `NOT NULL` | Nome do banco ou instituição financeira |
| `tipo_conta` | `ENUM` | `'corrente', 'poupanca', 'investimento'` | Modalidade da conta bancária |
| `valor_conta_atual` | `DECIMAL(12,2)` | `DEFAULT 0.00` | Saldo recalculado e consolidado |
| `ativa` | `BOOLEAN` | `DEFAULT TRUE` | Status ativo ou inativo da conta |
| `criado_em` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` | Data de criação |

### 3. `fluxo_dinheiro`
Registra cada movimentação, receita, despesa, ajuste ou transferência.

| Coluna | Tipo | Restrições | Descrição |
|---|---|---|---|
| `id` | `INT` | `PRIMARY KEY, AUTO_INCREMENT` | Identificador único da movimentação |
| `conta_bancaria_id`| `INT` | `FOREIGN KEY (contas_bancarias.id)` | Conta de origem da transação |
| `descricao` | `VARCHAR(200)` | `NOT NULL` | Descrição informativa |
| `valor` | `DECIMAL(12,2)` | `NOT NULL` | Valor monetário movimentado |
| `tipo` | `ENUM` | `'entrada', 'saida', 'transferencia', 'ajuste'` | Classificação da operação |
| `categoria` | `VARCHAR(100)` | `NOT NULL` | Categoria normalizada |
| `data_movimentacao`| `DATE` | `NOT NULL` | Data contábil da operação |
| `transferencia_id` | `VARCHAR(36)` | `NULLABLE` | UUID compartilhado pelo par da transferência |
| `transferencia_direcao`| `ENUM` | `'origem', 'destino', NULL` | Sentido do fluxo na conta corrente |
| `conta_destino_id` | `INT` | `NULLABLE, FK (contas_bancarias.id)` | Conta destino em transferências |

---

## ⚙️ Integridade e Versionamento via Alembic

> [!IMPORTANT]
> **Nunca execute arquivos `.sql` brutos em bases de produção!**  
> Os arquivos `.sql` presentes na pasta são dumps legados de referência. A única fonte oficial da verdade do esquema do banco de dados são as **migrações do Alembic** localizadas em [`migrations/`](migrations/).

Para atualizar seu banco com as versões oficiais mais recentes:

```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```
