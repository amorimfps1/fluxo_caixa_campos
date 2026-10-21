# 🧭 Catálogo de Rotas da API — Fluxo de Caixa

Este documento é a referência completa de endpoints REST expostos pela API do **Sistema de Fluxo de Caixa**.

---

## 🔐 Padrões de Autenticação e Autorização

- **Formato do Token:** Tokens emitidos são no padrão JWT com algoritmo HMAC-SHA256.
- **Cabeçalho de Envio:** Requisições para rotas protegidas devem incluir:
  ```http
  Authorization: Bearer <seu_access_token>
  ```
- **Identificação do Proprietário:** Todas as operações que consultam, criam, atualizam ou removem recursos filtram estritamente pelo ID do usuário extraído do token JWT. O cliente não precisa e nem pode especificar o `usuario_id` no corpo da requisição.
- **Paginação:** As rotas de listagem suportam os seguintes query parameters padrão:
  - `limit` (padrão: `50`, máximo: `100`)
  - `offset` (padrão: `0`)

---

## 👤 1. Módulo de Usuários e Autenticação (`usuario.py`)

**Prefixo Base:** `/usuarios` | **Tags:** `Usuários`

### `POST /usuarios/`
Cadastra um novo usuário no sistema.
- **Autenticação:** Pública
- **Rate Limit:** Limite por IP para prevenir ataques de criação automatizada de contas.
- **Body:**
  ```json
  {
    "nome_completo": "Arthur Rocha",
    "cpf": "12345678909",
    "email": "arthur@exemplo.com",
    "senha": "SenhaForte@2026",
    "telefone": "11987654321"
  }
  ```
- **Regras:**
  - O CPF deve conter exatamente 11 dígitos numéricos ASCII válidos pelos dígitos verificadores.
  - O telefone é opcional. Ambos são cifrados com Fernet antes de persistir no banco.
- **Resposta (201 Created):**
  ```json
  {
    "id": 1,
    "nome_completo": "Arthur Rocha",
    "email": "arthur@exemplo.com",
    "telefone": "11987654321",
    "criado_em": "2026-10-20T22:00:00"
  }
  ```

### `POST /login`
Autentica o usuário no padrão OAuth2 Password Flow.
- **Autenticação:** Pública
- **Rate Limit:** Bloqueio temporário (HTTP 429) após 5 falhas consecutivas do mesmo IP em uma janela de 15 minutos.
- **Form Data (x-www-form-urlencoded):**
  - `username`: e-mail do usuário
  - `password`: senha em texto puro
