# 🔐 Segurança — Fluxo de Caixa

Este módulo é responsável por proteger as credenciais dos usuários do sistema.

A principal função da pasta `seguranca` é garantir que as senhas não sejam armazenadas em texto puro no banco de dados, usando técnicas de hashing seguras.

---

## 📁 Estrutura do módulo

```text
seguranca/
├── __init__.py
├── seguranca.py
└── readme.md
```

---

## 🎯 Objetivo

O módulo atua em duas etapas principais:

- gerar um hash seguro a partir da senha informada pelo usuário;
- verificar se a senha inserida corresponde ao hash já armazenado no banco.

A autenticação de requisições e a emissão de tokens são implementadas separadamente em `backend/autenticacao.py`.

---

## 🧩 Arquivo principal

### `seguranca.py`

Este arquivo contém as funções:

- `gerar_hash_senha(senha: str) -> str`
- `verificar_senha(senha: str, senha_hash: str) -> bool`

A biblioteca utilizada é `pwdlib`, com o uso de `PasswordHash.recommended()` para manter um padrão seguro e atualizado de armazenamento de credenciais.

```python
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()
```

---

## 🔑 Funções disponíveis

### `gerar_hash_senha(senha: str) -> str`

Cria um hash seguro a partir da senha original do usuário.

```python
from seguranca.seguranca import gerar_hash_senha

senha_hash = gerar_hash_senha("Senha@123")
```

Esse valor é salvo no campo `senha_hash` da tabela `usuarios`.

### `verificar_senha(senha: str, senha_hash: str) -> bool`

Compara a senha informada com o hash armazenado.

```python
from seguranca.seguranca import verificar_senha

resultado = verificar_senha("Senha@123", senha_hash)
```

O retorno é:

- `True` → senha correta;
- `False` → senha incorreta.

---

## 🔄 Fluxo de uso

### Cadastro e login

```text
Usuário informa a senha
       │
       ▼
  gerar_hash_senha()
       │
       ▼
  Hash seguro
       │
       ▼
   Armazenado no banco
```

O endpoint `POST /login` recebe credenciais no formato OAuth2 Password: `username` deve conter o e-mail e `password`, a senha. Quando válidas, a API retorna `access_token` e `token_type: bearer`. Após cinco falhas de login do mesmo endereço IP em 15 minutos, novas tentativas são temporariamente bloqueadas.

```text
Usuário informa a senha
       │
       ▼
  verificar_senha()
       │
       ▼
  Compara com hash salvo
       │
       ▼
   Token JWT de acesso
```

As rotas de usuários, contas, movimentações, cálculos e metas exigem o token no cabeçalho `Authorization: Bearer <access_token>`. Cadastro e login são públicos. A identidade do proprietário é obtida do token, não de um `usuario_id` enviado pelo cliente.

---

## 🗃️ Relação com o banco

A tabela `usuarios` contém o campo:

```text
senha_hash
```

Esse campo guarda apenas o hash, nunca a senha em texto puro.

---

## ✅ Boas práticas aplicadas

- a senha original não é persistida;
- o hashing é usado antes do cadastro;
- a validação do login usa o hash salvo no banco;
- o módulo é importado corretamente pela aplicação;
- a segurança fica separada da regra de negócio da API;
- o segredo JWT vem da variável de ambiente `JWT_SECRET_KEY`, deve ter pelo menos 32 caracteres e não deve ser versionado;
- as respostas da API omitem CPF; o CPF é cifrado com Fernet antes do
  armazenamento e um índice HMAC separado é usado para detectar duplicatas;
- mantenha `CPF_ENCRYPTION_KEY` em segredo e com backup seguro: sem a chave
  correta, os CPFs e telefones cifrados não podem ser recuperados.

Exemplo de importação:

```python
from seguranca.seguranca import gerar_hash_senha, verificar_senha
```

---

## 🛡️ Importância da camada

A pasta `seguranca` é essencial para manter o sistema em conformidade com boas práticas de proteção de dados e minimização de riscos relacionados a vazamento de credenciais.

Os dados sensíveis de CPF e telefone são tratados separadamente deste módulo:
o backend valida o CPF com 11 dígitos ASCII, cifra CPF e telefone com Fernet e
usa um índice HMAC derivado para detectar CPFs duplicados. A chave
`CPF_ENCRYPTION_KEY` é diferente de `JWT_SECRET_KEY`; mantenha ambas fora do
repositório e preserve backup seguro da chave de cifragem.

A lógica principal é:

```text
senha original → hash → armazenamento seguro
```