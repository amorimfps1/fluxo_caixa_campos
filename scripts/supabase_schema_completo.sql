-- ====================================================================
-- SISTEMA FLUXO DE CAIXA - SCHEMA COMPLETO PARA SUPABASE (POSTGRESQL)
-- ====================================================================
-- Execute este script completo no SQL Editor do painel do Supabase.
-- Ele cria todos os tipos ENUM, tabelas, chaves primárias, chaves estrangeiras
-- com ON DELETE CASCADE, índices e as 16 categorias base do sistema.
-- ====================================================================

-- 1. Criação idempotente de Tipos ENUM
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_conta_enum') THEN
        CREATE TYPE tipo_conta_enum AS ENUM ('corrente', 'poupanca', 'investimento');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_movimentacao_enum') THEN
        CREATE TYPE tipo_movimentacao_enum AS ENUM ('entrada', 'saida', 'transferencia', 'ajuste', 'investimento');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'direcao_transferencia_enum') THEN
        CREATE TYPE direcao_transferencia_enum AS ENUM ('origem', 'destino');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'natureza_conta_enum') THEN
        CREATE TYPE natureza_conta_enum AS ENUM ('fixa', 'variavel');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tipo_calculo_enum') THEN
        CREATE TYPE tipo_calculo_enum AS ENUM ('diario', 'semanal', 'mensal', 'anual');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'status_meta_enum') THEN
        CREATE TYPE status_meta_enum AS ENUM ('em_andamento', 'concluida', 'cancelada');
    END IF;
END $$;

-- 2. Tabela de Usuários
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    nome_completo VARCHAR(150) NOT NULL,
    cpf VARCHAR(255) NOT NULL UNIQUE,
    cpf_indice VARCHAR(64) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefone VARCHAR(255),
    email_verificado BOOLEAN NOT NULL DEFAULT FALSE,
    codigo_verificacao_hash VARCHAR(64),
    codigo_expira_em TIMESTAMP WITHOUT TIME ZONE,
    senha_hash VARCHAR(255) NOT NULL,
    codigo_otp VARCHAR(64),
    otp_expiracao TIMESTAMP WITHOUT TIME ZONE,
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Tabela de Tentativas de Login (Rate Limit)
CREATE TABLE IF NOT EXISTS tentativas_login (
    chave_cliente VARCHAR(64) PRIMARY KEY,
    tentativas INTEGER NOT NULL DEFAULT 0,
    inicio_janela TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    bloqueado_ate TIMESTAMP WITHOUT TIME ZONE
);
CREATE INDEX IF NOT EXISTS idx_tentativas_login_janela ON tentativas_login (inicio_janela);

-- 4. Tabela de Categorias Fixas
CREATE TABLE IF NOT EXISTS categorias_movimentacao (
    nome VARCHAR(100) PRIMARY KEY
);

