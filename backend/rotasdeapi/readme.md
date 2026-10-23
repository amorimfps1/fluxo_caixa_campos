# 🧭 Catálogo de Rotas da API — Fluxo de Caixa

> ⚡ **Base URL em Produção (Render):** `https://fluxo-caixa-cuq1.onrender.com`  
> 💻 **Base URL Local:** `http://127.0.0.1:8000`  
> 📖 **Documentação Interativa (Swagger UI):** [https://fluxo-caixa-cuq1.onrender.com/docs](https://fluxo-caixa-cuq1.onrender.com/docs)

Este documento descreve todos os endpoints REST expostos pela API do **Sistema de Fluxo de Caixa**, seus formatos de requisição, regras de validação e respostas.

---

## 🔐 Padrões Globais

- **Autenticação:** Padrão OAuth2 Bearer Token (`Authorization: Bearer <access_token>`).
- **Isolamento de Dados:** O `usuario_id` é sempre obtido do token JWT assinado; nenhum endpoint aceita `usuario_id` vindo do cliente.
- **Paginação nas Listagens:** Suporte aos query parameters `limit` (padrão `50`, máximo `100`) e `offset` (padrão `0`).

---

## 👤 1. Usuários e Autenticação (`usuario.py`)

### `POST /usuarios/`
Registra um novo usuário com validação algorítmica de CPF e complexidade de senha.
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
  - `cpf`: 11 dígitos numéricos ASCII com dígitos verificadores válidos (cifrado com Fernet antes de salvar).
  - `senha`: Mínimo de 8 caracteres, contendo letra maiúscula, minúscula, número e caractere especial.
  - `telefone`: Opcional (10 ou 11 dígitos), também cifrado com Fernet.
- **Resposta (`201 Created`):** Retorna `id`, `nome_completo`, `email`, `telefone` e `criado_em` (o CPF nunca é exposto).

### `POST /login`
Autentica o usuário e emite o token JWT.
- **Autenticação:** Pública (protegida por rate limit: máx. 5 falhas em 15 min por IP/conta → `HTTP 429`).
- **Body (`application/x-www-form-urlencoded`):**
  - `username`: e-mail cadastrado
  - `password`: senha do usuário
- **Resposta (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

### `GET /usuarios/me`
Retorna os dados cadastrais do usuário autenticado.
- **Autenticação:** Bearer JWT.

### `POST /usuarios/redefinir-senha`
Redefine a senha do usuário mediante validação criptográfica do e-mail e do CPF cadastrado.
- **Autenticação:** Pública (protegida por rate limit anti-força bruta por IP e conta + comparação HMAC em tempo constante).
- **Body (`application/json`):**
  ```json
  {
    "email": "arthur@exemplo.com",
    "cpf": "123.456.789-09",
    "nova_senha": "NovaSenhaForte@2026"
  }
  ```
- **Resposta (`200 OK`):** `{"mensagem": "Senha redefinida com sucesso."}`

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
- **Comportamento:** Se `saldo_inicial > 0`, cria automaticamente uma movimentação inicial vinculada à conta.

### `GET /contas-bancarias/`
Lista as contas do usuário com `valor_conta_atual` sincronizado.
- **Query Params:** `ativa` (booleano opcional), `limit`, `offset`.

### `PUT /contas-bancarias/{conta_id}`
Atualiza `nome_banco`, `tipo_conta` ou status `ativa`.

### `DELETE /contas-bancarias/{conta_id}`
Remove a conta bancária (bloqueia exclusão caso existam transferências vinculadas a outra conta ativa do usuário).

---

## 💸 3. Fluxo de Dinheiro (`fluxo_dinheiro.py`)

### `POST /fluxo-dinheiro/`
Registra uma movimentação financeira ou transferência entre contas.
- **Tipos (`tipo`):**
  - `entrada`: Receitas (valor positivo).
  - `saida`: Despesas (valor positivo; valida saldo disponível em contas `poupanca` e `investimento`).
  - `ajuste`: Conciliação contábil (aceita valor positivo ou negativo diferente de zero).
  - `transferencia`: Transfere valor de `conta_bancaria_id` (origem) para `conta_destino_id` (destino) em uma transação atômica com par vinculado (`transferencia_id`).
- **Categorias permitidas (`categoria`):** `alimentacao`, `ajuste`, `compras`, `contas`, `educacao`, `freelance`, `impostos`, `investimento`, `lazer`, `moradia`, `outros`, `salario`, `saude`, `transporte`, `transferencia`, `vendas`.

### `GET /fluxo-dinheiro/`
Retorna o extrato de movimentações do usuário.
- **Filtros opcionais:** `conta_id`, `tipo`, `categoria`, `data_inicio`, `data_fim`, `limit`, `offset`.

### `PUT /fluxo-dinheiro/{movimentacao_id}`
Atualiza descrição, valor, tipo, categoria, data ou observação de um lançamento e recalcula o saldo da conta.

### `DELETE /fluxo-dinheiro/{movimentacao_id}`
Remove a movimentação. Caso pertença a uma transferência (`transferencia_id`), remove ambas as pontas (origem e destino) e atualiza os saldos das duas contas na mesma transação.

---

## 📊 4. Cálculos Financeiros (`calculo_financeiro.py`)

### `POST /calculos-financeiros/`
Consolida e grava o balanço de uma conta em um período (`diario`, `semanal`, `mensal`, `anual`).
- **Fórmula Contábil:**
  $$\text{Saldo Final} = \text{Entradas} - \text{Saídas} + \text{Transferências Recebidas} - \text{Transferências Enviadas} + \text{Ajustes}$$

### `GET /calculos-financeiros/`
Lista o histórico de cálculos consolidados do usuário.

---

## 🎯 5. Metas Financeiras (`meta_financeira.py`)

- `POST /metas-financeiras/`: Cria meta com `nome_meta`, `valor_desejado`, `valor_atual` e `data_limite`.
- `GET /metas-financeiras/`: Lista metas com filtro opcional por `status` (`em_andamento` ou `concluida`).
- `PUT /metas-financeiras/{meta_id}`: Atualiza valores/dados; promove automaticamente `status` para `concluida` quando `valor_atual >= valor_desejado`.
- `DELETE /metas-financeiras/{meta_id}`: Exclui a meta financeira.

---

## 🩺 6. Sistema (`api.py`)

- `GET /`: Confirmação de disponibilidade da API.
- `GET /health`: Retorna `{"status": "healthy", "ambiente": "production|development", "versao": "1.0.0"}`.
