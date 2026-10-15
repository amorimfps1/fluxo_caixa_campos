# 🧭 Rotas da API — Fluxo de Caixa

Os endpoints são organizados por recurso nos módulos desta pasta. Os schemas e regras financeiras ficam em `backend/esquema.py` e `backend/financeiro.py`.

## 🔐 Autenticação e propriedade dos dados

O cadastro também limita requisições por endereço cliente e responde com
HTTP 429 ao atingir o limite. O CPF deve ter 11 dígitos ASCII; a API valida
seus dígitos verificadores antes de cifrar e indexar o valor.

O cadastro e o login são públicos. O login está disponível em `POST /login`; envie o e-mail em `username` e a senha em `password`. Use o `access_token` retornado no cabeçalho `Authorization: Bearer <access_token>` das demais rotas. Após cinco falhas de login por endereço IP dentro de 15 minutos, a API bloqueia novas tentativas temporariamente e responde com HTTP 429.

Rotas financeiras consultam e alteram somente recursos pertencentes ao usuário autenticado. O servidor determina o proprietário pelo token; o cliente não deve enviar `usuario_id` para escolher o dono de uma conta ou meta. Listagens paginadas usam `limit` (padrão 50, máximo 100) e `offset` (padrão 0).

## 👤 Usuários — `usuario.py`

Prefixo: `/usuarios`

- `POST /usuarios/` — cadastra usuário com nome, CPF, e-mail e senha; aceita
  telefone opcional (201).
- `POST /login` — autentica e retorna token JWT.
- `GET /usuarios/me` — retorna os dados do usuário autenticado.
- `GET /usuarios/` — lista somente o usuário autenticado (com paginação).
- `GET /usuarios/{usuario_id}` — consulta o próprio cadastro.
- `DELETE /usuarios/{usuario_id}` — exclui o próprio cadastro.

O CPF é validado no cadastro, cifrado com Fernet usando `CPF_ENCRYPTION_KEY`
e não é incluído nas respostas. O telefone opcional também é cifrado com essa
chave e devolvido descriptografado somente nas respostas do próprio usuário.
Duplicatas de CPF são detectadas por uma impressão HMAC com chave derivada,
sem consulta pelo CPF em texto puro. Mantenha a chave em segredo e com backup
protegido.

## 🏦 Contas bancárias — `conta_bancaria.py`

Prefixo: `/contas-bancarias`

- `POST /contas-bancarias/` — cria uma conta (201).
- `GET /contas-bancarias/` e `GET /contas-bancarias/{conta_id}` — lista ou consulta as próprias contas.
- `PUT /contas-bancarias/{conta_id}` — atualiza dados editáveis, sem aceitar alteração direta do saldo.
- `DELETE /contas-bancarias/{conta_id}` — remove a conta se não houver transferências que impeçam a exclusão.

O proprietário é atribuído pela autenticação. Para corrigir o saldo, registre uma movimentação em vez de editar o saldo pelo endpoint de conta.

## 💸 Fluxo de dinheiro — `fluxo_dinheiro.py`

Prefixo: `/fluxo-dinheiro`

- `POST /fluxo-dinheiro/` — registra entrada, saída, investimento, transferência ou ajuste de saldo (201).
- `GET /fluxo-dinheiro/` e `GET /fluxo-dinheiro/{movimentacao_id}` — lista/consulta movimentações; a listagem aceita filtros por conta, categoria e período, além de paginação.
- `PUT /fluxo-dinheiro/{movimentacao_id}` — atualiza movimentação comum; transferências vinculadas não podem ser editadas como um único lançamento.
- `DELETE /fluxo-dinheiro/{movimentacao_id}` — exclui movimentação; transferências são revertidas como um par.

Exemplo de entrada:

```json
{
  "conta_bancaria_id": 1,
  "descricao": "Salário",
  "valor": 5000.00,
  "tipo": "entrada",
  "categoria": "salario",
  "data_movimentacao": "2026-10-08",
  "observacao": "Pagamento do mês"
}
```

Transferências devem informar também `conta_destino_id`, diferente da conta de origem. O destino precisa pertencer ao mesmo usuário. A API gera dois lançamentos vinculados, um de origem e outro de destino.

Contas correntes podem ficar negativas; poupanças e contas de investimento não. Categorias aceitas são fixas: `alimentacao`, `ajuste`, `compras`, `contas`, `educacao`, `freelance`, `impostos`, `investimento`, `lazer`, `moradia`, `outros`, `salario`, `saude`, `transporte`, `transferencia` e `vendas`. Acentos são removidos, e `investimentos` é normalizado para `investimento`. `transferencia` e `ajuste` só podem ser usados com os tipos correspondentes.

Para corrigir o saldo inicial, registre `tipo: "ajuste"`, `categoria: "ajuste"` e um valor assinado: positivo aumenta o saldo; negativo reduz. Ajustes não são classificados como entradas/saídas comuns.

## 📊 Cálculos financeiros — `calculo_financeiro.py`

Prefixo: `/calculos-financeiros`

- `POST /calculos-financeiros/` — calcula e persiste o resumo de uma conta/período (201).
- `GET /calculos-financeiros/` e `GET /calculos-financeiros/{calculo_id}` — consulta cálculos próprios, com paginação na listagem.
- `DELETE /calculos-financeiros/{calculo_id}` — remove um cálculo próprio.

Os tipos diário, semanal, mensal e anual precisam corresponder ao intervalo informado. Transferências recebidas/enviadas e ajustes têm totais próprios; o saldo final considera entradas − saídas + transferências recebidas − enviadas + ajustes. Investimentos são detalhamento das saídas, não uma dedução adicional.

## 🎯 Metas financeiras — `meta_financeira.py`

Prefixo: `/metas-financeiras`

- `POST /metas-financeiras/` — cria meta para o usuário autenticado (201).
- `GET /metas-financeiras/` — lista metas próprias, com filtro de status e paginação.
- `GET /metas-financeiras/{meta_id}` — consulta uma meta própria.
- `PUT /metas-financeiras/{meta_id}` — atualiza meta própria.
- `DELETE /metas-financeiras/{meta_id}` — remove meta própria.

Quando o valor atual alcança o valor desejado, o status é atualizado para `concluida`.

## 🧪 Documentação interativa

Com a API em execução, consulte `/docs` para ver os schemas e parâmetros exatos disponibilizados pelo OpenAPI.
