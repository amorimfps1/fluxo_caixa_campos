# 🧪 Suíte de Testes Automatizados — Backend

Esta pasta reúne a bateria de testes automatizados do **Sistema de Fluxo de Caixa**, garantindo a conformidade das regras financeiras, a segurança dos dados e o isolamento entre usuários.

---

## 📊 Visão Geral da Suíte

- **Executor de Testes:** `pytest` com suporte a `anyio` e `Starlette TestClient`.
- **Total de Testes:** **62 testes ativos** executados na suíte padrão.
- **Taxa de Sucesso:** **100% aprovados** sem dependências externas.
- **Estratégia de Isolamento:** Os testes utilizam um banco **SQLite temporário em memória** (`sqlite:///:memory:`), criado e destruído automaticamente por fixtures do pytest em [conftest.py](conftest.py).

---

## 🗂️ Mapeamento dos Arquivos de Teste

| Arquivo de Teste | Área Coberta | Principais Cenários |
|---|---|---|
| [`test_cors.py`](test_cors.py) | Segurança de Origens HTTP | Validação de pré-voo (OPTIONS), origens locais permitidas (`app.fluxocaixa`, `5173`, `5500`), bloqueio de origens não autorizadas e validação de `APP_ENV`. |
| [`test_cadastro_usuario.py`](test_cadastro_usuario.py) | Registro de Usuários | Validação de CPF com algoritmo dos dígitos verificadores, bloqueio de caracteres Unicode maliciosos e persistência de telefone opcional. |
| [`test_dados_sensiveis.py`](test_dados_sensiveis.py) | Criptografia em Repouso | Cifragem e decifragem de CPF/telefone via Fernet, integridade do índice cego HMAC e garantia de não-exposição nas respostas JSON. |
| [`test_financeiro.py`](test_financeiro.py) | Regras Contábeis | Precisão `Decimal`, bloqueio de saldo negativo em poupança, transferências entre contas e conciliação de ajustes assinados. |
| [`test_fluxo_integracao.py`](test_fluxo_integracao.py) | Fluxo E2E Completo | Ciclo de vida ponta a ponta: cadastro, login, obtenção de JWT, criação de contas, movimentações e consulta de extrato. |
| [`test_limites_requisicoes.py`](test_limites_requisicoes.py) | Defesa contra Força Bruta | Rate limiting no login e cadastro, bloqueio HTTP 429 após 5 tentativas e expiração da janela temporal. |
| [`test_metas_relatorios.py`](test_metas_relatorios.py) | Metas e Consolidação | Agregação por períodos (diário, semanal, mensal, anual) e promoção automática de metas para o status `concluida`. |
| [`test_mysql_concorrencia.py`](test_mysql_concorrencia.py) | Concorrência Real (Opt-in) | Testes com bloqueio pessimista `SELECT ... FOR UPDATE` no MySQL para evitar condições de corrida em saques simultâneos. |

---

## ⚙️ Como Executar os Testes

### 1. Execução Padrão (Rápida e Isolada)
Na raiz do repositório:

```powershell
python -m pytest -q
```

### 2. Execução Detalhada com Nomes de Cenários
```powershell
python -m pytest -v
```

### 3. Execução de um Módulo Específico
Exemplo: testando apenas a política de CORS:

```powershell
python -m pytest backend/tests/test_cors.py -v
```

---

## 🔒 Isolamento Criptográfico e de Dados

O arquivo [conftest.py](conftest.py) substitui automaticamente as variáveis sensíveis durante a execução dos testes:
- `DATABASE_URL` aponta para `sqlite:///:memory:`.
- `JWT_SECRET_KEY` utiliza uma chave fixa e descartável de teste.
- `CPF_ENCRYPTION_KEY` utiliza uma chave Fernet efêmera de teste.

Desta forma, os testes **nunca** tocam no banco de desenvolvimento MySQL nem utilizam as chaves criptográficas reais do usuário.

---

## 🐬 Testes de Concorrência no MySQL (Opcional)

O arquivo `test_mysql_concorrencia.py` valida transferências concorrentes e saques paralelos com locking pessimista no MySQL. Estes testes são sinalizados com a marcação `@pytest.mark.mysql` e são ignorados por padrão.

Para executá-los em um schema de teste exclusivo:

```powershell
$env:TEST_MYSQL_URL = "mysql+pymysql://USUARIO:SENHA@127.0.0.1:3306/fluxo_caixa_test"
python -m pytest -m mysql -v
```
