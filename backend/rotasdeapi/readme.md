# 🧭 Catálogo de Rotas da API — Fluxo de Caixa

> ⚡ **Base URL em Produção (Render):** `https://fluxo-caixa-cuq1.onrender.com`  
> 💻 **Base URL Local:** `http://127.0.0.1:8000`  
> 📖 **Documentação Interativa (Swagger UI):** [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs)

Este documento descreve todos os endpoints REST expostos pela API do **Sistema de Fluxo de Caixa**, seus formatos de requisição, regras de validação, segurança e respostas.

---

## 🔐 Padrões Globais

- **Autenticação:** Padrão OAuth2 Bearer Token (`Authorization: Bearer <access_token>`).
- **Isolamento de Dados:** O `usuario_id` é sempre obtido do token JWT assinado; nenhum endpoint aceita `usuario_id` arbitrário vindo do cliente.
- **Precisão Financeira:** Valores monetários processados com tipo `Decimal(12, 2)`.
- **Paginação nas Listagens:** Suporte aos query parameters `limit` (padrão `50`, máximo `100`) e `offset` (padrão `0`).

---

## 👤 1. Usuários e Autenticação (`usuario.py`)

### `POST /usuarios/`
Registra um novo usuário com validação algorítmica de CPF, complexidade de senha e envio de e-mail de boas-vindas com código de confirmação.
- **Autenticação:** Pública (com rate limit por IP).
- **Body (`application/json`):**
  ```json
  {
    "nome_completo": "Arthur Rocha",
    "cpf": "12345678909",
    "email": "arthur@exemplo.com",
    "senha": "SenhaForte@2026",
    "telefone": "11987654321"
  }
  ```
- **Regras de Validação:**
  - `cpf`: 11 dígitos numéricos com dígitos verificadores válidos (cifrado com Fernet AES-128 e indexado por Blind Index HMAC-SHA256).
  - `senha`: Mínimo de 8 caracteres, contendo letra maiúscula, minúscula, número e caractere especial (hasheada com Argon2id/Bcrypt).
  - `telefone`: Opcional (10 ou 11 dígitos), cifrado com Fernet.
- **Resposta (`201 Created`):** Retorna `id`, `nome_completo`, `email`, `telefone`, `email_confirmado` e `criado_em`.

### `POST /usuarios/confirmar-email`
Valida o código OTP de 6 dígitos enviado por e-mail para ativar a confirmação cadastral.
- **Body (`application/json`):** `{"email": "arthur@exemplo.com", "codigo": "123456"}`

### `POST /login`
Autentica o usuário e emite o token JWT com controle anti-força bruta.
- **Autenticação:** Pública (protegida por rate limit: máx. 5 falhas em 15 min por IP/conta → `HTTP 429`).
- **Body (`application/x-www-form-urlencoded`):**
  - `username`: e-mail cadastrado
  - `password`: senha do usuário
- **Resposta (`200 OK`):** `{"access_token": "...", "token_type": "bearer"}`

### `POST /usuarios/esqueci-senha`
Gera código OTP seguro e envia por e-mail para recuperação de acesso.

### `POST /usuarios/redefinir-senha`
Redefine a senha do usuário mediante validação criptográfica do e-mail, código OTP e nova senha forte.

### `GET /usuarios/me`
Retorna os dados cadastrais do usuário autenticado.

### `PUT /usuarios/me`
Atualiza dados de perfil do usuário logado (`nome_completo`, `telefone`).

### `DELETE /usuarios/me`
Exclui a conta do usuário logado e remove em cascata todas as suas contas bancárias, movimentações e registros vinculados. Exige confirmação de senha no payload.

### `GET /usuarios/`
Lista usuários cadastrados no sistema (endpoint administrativo protegido por Bearer JWT).

### `GET /usuarios/{usuario_id}`
Detalha o cadastro de um usuário específico por ID.

### `DELETE /usuarios/{usuario_id}`
Remove um usuário específico por ID com exclusão segura em cascata de seus dados.

---

## 🏦 2. Contas Bancárias (`conta_bancaria.py`)

### `POST /contas-bancarias/`
Cria uma nova conta bancária para o usuário logado.
- **Body (`application/json`):**
  ```json
  {
    "nome_banco": "Nubank",
    "tipo_conta": "corrente",
    "saldo_inicial": 1500.00
  }
  ```
- **Tipos aceitos:** `corrente`, `poupanca`, `investimento`.
- **Comportamento:** Se `saldo_inicial > 0`, cria automaticamente um lançamento de saldo inicial.