-- 5. Tabela de Contas Bancárias
CREATE TABLE IF NOT EXISTS contas_bancarias (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    nome_banco VARCHAR(100) NOT NULL,
    tipo_conta tipo_conta_enum NOT NULL,
    valor_conta_atual NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    ativa BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_conta_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_contas_usuario ON contas_bancarias (usuario_id);

-- 6. Tabela de Fluxo de Dinheiro (Movimentações)
CREATE TABLE IF NOT EXISTS fluxo_dinheiro (
    id SERIAL PRIMARY KEY,
    conta_bancaria_id INTEGER NOT NULL,
    conta_destino_id INTEGER,
    descricao VARCHAR(200) NOT NULL,
    valor NUMERIC(12, 2) NOT NULL,
    tipo tipo_movimentacao_enum NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    data_movimentacao DATE NOT NULL,
    observacao VARCHAR(255),
    transferencia_id VARCHAR(36),
    transferencia_direcao direcao_transferencia_enum,
    natureza_conta natureza_conta_enum,
    dia_repeticao INTEGER,
    tipo_investimento VARCHAR(60),
    CONSTRAINT fk_fluxo_conta FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias (id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_fluxo_conta_destino FOREIGN KEY (conta_destino_id) REFERENCES contas_bancarias (id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fluxo_categoria FOREIGN KEY (categoria) REFERENCES categorias_movimentacao (nome) ON DELETE RESTRICT ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fluxo_conta ON fluxo_dinheiro (conta_bancaria_id);
CREATE INDEX IF NOT EXISTS idx_fluxo_data ON fluxo_dinheiro (data_movimentacao);
CREATE INDEX IF NOT EXISTS idx_fluxo_tipo ON fluxo_dinheiro (tipo);
CREATE INDEX IF NOT EXISTS ix_fluxo_dinheiro_transferencia_id ON fluxo_dinheiro (transferencia_id);

-- 7. Tabela de Cálculos Financeiros (Resumos)
CREATE TABLE IF NOT EXISTS calculos_financeiros (
    id SERIAL PRIMARY KEY,
    conta_bancaria_id INTEGER NOT NULL,
    tipo_calculo tipo_calculo_enum NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    valor_original NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_entradas NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_saidas NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_investimentos NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_transferencias_recebidas NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_transferencias_enviadas NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_ajustes NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    valor_final NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_calculo_conta FOREIGN KEY (conta_bancaria_id) REFERENCES contas_bancarias (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_calculo_conta ON calculos_financeiros (conta_bancaria_id);

-- 8. Tabela de Metas Financeiras
CREATE TABLE IF NOT EXISTS metas_financeiras (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    nome VARCHAR(150) NOT NULL,
    valor_meta NUMERIC(12, 2) NOT NULL,
    valor_atual NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    data_inicio DATE NOT NULL,
    data_limite DATE,
    status status_meta_enum NOT NULL DEFAULT 'em_andamento',
    descricao VARCHAR(255),
    criado_em TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_meta_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_metas_usuario ON metas_financeiras (usuario_id);

-- 9. Tabela de Orçamentos
CREATE TABLE IF NOT EXISTS orcamentos (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    mes DATE NOT NULL,
    limite NUMERIC(12, 2) NOT NULL,
    CONSTRAINT uq_orcamento_usuario_categoria_mes UNIQUE (usuario_id, categoria, mes),
    CONSTRAINT fk_orcamento_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE,
    CONSTRAINT fk_orcamento_categoria FOREIGN KEY (categoria) REFERENCES categorias_movimentacao (nome) ON DELETE RESTRICT ON UPDATE CASCADE
);

-- 10. Tabela de Preferências de Alerta
CREATE TABLE IF NOT EXISTS preferencias_alerta (
    usuario_id INTEGER PRIMARY KEY,
    orcamento BOOLEAN NOT NULL DEFAULT TRUE,
    vencimento BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_pref_alerta_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 11. Tabela de Alertas Lidos
CREATE TABLE IF NOT EXISTS alertas_lidos (
    usuario_id INTEGER NOT NULL,
    chave VARCHAR(100) NOT NULL,
    PRIMARY KEY (usuario_id, chave),
    CONSTRAINT fk_alerta_lido_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

-- 12. Tabela de Controle de Versão do Alembic (compatibilidade total com futuras migrações)
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);
DELETE FROM alembic_version;
INSERT INTO alembic_version (version_num) VALUES ('f24e2179202c');

-- 13. População Inicial das 16 Categorias Fixas
INSERT INTO categorias_movimentacao (nome) VALUES
    ('alimentacao'),
    ('ajuste'),
    ('compras'),
    ('contas'),
    ('educacao'),
    ('freelance'),
    ('impostos'),
    ('investimento'),
    ('lazer'),
    ('moradia'),
    ('outros'),
    ('salario'),
    ('saude'),
    ('transporte'),
    ('transferencia'),
    ('vendas')
ON CONFLICT (nome) DO NOTHING;
