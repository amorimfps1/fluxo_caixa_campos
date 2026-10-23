# 🧪 Suíte de Testes Automatizados — Backend

Esta pasta reúne a bateria completa de testes automatizados do **Sistema de Fluxo de Caixa**, assegurando a precisão matemática das operações financeiras, o isolamento entre usuários, a criptografia de dados sensíveis e a segurança de rede.

---

## 📊 Resumo da Cobertura

- **Runner:** `pytest`
- **Testes Padrão (Isolados em Memória):** **65 testes passando (100%)**
- **Testes de Concorrência Real (MySQL Opt-in):** **5 testes adicionais** (`@pytest.mark.mysql`)
- **Banco de Teste Padrão:** SQLite em memória (`sqlite:///:memory:`) recriado de forma limpa a cada teste via fixtures em [`conftest.py`](conftest.py).

---

## 🗂️ Mapeamento dos Arquivos de Teste

| Arquivo | Domínio Coberto | Cenários Validados |
|---|---|---|
| [`test_cors.py`](test_cors.py) | Segurança CORS & Ambiente | Preflight `OPTIONS`, origens locais e da Vercel, bloqueio de origens externas, obrigatoriedade de `APP_ENV` e proibição de `*` em produção. |
| [`test_cadastro_usuario.py`](test_cadastro_usuario.py) | Cadastro & Validações | Cálculo dos dígitos verificadores do CPF, rejeição de dígitos Unicode maliciosos, complexidade de senha e telefone opcional. |
| [`test_dados_sensiveis.py`](test_dados_sensiveis.py) | Criptografia LGPD | Cifragem/decifragem Fernet, determinismo do Blind Index HMAC (`cpf_indice`) e garantia de omissão do CPF nas respostas HTTP. |
| [`test_financeiro.py`](test_financeiro.py) | Motor Contábil | Precisão `Decimal`, proibição de saldo negativo em poupança/investimento, transferências atômicas entre contas e ajustes assinados. |
| [`test_fluxo_integracao.py`](test_fluxo_integracao.py) | Fluxo E2E Completo | Jornada completa: cadastro → login JWT → criação de contas → lançamentos → transferências → exclusão reversa. |
| [`test_limites_requisicoes.py`](test_limites_requisicoes.py) | Rate Limiting | Bloqueio `HTTP 429` após 5 tentativas inválidas de login, limite de criação de contas por IP e expiração da janela de bloqueio. |
| [`test_metas_relatorios.py`](test_metas_relatorios.py) | Metas & Balanços | Consolidação de períodos (`diario`, `semanal`, `mensal`, `anual`) e conclusão automática de metas financeiras. |
| [`test_mysql_concorrencia.py`](test_mysql_concorrencia.py) | Concorrência MySQL | Testes multi-thread com `SELECT ... FOR UPDATE` para validar ausência de *race conditions* em saques e transferências simultâneas. |

---

## 🚀 Como Executar

### 1. Suíte Padrão Completa (65 testes)
Na raiz do projeto:

```powershell
python -m pytest -q
```

### 2. Execução Detalhada (Verbose)
```powershell
python -m pytest -v
```

### 3. Executar um Arquivo Específico
```powershell
python -m pytest backend/tests/test_financeiro.py -v
```

### 4. Executar Testes de Concorrência no MySQL (Opcional)
Requer uma base MySQL de teste dedicada:
```powershell
$env:TEST_MYSQL_URL = "mysql+pymysql://USUARIO:SENHA@127.0.0.1:3306/fluxo_caixa_test"
python -m pytest -m mysql -v
```
