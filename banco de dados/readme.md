# 🗄️ Banco de Dados — Fluxo de Caixa

Este módulo descreve a estrutura do banco de dados do sistema e a responsabilidade de cada tabela.

O banco principal do projeto é `fluxo_caixa` e ele foi organizado para suportar usuários, contas, categorias fixas, movimentações, cálculos financeiros, metas e controle de tentativas de login.

---

## 📊 Visão geral

O esquema atual possui 7 tabelas:

1. `usuarios`
2. `contas_bancarias`
3. `categorias_movimentacao`
4. `fluxo_dinheiro`
5. `calculos_financeiros`
6. `metas_financeiras`
7. `tentativas_login`

---

## 1. Tabela `usuarios`

Armazena os dados pessoais e de autenticação dos usuários.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INT | Identificador único do usuário |
| `nome_completo` | VARCHAR(150) | Nome completo |
| `cpf` | VARCHAR(255) | CPF cifrado com Fernet |
| `cpf_indice` | VARCHAR(64) | Índice HMAC para detectar duplicatas |
| `email` | VARCHAR(100) | E-mail principal |
| `telefone` | VARCHAR(255), NULL | Telefone opcional cifrado com Fernet |
| `senha_hash` | VARCHAR(255) | Senha em formato seguro |
| `criado_em` | TIMESTAMP | Data de criação |

### Função

Essa tabela identifica quem usa o sistema e guarda os dados essenciais para cadastro e autenticação.

O CPF é dado pessoal: é cifrado com Fernet usando `CPF_ENCRYPTION_KEY`, e a
API não o inclui nas respostas. O índice HMAC também depende dessa chave.
Proteja a chave e mantenha backup seguro; perder ou trocar a chave sem
recifragem impede recuperar e consultar corretamente os CPFs armazenados.

---

## 2. Tabela `contas_bancarias`

Armazena as contas financeiras vinculadas a cada usuário.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INT | Identificador da conta |
| `usuario_id` | INT | Usuário proprietário |
| `nome_banco` | VARCHAR(100) | Nome do banco |
| `tipo_conta` | ENUM | Corrente, poupança ou investimento |
| `valor_conta_atual` | DECIMAL(12,2) | Saldo atual |
| `ativa` | BOOLEAN | Conta ativa/inativa |
| `criado_em` | TIMESTAMP | Data de criação |

### Relacionamento

```text
usuarios
   │
   └── contas_bancarias
         └── vários registros por usuário
```

---

## 3. Tabela `fluxo_dinheiro`

Registra todas as movimentações financeiras registradas na conta.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INT | Identificador da movimentação |
| `conta_bancaria_id` | INT | Conta relacionada |
| `descricao` | VARCHAR(200) | Descrição da operação |
| `valor` | DECIMAL(12,2) | Valor movimentado |
| `tipo` | ENUM | Entrada, saída, transferência ou ajuste |
| `categoria` | VARCHAR(100) | Categoria permitida na tabela de categorias |
| `data_movimentacao` | DATE | Data da operação |
| `observacao` | VARCHAR(255) | Informações adicionais |
| `transferencia_id` | VARCHAR(36), NULL | Identificador compartilhado pelas pontas da transferência |
| `transferencia_direcao` | ENUM, NULL | Indica `origem` ou `destino` |
| `conta_destino_id` | INT, NULL | Conta contraparte da transferência |

Para `entrada` e `saida`, `valor` é positivo. Para `ajuste`, o valor é
assinado: positivo aumenta o saldo e negativo o reduz. A categoria deve ser
`ajuste`. Uma transferência é armazenada como duas movimentações vinculadas;
transferências não contam como renda ou gasto nos totais comuns.

### Exemplos

- salário → entrada
- aluguel → saída
- investimento → saída
- transferência entre contas → dois lançamentos vinculados (origem e destino)

---

## 4. Tabela `categorias_movimentacao`

Mantém as categorias fixas aceitas pela API. A tabela `fluxo_dinheiro`
referencia uma delas; não são criadas categorias livres durante uma requisição.
Os nomes são convertidos para minúsculas e sem acentos, `investimentos` vira
`investimento`, e valores legados desconhecidos ou vazios são convertidos em
`outros`.

Categorias disponíveis: `alimentacao`, `ajuste`, `compras`, `contas`,
`educacao`, `freelance`, `impostos`, `investimento`, `lazer`, `moradia`,
`outros`, `salario`, `saude`, `transporte`, `transferencia` e `vendas`.
`ajuste` e `transferencia` são reservadas para seus respectivos tipos.

