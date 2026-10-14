# Frontend

Frontend estático em HTML, CSS e JavaScript nativo:

- `login.html`: autenticação via `POST /login`;
- `cadastro.html`: cadastro com nome, CPF obrigatório, e-mail, senha e
  telefone opcional;
- `index.html`: dashboard protegido, com contas e movimentações;
- `css/style.css`: estilos compartilhados;
- `js/api.js`: cliente HTTP e armazenamento do JWT em `sessionStorage`;
- `js/login.js` e `js/dashboard.js`: fluxos de tela.
- `js/cadastro.js`: validação de confirmação de senha e envio do cadastro.

## Execução local

Inicie a API em um terminal, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe main.py
```

Em outro terminal, sirva a pasta do frontend na porta `5173`:

```powershell
Set-Location frontend
..\.venv\Scripts\python.exe -m http.server 5173 --bind 127.0.0.1
```

Abra `http://127.0.0.1:5173/login.html`. A API permite essa origem local e
`http://app.fluxocaixa`, inclusive o servidor na porta padrão 80, e
`http://app.fluxocaixa:5173`. Para usar os endereços com o nome
`app.fluxocaixa`, configure esse nome para `127.0.0.1` no arquivo `hosts` do
Windows (requer permissão de administrador). O cliente usa `127.0.0.1:8000`
para acessar a API local, sem exigir um alias DNS adicional.

## Autenticação e limites de segurança

O login envia `username` (e-mail) e `password` como formulário OAuth2. A
resposta contém `access_token`, guardado em `sessionStorage` e enviado como
`Authorization: Bearer` nas chamadas protegidas. Se o token expirar, a API
retorna 401 e a interface solicita novo login.

O cadastro aceita Gmail como endereço comum de e-mail, com senha local; isso
não é autenticação Google OAuth. O CPF permanece obrigatório pela API. O
telefone é opcional, cifrado no banco com a chave de dados sensíveis e
descriptografado apenas na resposta ao próprio usuário.

O servidor de desenvolvimento e a API usam HTTP sem TLS. Use-os apenas em
`localhost` com usuários e dados fictícios; não publique essas portas na rede
nem use este frontend como serviço de produção.