### `GET /contas-bancarias/`
Lista as contas do usuário com `valor_conta_atual` recalculado dinamicamente.

### `PUT /contas-bancarias/{conta_id}`
Atualiza dados cadastrais da conta (`nome_banco`, `tipo_conta`, `ativa`).

### `DELETE /contas-bancarias/{conta_id}`
Remove a conta bancária (bloqueia exclusão caso existam transferências ativas vinculadas a outra conta).

---

## 💸 3. Fluxo de Dinheiro e Investimentos (`fluxo_dinheiro.py`)

### `POST /fluxo-dinheiro/`
Registra movimentações financeiras, transferências atômicas ou aportes de investimento.
- **Tipos (`tipo`):**
  - `entrada`: Ganhos Financeiros. Subdividido no frontend em **Ganhos Fixos** (`salario`) e **Ganhos Variáveis** (`vendas`, `freelance`, `outros`, etc.).
  - `saida`: Despesas. Subdividido em **Gastos Fixos** e **Gastos Variáveis**. Valida saldo disponível em contas `poupanca` e `investimento`.
  - `investimento`: Aporte financeiro em ativos. O valor é **debitado automaticamente da conta de origem**, integrado à carteira de patrimônio e classificado pelo ativo correspondente:
    - *Renda Fixa:* `Poupança`, `CDB`, `LCI/LCA`, `Tesouro Direto`, `Fundos de Investimento`
    - *Renda Variável:* `Ações`, `ETFs`, `FIIs`, `Subscrições`
  - `ajuste`: Conciliação contábil (positivo ou negativo).
  - `transferencia`: Transfere fundos entre duas contas do usuário de forma atômica gerando par vinculado por `transferencia_id`.

### `GET /fluxo-dinheiro/`
Retorna o extrato de movimentações com paginação e filtros combinados (`conta_id`, `tipo`, `categoria`, `data_inicio`, `data_fim`).

### `PUT /fluxo-dinheiro/{movimentacao_id}`
Atualiza os atributos de um lançamento e recalcula instantaneamente os saldos das contas envolvidas.

### `DELETE /fluxo-dinheiro/{movimentacao_id}`
Exclui a movimentação. Se pertencer a uma transferência, remove atomicamente ambas as pontas (origem e destino).

---

## 📊 4. Cálculos Financeiros (`calculo_financeiro.py`)

### `POST /calculos-financeiros/`
Gera e persiste o balanço contábil consolidado de uma conta por período (`diario`, `semanal`, `mensal`, `anual`).

### `GET /calculos-financeiros/`
Lista o histórico de relatórios de conciliação e balanços consolidados.

---

## 🎯 5. Metas Financeiras (`meta_financeira.py`)

- `POST /metas-financeiras/`: Cria uma meta de economia (`nome_meta`, `valor_desejado`, `valor_atual`, `data_limite`).
- `GET /metas-financeiras/`: Lista as metas do usuário.
- `PUT /metas-financeiras/{meta_id}`: Registra aportes ou atualiza dados; define `status = "concluida"` quando `valor_atual >= valor_desejado`.
- `DELETE /metas-financeiras/{meta_id}`: Exclui a meta.

---

## 🔔 6. Orçamentos e Alertas Proativos (`orcamentos_alertas.py`)

### `GET /orcamentos`
Lista os orçamentos do mês corrente ou especificado (`?mes=2026-10`), com total gasto, percentual atingido e saldo restante.

### `POST /orcamentos`
Cria ou atualiza teto de gastos por categoria para determinado mês.
- **Body (`application/json`):**
  ```json
  {
    "categoria": "alimentacao",
    "limite_mensal": 1200.00,
    "mes_referencia": "2026-10"
  }
  ```

### `PUT /orcamentos/{item_id}`
Edita o limite mensal de um orçamento existente.

### `DELETE /orcamentos/{item_id}`
Exclui o teto orçamentário.

### `GET /alertas`
Retorna alertas consolidados para o Dashboard:
- Orçamentos que atingiram 80% ou 100% do teto.
- Contas/saídas com vencimento programado nos próximos 7 dias.

### `PUT /alertas/lido`
Registra a marcação de um alerta como lido para não reaparecer na interface.

### `GET /alertas/preferencias` & `PUT /alertas/preferencias`
Consulta e atualiza as preferências de notificação do usuário (ex: ativar/desativar avisos de vencimento).

---

## 🩺 7. Sistema e Monitoramento (`api.py`)

- `GET /`: Confirmação de status operacional da API.
- `GET /health`: Healthcheck detalhado (`{"status": "healthy", "ambiente": "production|development", "versao": "1.0.0"}`).