- **Resposta (200 OK):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
  ```

### `GET /usuarios/me`
Retorna as informações do usuário autenticado no momento.
- **Autenticação:** Obrigatória (`Bearer`)
- **Resposta (200 OK):**
  ```json
  {
    "id": 1,
    "nome_completo": "Arthur Rocha",
    "email": "arthur@exemplo.com",
    "telefone": "11987654321",
    "criado_em": "2026-10-20T22:00:00"
  }
  ```

---

## 🏦 2. Módulo de Contas Bancárias (`conta_bancaria.py`)

**Prefixo Base:** `/contas-bancarias` | **Tags:** `Contas Bancárias`

### `POST /contas-bancarias/`
Cadastra uma nova conta bancária para o usuário autenticado.
- **Autenticação:** Obrigatória
- **Body:**
  ```json
  {
    "nome_banco": "Banco Nubank",
    "tipo_conta": "corrente",
    "saldo_inicial": 1500.00
  }
  ```
- **Tipos Permitidos:** `corrente`, `poupanca`, `investimento`.
- **Resposta (201 Created):** Retorna os dados da conta criada e gera automaticamente o lançamento de saldo inicial.

### `GET /contas-bancarias/`
Lista todas as contas pertencentes ao usuário autenticado com seus saldos consolidados em tempo real.
- **Autenticação:** Obrigatória
- **Query Params:** `ativa` (booleano opcional), `limit`, `offset`.

### `PUT /contas-bancarias/{conta_id}`
Atualiza dados cadastrais da conta (ex.: `nome_banco`, status `ativa`).
- **Nota:** O saldo não é alterado diretamente por este endpoint; ele reflete a soma histórica das movimentações.

### `DELETE /contas-bancarias/{conta_id}`
Remove a conta bancária indicada, caso não possua vínculos de transferências pendentes que violem a integridade.

---

## 💸 3. Módulo de Fluxo de Dinheiro (`fluxo_dinheiro.py`)

**Prefixo Base:** `/fluxo-dinheiro` | **Tags:** `Fluxo de Dinheiro`

### `POST /fluxo-dinheiro/`
Registra uma nova movimentação financeira.
- **Autenticação:** Obrigatória
- **Tipos de Movimentação:**
  - `entrada`: Receitas e proventos.
  - `saida`: Gastos e despesas.
  - `ajuste`: Correção de conciliação (valor com sinal: positivo aumenta saldo, negativo reduz).
  - `transferencia`: Movimenta fundos entre duas contas do mesmo usuário.
- **Exemplo de Lançamento Comum (Entrada/Saída):**
  ```json
  {
    "conta_bancaria_id": 1,
    "descricao": "Salário Mensal",
    "valor": 5500.00,
    "tipo": "entrada",
    "categoria": "salario",
    "data_movimentacao": "2026-10-20",
    "observacao": "Salário referente ao mês atual"
  }
  ```
- **Exemplo de Transferência entre Contas:**
  ```json
  {
    "conta_bancaria_id": 1,
    "conta_destino_id": 2,
    "descricao": "Transferência para Reserva de Emergência",
    "valor": 1000.00,
    "tipo": "transferencia",
    "categoria": "transferencia",
    "data_movimentacao": "2026-10-20"
  }
  ```
- **Categorias Fixas Permitidas:** `alimentacao`, `ajuste`, `compras`, `contas`, `educacao`, `freelance`, `impostos`, `investimento`, `lazer`, `moradia`, `outros`, `salario`, `saude`, `transporte`, `transferencia`, `vendas`.

### `GET /fluxo-dinheiro/`
Consulta o extrato financeiro com filtros opcionais.
- **Filtros (Query Params):** `conta_id`, `tipo`, `categoria`, `data_inicio`, `data_fim`, `limit`, `offset`.

### `DELETE /fluxo-dinheiro/{movimentacao_id}`
Exclui um lançamento. Se for uma transferência, a exclusão remove automaticamente ambas as pontas vinculadas em uma transação atômica.

---

## 📊 4. Módulo de Cálculos Financeiros (`calculo_financeiro.py`)

**Prefixo Base:** `/calculos-financeiros` | **Tags:** `Cálculos Financeiros`

### `POST /calculos-financeiros/`
Calcula e persiste o resumo financeiro consolidado de uma conta em um determinado intervalo.
- **Body:**
  ```json
  {
    "conta_bancaria_id": 1,
    "tipo_calculo": "mensal",
    "data_inicio": "2026-10-01",
    "data_fim": "2026-10-31"
  }
  ```
- **Tipos de Período:** `diario`, `semanal`, `mensal`, `anual`.
- **Fórmula de Saldo Final:**
  $$\text{Saldo Final} = \text{Entradas} - \text{Saídas} + \text{Transferências Recebidas} - \text{Transferências Enviadas} + \text{Ajustes}$$

---

## 🎯 5. Módulo de Metas Financeiras (`meta_financeira.py`)

**Prefixo Base:** `/metas-financeiras` | **Tags:** `Metas Financeiras`

### `POST /metas-financeiras/`
Cria uma meta financeira com data limite e valor alvo.
- **Body:**
  ```json
  {
    "nome_meta": "Viagem de Férias",
    "valor_desejado": 6000.00,
    "valor_atual": 1500.00,
    "data_limite": "2027-06-30"
  }
  ```

### `PUT /metas-financeiras/{meta_id}`
Atualiza os aportes da meta. Ao atingir ou superar o `valor_desejado`, a meta é automaticamente promovida para status `concluida`.

---

## 🩺 6. Módulo de Sistema (`api.py`)

### `GET /`
Retorna mensagem de boas-vindas e confirmação de operação da API.

### `GET /health`
Endpoint de healthcheck para monitoramento, balanceadores de carga e orquestradores:
```json
{
  "status": "healthy",
  "ambiente": "development",
  "versao": "1.0.0"
}
```
