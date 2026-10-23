# 🛠️ Scripts Utilitários — Fluxo de Caixa

Esta pasta reúne scripts administrativos para manutenção segura e limpeza controlada de dados em ambientes de desenvolvimento e homologação.

---

## 📄 Scripts Disponíveis

### [`remover_usuario_teste.py`](remover_usuario_teste.py)
Remove um usuário de teste específico (identificado pelo seu endereço de e-mail) e todos os registros vinculados a ele em uma única transação atômica.

#### Ordem de Exclusão Segura:
1. Metas financeiras do usuário (`metas_financeiras`)
2. Cálculos financeiros consolidados das contas do usuário (`calculos_financeiros`)
3. Movimentações financeiras das contas do usuário (`fluxo_dinheiro`)
4. Contas bancárias do usuário (`contas_bancarias`)
5. Registro do usuário (`usuarios`)

#### Travas de Segurança Interativas:
- Exibe previamente o banco de dados alvo (ocultando a senha da `DATABASE_URL`) e a contagem exata de registros que serão removidos em cada tabela.
- Solicita que o operador digite manualmente o **nome do banco de dados** e a palavra **`CONFIRMO`** antes de executar qualquer `DELETE`.

#### Como Executar:
Na raiz do repositório, com o ambiente virtual ativado:

```powershell
python scripts/remover_usuario_teste.py usuario_teste@exemplo.com
```
