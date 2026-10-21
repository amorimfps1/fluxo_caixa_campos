# 🔄 Migrações de Banco de Dados — Alembic

Esta pasta contém a infraestrutura e os scripts do **Alembic**, responsável pelo versionamento estruturado e pela evolução contínua do esquema do banco de dados do **Sistema de Fluxo de Caixa**.

---

## 🎯 Por Que Usar Migrações?

O Alembic garante que o esquema do banco de dados possa ser reproduzido de maneira determinística, rastreável e auditável em qualquer ambiente (desenvolvimento, homologação, testes e produção), prevenindo divergências e alterações manuais sem histórico.

---

## 📁 Estrutura de Arquivos

```text
migrations/
├── env.py                  # Script de configuração do ambiente Alembic
├── script.py.mako          # Template utilizado na geração de novas revisões
├── versions/               # Pasta com as revisões versionadas em ordem cronológica
└── README.md               # Esta documentação
```

---

## 🚀 Comandos Mais Utilizados

Execute todos os comandos a partir da **raiz do repositório**:

### 1. Aplicar Todas as Migrações Pendentes
```powershell
python -m alembic -c "banco de dados/alembic.ini" upgrade head
```

### 2. Verificar a Versão Atual do Banco
```powershell
python -m alembic -c "banco de dados/alembic.ini" current
```

### 3. Exibir o Histórico de Migrações
```powershell
python -m alembic -c "banco de dados/alembic.ini" history --verbose
```

### 4. Criar uma Nova Revisão
```powershell
python -m alembic -c "banco de dados/alembic.ini" revision -m "nome_da_migracao"
```

---

## 🛡️ Cuidados e Diretrizes de Segurança

- **Chave de Criptografia Obrigatória:** A revisão `proteger_cpf` exige a presença da variável de ambiente `CPF_ENCRYPTION_KEY` para migrar CPFs legados para formato criptografado.
- **Prevenção de Perda de Dados:** A migração de proteção de CPF proíbe downgrade automático para evitar regravação acidental de dados pessoais em texto puro.
- **Backup Obrigatório:** Antes de rodar `upgrade head` em bancos com dados existentes, efetue sempre um backup completo da base de dados.
