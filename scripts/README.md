# 🛠️ Scripts Utilitários — Fluxo de Caixa

Esta pasta reúne scripts administrativos para manutenção segura, migrações de dados e limpeza controlada em ambientes de desenvolvimento, homologação e nuvem.

---

## 📄 Scripts Disponíveis

### 1. [`migrar_para_supabase.py`](migrar_para_supabase.py)
Script automatizado de migração de dados e esquemas de bancos de dados legados (MySQL / SQLite / TiDB) diretamente para o **Supabase PostgreSQL**.
- Lê as credenciais e conexões do arquivo `.env`.
- Cria sequencialmente as 11 tabelas no schema do PostgreSQL com chaves estrangeiras, índices e restrições.
- Popula as 16 categorias oficiais de movimentação.
- Valida a integridade dos dados inseridos através de contagem comparativa.

#### Como Executar:
```powershell
python scripts/migrar_para_supabase.py
```

---

### 2. [`supabase_schema_completo.sql`](supabase_schema_completo.sql)
Script DDL em SQL puro compatível com o **SQL Editor do Supabase**. Contém as definições estruturadas de todas as tabelas, tipos de dados, chaves primárias, relacionamentos com integridade referencial (`ON DELETE CASCADE` / `ON DELETE RESTRICT`) e índices de busca rápida (`cpf_indice`, `usuario_id`, etc.).

---

### 3. [`remover_usuario_teste.py`](remover_usuario_teste.py)
Remove um usuário de teste específico (identificado pelo endereço de e-mail) e todos os registros vinculados a ele em uma única transação atômica.

#### Ordem de Exclusão Segura:
1. Alertas lidos (`alertas_lidos`) e preferências (`preferencias_alerta`)
2. Orçamentos mensais (`orcamentos`)
3. Metas financeiras (`metas_financeiras`)
4. Cálculos financeiros consolidados (`calculos_financeiros`)
5. Movimentações financeiras (`fluxo_dinheiro`)
6. Contas bancárias (`contas_bancarias`)
7. Tentativas de login registradas (`tentativas_login`)
8. Registro do usuário (`usuarios`)

#### Travas de Segurança Interativas:
- Exibe previamente o banco de dados alvo (com a senha ocultada da `DATABASE_URL`) e a contagem exata de registros afetados.
- Solicita confirmação explícita digitando o **nome do banco** e a palavra **`CONFIRMO`** antes de executar qualquer `DELETE`.

#### Como Executar:
```powershell
python scripts/remover_usuario_teste.py usuario_teste@exemplo.com
```
