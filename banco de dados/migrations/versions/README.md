# 📜 Histórico de Revisões do Esquema — Alembic

Este documento registra a linha do tempo e a árvore de dependências das 8 revisões que compõem o esquema relacional do **Sistema de Fluxo de Caixa**.

---

## 🌳 Árvore Linear de Revisões

```mermaid
flowchart TD
    R1["1. esquema_inicial<br/>(Tabelas base: usuarios, contas, fluxo, calculos, metas)"] --> R2["2. transferencias<br/>(Vínculo atômico entre contas: transferencia_id e direção)"]
    R2 --> R3["3. categorias_movimentacao<br/>(Tabela de domínio de categorias fixas e FK)"]
    R3 --> R4["4. ajustes_e_resumos<br/>(Suporte a conciliação contábil assinada)"]
    R4 --> R5["5. limite_login<br/>(Tabela tentativas_login para Rate Limiting)"]
    R5 --> R6["6. normalizar_schema<br/>(Padronização DECIMAL(12,2), FKs e índices MySQL)"]
    R6 --> R7["7. proteger_cpf<br/>(Cifragem Fernet em repouso + Blind Index cpf_indice)"]
    R7 --> R8["8. adicionar_telefone_usuario<br/>(Coluna telefone opcional cifrada com Fernet)"]
```

---

## 📋 Detalhamento Técnico das Revisões

| # | Revisão (`revision`) | Revisão Anterior (`down_revision`) | Descrição e Impacto no Banco |
|---|---|---|---|
| **1** | `esquema_inicial` | `None` | Criação das tabelas principais (`usuarios`, `contas_bancarias`, `fluxo_dinheiro`, `calculos_financeiros`, `metas_financeiras`). |
| **2** | `transferencias` | `esquema_inicial` | Inclusão de `transferencia_id`, `transferencia_direcao` e `conta_destino_id` em `fluxo_dinheiro` para rastreio de transferências entre contas. |
| **3** | `categorias_movimentacao` | `transferencias` | Criação da tabela `categorias_movimentacao` populada com as 16 categorias oficiais e normalização dos registros existentes. |
| **4** | `ajustes_e_resumos` | `categorias_movimentacao` | Inclusão do tipo `ajuste` no enum de movimentações e suporte a valores negativos de conciliação. |
| **5** | `limite_login` | `ajustes_e_resumos` | Criação da tabela `tentativas_login` para controle de força bruta por IP e conta. |
| **6** | `normalizar_schema` | `limite_login` | Alinhamento de tipos `DECIMAL(12,2)`, chaves estrangeiras com `ON DELETE CASCADE` e índices compostos de performance. |
| **7** | `proteger_cpf` | `normalizar_schema` | Migração de segurança LGPD: cifra CPFs com Fernet e adiciona a coluna `cpf_indice` (`UNIQUE`) com HMAC-SHA256. |
| **8** | `adicionar_telefone_usuario` | `proteger_cpf` (`head`) | Adiciona a coluna opcional `telefone` (`VARCHAR(255)`) na tabela `usuarios`, armazenada cifrada com Fernet. |