| Campo | Tipo | Descrição |
|---|---|---|
| `nome` | VARCHAR(100) | Nome normalizado e chave primária |

---

## 5. Tabela `calculos_financeiros`

Armazena os resultados gerados pelos cálculos financeiros por período.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INT | Identificador do cálculo |
| `conta_bancaria_id` | INT | Conta analisada |
| `tipo_calculo` | ENUM | Diário, semanal, mensal ou anual |
| `data_inicio` | DATE | Início do período |
| `data_fim` | DATE | Fim do período |
| `valor_original` | DECIMAL(12,2) | Saldo no início |
| `total_entradas` | DECIMAL(12,2) | Soma das entradas |
| `total_saidas` | DECIMAL(12,2) | Soma das saídas |
| `total_investimentos` | DECIMAL(12,2) | Soma dos investimentos |
| `total_transferencias_recebidas` | DECIMAL(12,2) | Transferências recebidas no período |
| `total_transferencias_enviadas` | DECIMAL(12,2) | Transferências enviadas no período |
| `total_ajustes` | DECIMAL(12,2) | Soma assinada dos ajustes do período |
| `valor_final` | DECIMAL(12,2) | Saldo final |
| `criado_em` | TIMESTAMP | Data de registro |

### Fórmula utilizada

```text
valor_final = valor_original + total_entradas - total_saidas
              + total_transferencias_recebidas
              - total_transferencias_enviadas + total_ajustes
```

Os investimentos já fazem parte do total de saídas; `total_investimentos` é um detalhamento e não deve ser subtraído uma segunda vez.

---

## 6. Tabela `metas_financeiras`

Armazena os objetivos financeiros definidos pelos usuários.

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | INT | Identificador da meta |
| `usuario_id` | INT | Usuário responsável |
| `nome` | VARCHAR(150) | Nome da meta |
| `valor_meta` | DECIMAL(12,2) | Valor desejado |
| `valor_atual` | DECIMAL(12,2) | Valor acumulado |
| `data_inicio` | DATE | Data de início |
| `data_limite` | DATE | Prazo da meta |
| `status` | ENUM | Em andamento, concluída ou cancelada |
| `descricao` | VARCHAR(255) | Observações |
| `criado_em` | TIMESTAMP | Data de criação |

### Exemplo

- meta: reserva de emergência
- valor_meta: R$ 10.000,00
- valor_atual: R$ 6.500,00
- status: em_andamento

---

## 7. Tabela `tentativas_login`

Mantém a janela de falhas de autenticação por endereço cliente para aplicar o
limite de cinco falhas em 15 minutos. O IP não é armazenado em texto:
`chave_cliente` guarda seu hash SHA-256.

| Campo | Tipo | Descrição |
|---|---|---|
| `chave_cliente` | VARCHAR(64) | Hash SHA-256 do endereço cliente, chave primária |
| `tentativas` | INT | Número de falhas na janela atual |
| `inicio_janela` | DATETIME | Início da janela de 15 minutos |
| `bloqueado_ate` | DATETIME, NULL | Momento em que termina o bloqueio |

---

## 🔗 Relacionamento entre as tabelas

```text
usuarios ──┬── contas_bancarias
           └── metas_financeiras

contas_bancarias ──> fluxo_dinheiro ──> calculos_financeiros
                           │
                           └── categorias_movimentacao

tentativas_login (controle operacional do login)
```

---

## ✅ Resumo das tabelas

| Tabela | Responsabilidade |
|---|---|
| `usuarios` | dados do usuário e credenciais |
| `contas_bancarias` | contas financeiras do usuário |
| `categorias_movimentacao` | categorias normalizadas dos lançamentos |
| `fluxo_dinheiro` | movimentações financeiras |
| `calculos_financeiros` | resultados por período |
| `metas_financeiras` | objetivos financeiros |
| `tentativas_login` | contagem temporária de falhas de login por endereço |

---

## 🧩 Observação

O esquema oficial é mantido pelas migrações Alembic em `migrations/`, configuradas por `alembic.ini`. Os arquivos `.sql` desta pasta são dumps legados e podem conter `DROP TABLE`; não os execute em um banco com dados.

Execute os comandos a partir da raiz do repositório. Para um banco novo, aplique as migrações com `python -m alembic -c "banco de dados/alembic.ini" upgrade head`. Para adotar Alembic em um banco existente, faça backup, confira se o esquema corresponde ao baseline e siga o procedimento descrito no README principal antes de marcar a revisão inicial.
